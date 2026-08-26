"""Database Repository for Synergy Opportunities and Actual Realization Logging."""

import uuid
from typing import Any, Dict, List, Optional
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.domains.decision.repository import DecisionRepository
from app.domains.synergy.models import SynergyOpportunity, SynergyRealizationLog


class SynergyRepository:
    """Async database repository for synergy opportunity management and realization tracking."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.decision_repo = DecisionRepository(session)

    async def get_deal_diligence_context(
        self, organization_id: uuid.UUID, deal_id: uuid.UUID
    ) -> Optional[Dict[str, Any]]:
        """Fetch complete diligence context for value bridge calculations."""
        return await self.decision_repo.get_complete_deal_diligence_context(
            organization_id, deal_id
        )

    async def list_synergies(
        self, organization_id: uuid.UUID, deal_id: uuid.UUID, synergy_type: Optional[str] = None
    ) -> List[SynergyOpportunity]:
        """List all synergy opportunities for a deal."""
        query = (
            select(SynergyOpportunity)
            .where(
                SynergyOpportunity.organization_id == organization_id,
                SynergyOpportunity.deal_id == deal_id,
            )
            .order_by(SynergyOpportunity.created_at.desc())
        )
        if synergy_type:
            query = query.where(SynergyOpportunity.synergy_type == synergy_type)

        res = await self.session.execute(query)
        return list(res.scalars().all())

    async def get_synergy(
        self, organization_id: uuid.UUID, deal_id: uuid.UUID, synergy_id: uuid.UUID
    ) -> Optional[SynergyOpportunity]:
        """Fetch a specific synergy opportunity by ID."""
        query = select(SynergyOpportunity).where(
            SynergyOpportunity.organization_id == organization_id,
            SynergyOpportunity.deal_id == deal_id,
            SynergyOpportunity.id == synergy_id,
        )
        res = await self.session.execute(query)
        return res.scalar_one_or_none()

    async def create_synergy(
        self,
        organization_id: uuid.UUID,
        deal_id: uuid.UUID,
        company_id: Optional[uuid.UUID],
        data: Dict[str, Any],
        user_id: Optional[uuid.UUID] = None,
    ) -> SynergyOpportunity:
        """Create and persist a new synergy opportunity."""
        synergy = SynergyOpportunity(
            organization_id=organization_id,
            deal_id=deal_id,
            company_id=company_id,
            name=data["name"],
            description=data.get("description"),
            synergy_type=data["synergy_type"],
            category=data["category"],
            status="IDENTIFIED",
            confidence=data.get("confidence", "MEDIUM"),
            baseline_value=data.get("baseline_value", 0.0),
            target_value=data["target_value"],
            potential_annual_value=data["potential_annual_value"],
            realization_rate_pct=data.get("realization_rate_pct", 100.0),
            probability_pct=data.get("probability_pct", 80.0),
            expected_annual_value=data["expected_annual_value"],
            one_time_integration_cost=data.get("one_time_integration_cost", 0.0),
            realization_curve=data.get("realization_curve"),
            evidence_citation_ids=data.get("evidence_citation_ids", []),
            owner=data.get("owner"),
            realized_annual_value=0.0,
            notes=data.get("notes"),
            created_by_id=user_id,
        )
        self.session.add(synergy)
        await self.session.flush()
        return synergy

    async def update_synergy(
        self, synergy: SynergyOpportunity, updates: Dict[str, Any]
    ) -> SynergyOpportunity:
        """Update fields on an existing synergy opportunity."""
        for k, v in updates.items():
            if v is not None and hasattr(synergy, k):
                setattr(synergy, k, v)
        await self.session.flush()
        return synergy

    async def delete_synergy(self, synergy: SynergyOpportunity) -> None:
        """Delete synergy opportunity."""
        await self.session.delete(synergy)
        await self.session.flush()

    async def log_actual_realization(
        self,
        organization_id: uuid.UUID,
        deal_id: uuid.UUID,
        synergy: SynergyOpportunity,
        fiscal_period: str,
        planned_value: float,
        actual_value: float,
        notes: Optional[str] = None,
        user_id: Optional[uuid.UUID] = None,
    ) -> SynergyRealizationLog:
        """Record an actual realization entry and update the synergy's cumulative realized value."""
        variance = actual_value - planned_value
        log = SynergyRealizationLog(
            organization_id=organization_id,
            deal_id=deal_id,
            synergy_id=synergy.id,
            fiscal_period=fiscal_period,
            planned_value=planned_value,
            actual_value=actual_value,
            variance=variance,
            notes=notes,
            logged_by_id=user_id,
        )
        self.session.add(log)

        # Update synergy cumulative realized value
        synergy.realized_annual_value = float(synergy.realized_annual_value or 0.0) + actual_value
        if synergy.realized_annual_value >= synergy.potential_annual_value and synergy.potential_annual_value > 0:
            synergy.status = "REALIZED"
        elif synergy.realized_annual_value > 0 and synergy.status not in ["REALIZED", "ABANDONED"]:
            synergy.status = "PARTIALLY_REALIZED"

        await self.session.flush()
        return log
