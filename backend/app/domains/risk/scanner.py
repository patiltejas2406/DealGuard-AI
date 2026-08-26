"""Automated 17-Pillar Document Risk Detection and Evidence Provenance Scanner."""

import hashlib
import re
import uuid
from typing import Any, Dict, List, Optional, Set, Tuple
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.domains.ai.guardrails import AIGuardrailValidator
from app.domains.ai.schemas import CitationRef, GroundedFinding
from app.domains.documents.models import Citation, Document, DocumentChunk
from app.domains.risk.models import Risk, RiskEvidence
from app.domains.risk.scoring import calculate_risk_evaluation
from app.domains.risk.taxonomy import (
    CATEGORY_METADATA,
    CategoryInfo,
    DetectionSource,
    RiskCategory,
    RiskStatus,
)


def compute_risk_fingerprint(deal_id: uuid.UUID, category: str, title: str, quote: str) -> str:
    """Generate deterministic SHA256 fingerprint for deduplication."""
    norm_title = title.lower().strip()
    norm_quote = quote.lower().strip()[:80]
    payload = f"{deal_id}:{category.upper()}:{norm_title}:{norm_quote}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class DocumentRiskScanner:
    """
    Scans indexed document chunks for risk signals across all 17 Diligence Pillars.
    Enforces deterministic scoring, AI guardrails, and citation binding.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def scan_deal_documents(
        self,
        organization_id: uuid.UUID,
        deal_id: uuid.UUID,
        categories: Optional[List[RiskCategory]] = None,
        min_confidence: float = 0.60,
    ) -> Tuple[List[Risk], int, int, int]:
        """
        Scan deal document chunks for grounded risks across selected or all 17 categories.
        Returns (created_risks, scanned_chunks_count, detected_count, duplicates_skipped).
        """
        target_categories = categories or list(RiskCategory)

        # 1. Fetch document chunks for the deal
        stmt = (
            select(DocumentChunk, Document.name)
            .join(Document, DocumentChunk.document_id == Document.id)
            .where(
                DocumentChunk.organization_id == organization_id,
                DocumentChunk.deal_id == deal_id,
            )
            .order_by(DocumentChunk.document_id, DocumentChunk.chunk_index)
        )
        result = await self.session.execute(stmt)
        chunk_rows = result.all()
        scanned_chunks_count = len(chunk_rows)

        if scanned_chunks_count == 0:
            return [], 0, 0, 0

        # 2. Fetch existing fingerprints for deduplication
        existing_stmt = select(Risk.fingerprint).where(
            Risk.organization_id == organization_id,
            Risk.deal_id == deal_id,
            Risk.fingerprint.isnot(None),
        )
        existing_res = await self.session.execute(existing_stmt)
        existing_fingerprints: Set[str] = {fp for fp in existing_res.scalars().all() if fp}

        detected_risks: List[Dict[str, Any]] = []

        # 3. Detect candidate risks from chunk content
        for chunk, doc_name in chunk_rows:
            text = chunk.content
            if not text or len(text.strip()) < 20:
                continue

            for cat in target_categories:
                meta = CATEGORY_METADATA.get(cat)
                if not meta:
                    continue

                candidate = self._detect_category_signal(
                    cat=cat,
                    meta=meta,
                    chunk=chunk,
                    doc_name=doc_name,
                    text=text,
                    min_confidence=min_confidence,
                )
                if candidate:
                    detected_risks.append(candidate)

        detected_count = len(detected_risks)
        created_risks: List[Risk] = []
        duplicates_skipped = 0

        # 4. Process and persist grounded risks with guardrail checks
        for item in detected_risks:
            fp = compute_risk_fingerprint(
                deal_id=deal_id,
                category=item["category"],
                title=item["title"],
                quote=item["exact_quote"],
            )

            if fp in existing_fingerprints:
                duplicates_skipped += 1
                continue

            # Build and validate GroundedFinding via Guardrails
            cit_ref = CitationRef(
                document_id=item["document_id"],
                chunk_id=item["chunk_id"],
                document_name=item["doc_name"],
                page_number=item["page_number"],
                section_title=item["section_title"],
                exact_quote=item["exact_quote"],
                confidence_score=item["confidence_score"],
            )

            finding = GroundedFinding(
                domain_pillar="RISK",
                category=item["category"],
                headline=item["title"],
                detailed_reasoning=item["description"],
                confidence_score=item["confidence_score"],
                is_deterministic_calculation=False,
                citations=[cit_ref],
            )

            is_valid, violations = AIGuardrailValidator.validate_finding_grounding(finding)
            if not is_valid:
                continue

            # Deterministic scoring
            score, risk_level = calculate_risk_evaluation(item["severity"], item["likelihood"])

            # Create Risk ORM record
            risk = Risk(
                organization_id=organization_id,
                deal_id=deal_id,
                category=item["category"],
                title=item["title"],
                description=item["description"],
                severity=item["severity"],
                likelihood=item["likelihood"],
                score=score,
                risk_level=risk_level.value,
                status=RiskStatus.IDENTIFIED.value,
                detection_source=DetectionSource.AI_EXTRACTED.value,
                confidence_score=item["confidence_score"],
                mitigation_strategy=item["default_mitigation"],
                recommendation=item["recommendation"],
                fingerprint=fp,
            )
            self.session.add(risk)
            await self.session.flush()

            # Create Citation & Evidence link
            citation = Citation(
                organization_id=organization_id,
                deal_id=deal_id,
                document_id=item["document_id"],
                chunk_id=item["chunk_id"],
                page_number=item["page_number"],
                section=item["section_title"],
                exact_quote=item["exact_quote"],
                extraction_method="AI_DETECTION_SCAN",
                source_entity_type="DOCUMENT",
                confidence_score=item["confidence_score"],
            )
            self.session.add(citation)
            await self.session.flush()

            evidence = RiskEvidence(
                organization_id=organization_id,
                deal_id=deal_id,
                risk_id=risk.id,
                citation_id=citation.id,
                relevance_explanation=f"Signal extracted from {item['doc_name']} (Page {item['page_number']})",
                weight=1.0,
            )
            self.session.add(evidence)
            await self.session.flush()

            existing_fingerprints.add(fp)
            created_risks.append(risk)

        return created_risks, scanned_chunks_count, detected_count, duplicates_skipped

    def _detect_category_signal(
        self,
        cat: RiskCategory,
        meta: CategoryInfo,
        chunk: DocumentChunk,
        doc_name: str,
        text: str,
        min_confidence: float,
    ) -> Optional[Dict[str, Any]]:
        """Evaluate text against domain signal patterns and extract sentence quotation."""
        text_lower = text.lower()
        matched_signals = [sig for sig in meta.signals if sig in text_lower]

        if not matched_signals:
            return None

        # Extract context sentence containing the primary matched signal
        primary_sig = matched_signals[0]
        sentences = re.split(r"(?<=[.!?])\s+", text)
        matched_sentence = ""
        for s in sentences:
            if primary_sig in s.lower():
                matched_sentence = s.strip()
                break

        if not matched_sentence or len(matched_sentence) < 10:
            matched_sentence = text[:200].strip()

        # Quantitative estimation based on matched signals density
        signal_count = len(matched_signals)
        confidence = min(0.98, 0.65 + (signal_count * 0.08))

        if confidence < min_confidence:
            return None

        # Severity & Likelihood heuristics calibrated to category guidelines
        severity, likelihood = self._estimate_severity_likelihood(cat, text_lower)

        title = f"{meta.name}: {primary_sig.title()} Signal Detected"
        description = (
            f"Automated scan identified potential {meta.name.lower()} exposure in document '{doc_name}' "
            f"(Page {chunk.page_number}). Matched signal indicators: {', '.join(matched_signals[:3])}."
        )
        recommendation = (
            f"Conduct targeted confirmatory diligence on {meta.name.lower()}. {meta.default_mitigation}"
        )

        return {
            "category": cat.value,
            "title": title,
            "description": description,
            "severity": severity,
            "likelihood": likelihood,
            "confidence_score": confidence,
            "exact_quote": matched_sentence,
            "document_id": chunk.document_id,
            "chunk_id": chunk.id,
            "doc_name": doc_name,
            "page_number": chunk.page_number,
            "section_title": chunk.section_title or "General Section",
            "default_mitigation": meta.default_mitigation,
            "recommendation": recommendation,
        }

    def _estimate_severity_likelihood(self, cat: RiskCategory, text_lower: str) -> Tuple[int, int]:
        """Heuristic quantitative severity and likelihood estimation."""
        high_severity_words = ["breach", "critical", "lawsuit", "sanction", "default", "catastrophic", "violation", "loss", "restatement"]
        high_likelihood_words = ["ongoing", "repeated", "pending", "frequent", "active", "imminent", "historical"]

        severity = 3
        likelihood = 3

        if any(w in text_lower for w in high_severity_words):
            severity = min(5, severity + 1)
        if any(w in text_lower for w in high_likelihood_words):
            likelihood = min(5, likelihood + 1)

        # Category-specific base adjustments
        if cat in [RiskCategory.DEBT_COVENANTS, RiskCategory.RESTATEMENT, RiskCategory.LEGAL_LITIGATION]:
            severity = max(4, severity)
        elif cat in [RiskCategory.CUSTOMER_CONCENTRATION, RiskCategory.KEY_PERSON, RiskCategory.CYBERSECURITY]:
            severity = max(3, severity)

        return severity, likelihood
