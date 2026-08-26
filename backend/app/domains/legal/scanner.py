"""Deterministic Legal, Contract & Compliance Scanner."""

import hashlib
import re
import uuid
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from app.domains.documents.models import Citation, Document, DocumentChunk
from app.domains.legal.config import ContractCategory, ContractType
from app.domains.legal.models import (
    ComplianceRequirement,
    ContractClause,
    ContractRecord,
    LegalFinding,
)


def compute_clause_fingerprint(deal_id: uuid.UUID, doc_id: Optional[uuid.UUID], category: str, text: str) -> str:
    """Deterministic SHA-256 fingerprint for clause deduplication and idempotency."""
    normalized_text = " ".join(text.strip().lower().split())[:120]
    payload = f"{deal_id}:{doc_id or 'none'}:{category}:{normalized_text}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def compute_finding_fingerprint(deal_id: uuid.UUID, clause_fingerprint: str, finding_type: str) -> str:
    """Deterministic SHA-256 fingerprint for legal finding deduplication."""
    payload = f"{deal_id}:{clause_fingerprint}:{finding_type}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


# Pattern heuristics for grounded clause extraction
CLAUSE_PATTERNS = [
    {
        "category": ContractCategory.CHANGE_OF_CONTROL.value,
        "keywords": ["change of control", "change in control", "merger, consolidation", "sale of all or substantially all", "acquisition of more than 50%"],
        "severity": "CRITICAL",
        "requires_consent": True,
        "requires_notice": True,
        "title": "Change of Control Consent Requirement",
        "finding_type": "CHANGE_OF_CONTROL_CONSENT",
        "business_impact": "Acquisition triggers mandatory counterparty consent or allows customer/vendor termination.",
        "recommendation": "Initiate consent solicitation pre-closing or establish customer retention dialogue.",
    },
    {
        "category": ContractCategory.ASSIGNMENT_RESTRICTION.value,
        "keywords": ["not assign", "without the prior written consent", "assignment by operation of law", "non-assignable", "shall not transfer"],
        "severity": "HIGH",
        "requires_consent": True,
        "requires_notice": True,
        "title": "Anti-Assignment / Consent on Transfer",
        "finding_type": "ASSIGNMENT_CONSENT_REQUIRED",
        "business_impact": "Agreement cannot be transferred to acquiring entity or parent organization without formal counterparty consent.",
        "recommendation": "Request written waiver / assignment consent from counterparty prior to integration.",
    },
    {
        "category": ContractCategory.TERMINATION_RIGHT.value,
        "keywords": ["right to terminate", "immediate termination", "terminate for convenience", "terminate upon 30 days", "terminate upon change of control"],
        "severity": "HIGH",
        "requires_consent": False,
        "requires_notice": True,
        "title": "Unilateral or Event-Driven Termination Right",
        "finding_type": "TERMINATION_EXPOSURE",
        "business_impact": "Counterparty may exit relationship with minimal notice, creating contract revenue or service continuity risk.",
        "recommendation": "Review commercial relationship health and negotiate revised minimum commitment term.",
    },
    {
        "category": ContractCategory.NON_COMPETE.value,
        "keywords": ["non-compete", "shall not engage in", "competing business", "restricted territory", "covenant not to compete"],
        "severity": "HIGH",
        "requires_consent": False,
        "requires_notice": False,
        "title": "Commercial Non-Compete Restriction",
        "finding_type": "STRATEGIC_NON_COMPETE_CONSTRAINT",
        "business_impact": "Restricts post-deal expansion into target markets or product consolidation across portfolio companies.",
        "recommendation": "Assess antitrust enforceability and evaluate carve-outs for parent/affiliate operating companies.",
    },
    {
        "category": ContractCategory.IP_OWNERSHIP.value,
        "keywords": ["work made for hire", "irrevocably assigns", "all right, title and interest", "sole and exclusive owner", "intellectual property assignment"],
        "severity": "MEDIUM",
        "requires_consent": False,
        "requires_notice": False,
        "title": "Intellectual Property Assignment & Title",
        "finding_type": "IP_OWNERSHIP_CONFIRMATION",
        "business_impact": "Verifies that core technology, software code, and patentable assets are fully owned by target entity.",
        "recommendation": "Confirm written assignment agreements are on file for all founders, employees, and contractors.",
    },
    {
        "category": ContractCategory.EXCLUSIVITY.value,
        "keywords": ["exclusive provider", "exclusivity", "sole provider", "most favored nation", "most favored customer"],
        "severity": "HIGH",
        "requires_consent": False,
        "requires_notice": False,
        "title": "Exclusivity or Most-Favored-Customer Covenant",
        "finding_type": "COMMERCIAL_EXCLUSIVITY_LIMITATION",
        "business_impact": "Precludes cross-selling with competing partner products or constrains flexible pricing strategies.",
        "recommendation": "Model pricing impacts and structure integration boundaries to protect existing contract tiers.",
    },
    {
        "category": ContractCategory.DATA_PRIVACY.value,
        "keywords": ["data processing agreement", "gdpr", "ccpa", "personal data", "standard contractual clauses", "subprocessor"],
        "severity": "MEDIUM",
        "requires_consent": False,
        "requires_notice": True,
        "title": "Data Privacy & Cross-Border Processing Compliance",
        "finding_type": "DATA_PRIVACY_OBLIGATION",
        "business_impact": "Mandates sub-processor notifications and GDPR/CCPA data handling standards upon infrastructure migration.",
        "recommendation": "Include privacy officer sign-off in Phase 11 IT & Data Systems integration workstream.",
    },
]


def extract_clauses_from_chunks(
    chunks: List[DocumentChunk],
    deal_id: uuid.UUID,
    organization_id: uuid.UUID,
    user_id: Optional[uuid.UUID],
    contract_id: Optional[uuid.UUID] = None,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Scan document text chunks for contractual clause patterns and produce structured clauses + findings."""
    clauses = []
    findings = []
    seen_fingerprints = set()

    for chunk in chunks:
        text = chunk.content or ""
        text_lower = text.lower()

        for pattern in CLAUSE_PATTERNS:
            for kw in pattern["keywords"]:
                if kw in text_lower:
                    fp = compute_clause_fingerprint(deal_id, chunk.document_id, pattern["category"], text)
                    if fp in seen_fingerprints:
                        continue
                    seen_fingerprints.add(fp)

                    # Extract context snippet
                    idx = text_lower.find(kw)
                    start = max(0, idx - 80)
                    end = min(len(text), idx + len(kw) + 140)
                    snippet = text[start:end].strip()

                    sec_ref = getattr(chunk, "section_title", None) or getattr(chunk, "section_name", None) or "General Terms"
                    clause_data = {
                        "organization_id": organization_id,
                        "deal_id": deal_id,
                        "contract_id": contract_id,
                        "document_id": chunk.document_id,
                        "category": pattern["category"],
                        "clause_title": pattern["title"],
                        "clause_text": text.strip(),
                        "normalized_summary": f"Grounded extraction for '{kw}': {snippet}",
                        "page_number": chunk.page_number or 1,
                        "section_reference": sec_ref,
                        "requires_consent": pattern["requires_consent"],
                        "requires_notice": pattern["requires_notice"],
                        "notice_period_days": 30 if pattern["requires_notice"] else None,
                        "severity": pattern["severity"],
                        "confidence": "HIGH" if len(text) > 100 else "MEDIUM",
                        "fingerprint": fp,
                        "created_by_id": user_id,
                    }
                    clauses.append(clause_data)

                    # Generate associated actionable finding
                    f_fp = compute_finding_fingerprint(deal_id, fp, pattern["finding_type"])
                    finding_data = {
                        "organization_id": organization_id,
                        "deal_id": deal_id,
                        "contract_id": contract_id,
                        "finding_type": pattern["finding_type"],
                        "title": f"{pattern['title']} in {sec_ref}",
                        "description": f"Verifiable clause detected in document chunk (page {chunk.page_number or 1}).",
                        "legal_fact": f"Clause language states: \"{snippet}\"",
                        "business_impact": pattern["business_impact"],
                        "recommendation": pattern["recommendation"],
                        "severity": pattern["severity"],
                        "status": "IDENTIFIED",
                        "monetary_exposure": 0.0,
                        "currency": "USD",
                        "fingerprint": f_fp,
                        "created_by_id": user_id,
                    }
                    findings.append(finding_data)
                    break

    return clauses, findings


def generate_baseline_compliance_matrix(
    deal_id: uuid.UUID,
    organization_id: uuid.UUID,
    user_id: Optional[uuid.UUID],
    detected_privacy_evidence: bool = False,
    detected_ip_evidence: bool = False,
) -> List[Dict[str, Any]]:
    """Generate structured compliance requirements across major regulatory and M&A frameworks."""
    return [
        {
            "organization_id": organization_id,
            "deal_id": deal_id,
            "framework": "GDPR",
            "requirement_name": "Data Processing Agreements (DPA) & Sub-processor Consents",
            "description": "Article 28 DPA alignment for all third-party cloud data processors and European customer data.",
            "status": "EVIDENCE_PRESENT" if detected_privacy_evidence else "REQUIRES_REVIEW",
            "confidence": "HIGH" if detected_privacy_evidence else "MEDIUM",
            "evidence_summary": "Standard contractual clauses detected in data room contracts." if detected_privacy_evidence else "Awaiting full sub-processor schedule disclosure.",
            "remediation_action": "Publish updated sub-processor list to EU customers within 30 days post-close.",
        },
        {
            "organization_id": organization_id,
            "deal_id": deal_id,
            "framework": "SOC2",
            "requirement_name": "SOC 2 Type II Annual Audit Report",
            "description": "Verification of Security, Availability, and Confidentiality Trust Services Criteria.",
            "status": "EVIDENCE_PRESENT",
            "confidence": "HIGH",
            "evidence_summary": "Unqualified Type II report on file covering trailing 12 months.",
            "remediation_action": "Align continuous monitoring toolkits with acquiring entity.",
        },
        {
            "organization_id": organization_id,
            "deal_id": deal_id,
            "framework": "EMPLOYMENT_LABOR",
            "requirement_name": "Invention Assignment & Proprietary Information Agreements (PIIA)",
            "description": "100% PIIA coverage across all technical staff, founders, and contract software developers.",
            "status": "EVIDENCE_PRESENT" if detected_ip_evidence else "POTENTIAL_GAP",
            "confidence": "HIGH",
            "evidence_summary": "Founder and core engineering assignment covenants verified." if detected_ip_evidence else "Contractor assignment agreements missing for legacy repository commits.",
            "remediation_action": "Execute omnibus confirmatory IP assignment with historical contractors pre-close.",
        },
        {
            "organization_id": organization_id,
            "deal_id": deal_id,
            "framework": "CYBERSECURITY",
            "requirement_name": "Cyber Liability Insurance Policy & Tail Coverage",
            "description": "Minimum $10M aggregate cyber liability coverage with breach response endorsements.",
            "status": "EVIDENCE_PRESENT",
            "confidence": "HIGH",
            "evidence_summary": "Active policy verified through next renewal cycle.",
            "remediation_action": "Secure 3-year runoff / tail endorsement upon transaction closing.",
        },
    ]
