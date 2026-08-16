"""17-Pillar Deal Risk Repository Layer."""

import uuid
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.domains.risk.models import Risk, RiskEvidence


class RiskRepository:
    """Tenant-scoped persistence operations for 17-Pillar Deal Risks."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_risks_for_deal(
        self, organization_id: uuid.UUID, deal_id: uuid.UUID, category: Optional[str] = None
    ) -> List[Risk]:
        stmt = (
            select(Risk)
            .where(
                Risk.organization_id == organization_id,
                Risk.deal_id == deal_id,
            )
            .options(selectinload(Risk.evidence_items).selectinload(RiskEvidence.citation))
            .order_by(Risk.score.desc(), Risk.severity.desc())
        )
        if category:
            stmt = stmt.where(Risk.category == category.upper())

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

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
        mitigation_strategy: Optional[str] = None,
        owner_id: Optional[uuid.UUID] = None,
    ) -> Risk:
        score = severity * likelihood
        risk = Risk(
            organization_id=organization_id,
            deal_id=deal_id,
            category=category.upper(),
            title=title,
            description=description,
            severity=severity,
            likelihood=likelihood,
            score=score,
            status=status,
            mitigation_strategy=mitigation_strategy,
            owner_id=owner_id,
        )
        self.session.add(risk)
        await self.session.flush()
        return risk

    async def link_evidence_to_risk(
        self,
        organization_id: uuid.UUID,
        deal_id: uuid.UUID,
        risk_id: uuid.UUID,
        citation_id: uuid.UUID,
        relevance_explanation: Optional[str] = None,
        weight: float = 1.0,
    ) -> RiskEvidence:
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
