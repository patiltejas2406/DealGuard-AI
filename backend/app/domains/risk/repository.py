"""17-Pillar Deal Risk Repository Layer."""

import uuid
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.domains.documents.models import Citation, Document
from app.domains.risk.models import Risk, RiskEvidence
from app.domains.risk.scoring import calculate_risk_evaluation
from app.domains.risk.taxonomy import DetectionSource, RiskCategory, RiskLevel, RiskStatus


class RiskRepository:
    """Tenant-scoped persistence operations for 17-Pillar Deal Risks."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_risks_for_deal(
        self,
        organization_id: uuid.UUID,
        deal_id: uuid.UUID,
        category: Optional[str] = None,
        risk_level: Optional[str] = None,
        status: Optional[str] = None,
        min_severity: Optional[int] = None,
        min_likelihood: Optional[int] = None,
        search: Optional[str] = None,
        sort_by: str = "score",
        sort_desc: bool = True,
        offset: int = 0,
        limit: int = 100,
    ) -> Tuple[List[Risk], int]:
        """Query risks with comprehensive filtering, sorting, and eager loading of citations."""
        base_stmt = (
            select(Risk)
            .where(
                Risk.organization_id == organization_id,
                Risk.deal_id == deal_id,
            )
            .options(
                selectinload(Risk.evidence_items)
                .selectinload(RiskEvidence.citation)
                .selectinload(Citation.document)
            )
        )

        count_stmt = (
            select(func.count(Risk.id))
            .where(
                Risk.organization_id == organization_id,
                Risk.deal_id == deal_id,
            )
        )

        if category:
            base_stmt = base_stmt.where(Risk.category == category.upper())
            count_stmt = count_stmt.where(Risk.category == category.upper())

        if risk_level:
            base_stmt = base_stmt.where(Risk.risk_level == risk_level.upper())
            count_stmt = count_stmt.where(Risk.risk_level == risk_level.upper())

        if status:
            base_stmt = base_stmt.where(Risk.status == status.upper())
            count_stmt = count_stmt.where(Risk.status == status.upper())

        if min_severity:
            base_stmt = base_stmt.where(Risk.severity >= min_severity)
            count_stmt = count_stmt.where(Risk.severity >= min_severity)

        if min_likelihood:
            base_stmt = base_stmt.where(Risk.likelihood >= min_likelihood)
            count_stmt = count_stmt.where(Risk.likelihood >= min_likelihood)

        if search:
            search_term = f"%{search.strip()}%"
            base_stmt = base_stmt.where(
                (Risk.title.ilike(search_term)) | (Risk.description.ilike(search_term))
            )
            count_stmt = count_stmt.where(
                (Risk.title.ilike(search_term)) | (Risk.description.ilike(search_term))
            )

        # Apply Sorting
        sort_col = getattr(Risk, sort_by, Risk.score)
        if sort_desc:
            base_stmt = base_stmt.order_by(sort_col.desc(), Risk.created_at.desc())
        else:
            base_stmt = base_stmt.order_by(sort_col.asc(), Risk.created_at.asc())

        # Pagination
        base_stmt = base_stmt.offset(offset).limit(limit)

        total_res = await self.session.execute(count_stmt)
        total = total_res.scalar_one()

        res = await self.session.execute(base_stmt)
        items = list(res.scalars().all())

        return items, total

    async def get_risk_by_id(
        self, organization_id: uuid.UUID, deal_id: uuid.UUID, risk_id: uuid.UUID
    ) -> Optional[Risk]:
        """Fetch single risk with all evidence citations eagerly loaded."""
        stmt = (
            select(Risk)
            .where(
                Risk.organization_id == organization_id,
                Risk.deal_id == deal_id,
                Risk.id == risk_id,
            )
            .options(
                selectinload(Risk.evidence_items)
                .selectinload(RiskEvidence.citation)
                .selectinload(Citation.document)
            )
        )
        res = await self.session.execute(stmt)
        return res.scalars().first()

    async def create_risk(
        self,
        organization_id: uuid.UUID,
        deal_id: uuid.UUID,
        category: str,
        title: str,
        description: str,
        severity: int,
        likelihood: int,
        status: str = "IDENTIFIED",
        detection_source: str = "MANUAL_ENTRY",
        confidence_score: Optional[float] = None,
        mitigation_strategy: Optional[str] = None,
        recommendation: Optional[str] = None,
        company_id: Optional[uuid.UUID] = None,
        fingerprint: Optional[str] = None,
        owner_id: Optional[uuid.UUID] = None,
    ) -> Risk:
        """Create a new risk item with deterministic score and risk level calculation."""
        score, risk_level = calculate_risk_evaluation(severity, likelihood)

        risk = Risk(
            organization_id=organization_id,
            deal_id=deal_id,
            company_id=company_id,
            category=category.upper(),
            title=title,
            description=description,
            severity=severity,
            likelihood=likelihood,
            score=score,
            risk_level=risk_level.value,
            status=status.upper(),
            detection_source=detection_source.upper(),
            confidence_score=confidence_score,
            mitigation_strategy=mitigation_strategy,
            recommendation=recommendation,
            fingerprint=fingerprint,
            owner_id=owner_id,
        )
        self.session.add(risk)
        await self.session.flush()
        return risk

    async def update_risk(
        self,
        risk: Risk,
        title: Optional[str] = None,
        description: Optional[str] = None,
        category: Optional[str] = None,
        severity: Optional[int] = None,
        likelihood: Optional[int] = None,
        status: Optional[str] = None,
        mitigation_strategy: Optional[str] = None,
        recommendation: Optional[str] = None,
    ) -> Risk:
        """Update risk fields and recalculate score/level if severity/likelihood modified."""
        if title is not None:
            risk.title = title
        if description is not None:
            risk.description = description
        if category is not None:
            risk.category = category.upper()
        if status is not None:
            risk.status = status.upper()
        if mitigation_strategy is not None:
            risk.mitigation_strategy = mitigation_strategy
        if recommendation is not None:
            risk.recommendation = recommendation

        recalc = False
        if severity is not None:
            risk.severity = severity
            recalc = True
        if likelihood is not None:
            risk.likelihood = likelihood
            recalc = True

        if recalc:
            score, risk_level = calculate_risk_evaluation(risk.severity, risk.likelihood)
            risk.score = score
            risk.risk_level = risk_level.value

        await self.session.flush()
        return risk

    async def delete_risk(self, risk: Risk) -> None:
        """Delete risk item and cascade delete linked risk evidence."""
        await self.session.delete(risk)
        await self.session.flush()

    async def link_evidence_to_risk(
        self,
        organization_id: uuid.UUID,
        deal_id: uuid.UUID,
        risk_id: uuid.UUID,
        citation_id: uuid.UUID,
        relevance_explanation: Optional[str] = None,
        weight: float = 1.0,
    ) -> RiskEvidence:
        """Attach citation evidence to a risk item."""
        evidence = RiskEvidence(
            organization_id=organization_id,
            deal_id=deal_id,
            risk_id=risk_id,
            citation_id=citation_id,
            relevance_explanation=relevance_explanation,
            weight=weight,
        )
        self.session.add(evidence)
        await self.session.flush()
        return evidence
