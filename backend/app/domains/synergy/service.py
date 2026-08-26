"""Synergy Business Service orchestrating value creation analysis, waterfalls, and realization tracking."""

import uuid
from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import NotFoundException
from app.domains.audit.models import AuditEvent
from app.domains.common.context import TenantContext
from app.domains.synergy.config import (
    calculate_expected_value,
    calculate_potential_value,
    calculate_value_capture_rate,
    validate_status_transition,
)
from app.domains.synergy.engine import (
    aggregate_synergy_portfolio,
    compute_synergy_5yr_schedule,
    compute_synergy_value_bridge,
)
from app.domains.synergy.models import SynergyOpportunity
from app.domains.synergy.repository import SynergyRepository
from app.domains.synergy.schemas import (
    RealizationScheduleResponse,
    SynergyActualLogRequest,
    SynergyCreateRequest,
    SynergyResponse,
    SynergyStatusUpdateRequest,
    SynergySummaryResponse,
    SynergyUpdateRequest,
    ValueBridgeResponse,
)


class SynergyService:
    """Business service for synergy discovery, realization tracking, and value creation bridges."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = SynergyRepository(session)

    async def list_synergies(
        self, context: TenantContext, deal_id: uuid.UUID, synergy_type: Optional[str] = None
    ) -> List[SynergyResponse]:
        """List all synergy opportunities for a deal."""
        context.validate_deal_access(deal_id)
        synergies = await self.repo.list_synergies(context.organization_id, deal_id, synergy_type)
        return [self._format_synergy(s) for s in synergies]

    async def get_synergy(
        self, context: TenantContext, deal_id: uuid.UUID, synergy_id: uuid.UUID
    ) -> SynergyResponse:
        """Fetch a single synergy opportunity."""
        context.validate_deal_access(deal_id)
        synergy = await self.repo.get_synergy(context.organization_id, deal_id, synergy_id)
        if not synergy:
            raise NotFoundException("SynergyOpportunity", synergy_id)
        return self._format_synergy(synergy)

    async def create_synergy(
        self, context: TenantContext, deal_id: uuid.UUID, payload: SynergyCreateRequest
    ) -> SynergyResponse:
        """Create and calculate a new synergy opportunity."""
        context.validate_deal_access(deal_id)
        data_ctx = await self.repo.get_deal_diligence_context(context.organization_id, deal_id)
        if not data_ctx:
            raise NotFoundException("Deal", deal_id)

        # 1. Compute Potential and Expected Values
        pot_val = calculate_potential_value(
            payload.baseline_value, payload.target_value, payload.synergy_type
        )
        exp_val = calculate_expected_value(
            pot_val, payload.realization_rate_pct, payload.probability_pct
        )

        create_data = payload.model_dump()
        create_data["potential_annual_value"] = pot_val
        create_data["expected_annual_value"] = exp_val

        synergy = await self.repo.create_synergy(
            organization_id=context.organization_id,
            deal_id=deal_id,
            company_id=getattr(data_ctx["deal"], "target_company_id", None),
            data=create_data,
            user_id=context.user_id,
        )

        # Audit Event
        self.session.add(
            AuditEvent(
                organization_id=context.organization_id,
                actor_user_id=context.user_id,
                deal_id=deal_id,
                action="SYNERGY_CREATED",
                entity_type="SynergyOpportunity",
                entity_id=synergy.id,
                details={
                    "name": synergy.name,
                    "synergy_type": synergy.synergy_type,
                    "potential_val": pot_val,
                    "expected_val": exp_val,
                },
            )
        )
        await self.session.commit()
        return self._format_synergy(synergy)

    async def update_synergy(
        self, context: TenantContext, deal_id: uuid.UUID, synergy_id: uuid.UUID, payload: SynergyUpdateRequest
    ) -> SynergyResponse:
        """Update synergy attributes and re-evaluate expected values."""
        context.validate_deal_access(deal_id)
        synergy = await self.repo.get_synergy(context.organization_id, deal_id, synergy_id)
        if not synergy:
            raise NotFoundException("SynergyOpportunity", synergy_id)

        updates = payload.model_dump(exclude_unset=True)

        # Recompute potential and expected if baseline/target/rates updated
        baseline = updates.get("baseline_value", synergy.baseline_value)
        target = updates.get("target_value", synergy.target_value)
        stype = updates.get("synergy_type", synergy.synergy_type)
        r_rate = updates.get("realization_rate_pct", synergy.realization_rate_pct)
        prob = updates.get("probability_pct", synergy.probability_pct)

        updates["potential_annual_value"] = calculate_potential_value(baseline, target, stype)
        updates["expected_annual_value"] = calculate_expected_value(
            updates["potential_annual_value"], r_rate, prob
        )

        updated = await self.repo.update_synergy(synergy, updates)
        await self.session.commit()
        return self._format_synergy(updated)

    async def update_synergy_status(
        self, context: TenantContext, deal_id: uuid.UUID, synergy_id: uuid.UUID, payload: SynergyStatusUpdateRequest
    ) -> SynergyResponse:
        """Transition synergy lifecycle status with state machine enforcement."""
        context.validate_deal_access(deal_id)
        synergy = await self.repo.get_synergy(context.organization_id, deal_id, synergy_id)
        if not synergy:
            raise NotFoundException("SynergyOpportunity", synergy_id)

        validate_status_transition(synergy.status, payload.status)

        old_status = synergy.status
        synergy.status = payload.status
        if payload.notes:
            synergy.notes = f"{synergy.notes or ''}\n[Status Change {old_status} -> {payload.status}]: {payload.notes}".strip()

        # Audit Event
        self.session.add(
            AuditEvent(
                organization_id=context.organization_id,
                actor_user_id=context.user_id,
                deal_id=deal_id,
                action="SYNERGY_STATUS_UPDATED",
                entity_type="SynergyOpportunity",
                entity_id=synergy.id,
                details={"old_status": old_status, "new_status": payload.status},
            )
        )
        await self.session.commit()
        return self._format_synergy(synergy)

    async def delete_synergy(
        self, context: TenantContext, deal_id: uuid.UUID, synergy_id: uuid.UUID
    ) -> None:
        """Delete a synergy opportunity."""
        context.validate_deal_access(deal_id)
        synergy = await self.repo.get_synergy(context.organization_id, deal_id, synergy_id)
        if not synergy:
            raise NotFoundException("SynergyOpportunity", synergy_id)

        await self.repo.delete_synergy(synergy)
        await self.session.commit()

    async def log_actual_realization(
        self, context: TenantContext, deal_id: uuid.UUID, synergy_id: uuid.UUID, payload: SynergyActualLogRequest
    ) -> SynergyResponse:
        """Log actual realization performance for a period."""
        context.validate_deal_access(deal_id)
        synergy = await self.repo.get_synergy(context.organization_id, deal_id, synergy_id)
        if not synergy:
            raise NotFoundException("SynergyOpportunity", synergy_id)

        log = await self.repo.log_actual_realization(
            organization_id=context.organization_id,
            deal_id=deal_id,
            synergy=synergy,
            fiscal_period=payload.fiscal_period,
            planned_value=payload.planned_value,
            actual_value=payload.actual_value,
            notes=payload.notes,
            user_id=context.user_id,
        )

        self.session.add(
            AuditEvent(
                organization_id=context.organization_id,
                actor_user_id=context.user_id,
                deal_id=deal_id,
                action="SYNERGY_REALIZATION_LOGGED",
                entity_type="SynergyRealizationLog",
                entity_id=log.id,
                details={
                    "synergy_id": str(synergy.id),
                    "period": payload.fiscal_period,
                    "actual": payload.actual_value,
                    "variance": log.variance,
                },
            )
        )
        await self.session.commit()
        return self._format_synergy(synergy)

    async def get_summary(
        self, context: TenantContext, deal_id: uuid.UUID
    ) -> SynergySummaryResponse:
        """Retrieve portfolio-level synergy summary and capture rates."""
        context.validate_deal_access(deal_id)
        synergies = await self.repo.list_synergies(context.organization_id, deal_id)
        agg = aggregate_synergy_portfolio(synergies)
        return SynergySummaryResponse(deal_id=deal_id, **agg)

    async def get_value_bridge(
        self, context: TenantContext, deal_id: uuid.UUID
    ) -> ValueBridgeResponse:
        """Compute Value Creation Waterfall Bridge and synergy impact on EV & Decision Score."""
        context.validate_deal_access(deal_id)
        data = await self.repo.get_deal_diligence_context(context.organization_id, deal_id)
        if not data:
            raise NotFoundException("Deal", deal_id)

        synergies = await self.repo.list_synergies(context.organization_id, deal_id)
        bridge = compute_synergy_value_bridge(
            deal=data["deal"],
            statements=data["statements"],
            metrics=data["metrics"],
            qoe_adjustments=data["qoe_adjustments"],
            valuation=data["valuation"],
            valuation_outputs=data["valuation_outputs"],
            risks=data["risks"],
            documents=data["documents"],
            citations=data["citations"],
            synergies=synergies,
        )
        return ValueBridgeResponse(deal_id=deal_id, **bridge)

    async def get_realization_schedule(
        self, context: TenantContext, deal_id: uuid.UUID
    ) -> RealizationScheduleResponse:
        """Compute 5-year phased realization trajectory."""
        context.validate_deal_access(deal_id)
        synergies = await self.repo.list_synergies(context.organization_id, deal_id)
        schedule_data = compute_synergy_5yr_schedule(synergies)
        return RealizationScheduleResponse(deal_id=deal_id, **schedule_data)

    def _format_synergy(self, synergy: SynergyOpportunity) -> SynergyResponse:
        """Convert ORM model to typed response with computed variance and capture rate."""
        pot = float(synergy.potential_annual_value or 0.0)
        real = float(synergy.realized_annual_value or 0.0)
        exp = float(synergy.expected_annual_value or 0.0)
        capture_rate = calculate_value_capture_rate(real, pot)
        variance = round(real - exp, 2)

        return SynergyResponse(
            id=synergy.id,
            deal_id=synergy.deal_id,
            company_id=synergy.company_id,
            organization_id=synergy.organization_id,
            name=synergy.name,
            description=synergy.description,
            synergy_type=synergy.synergy_type,
            category=synergy.category,
            status=synergy.status,
            confidence=synergy.confidence,
            baseline_value=synergy.baseline_value,
            target_value=synergy.target_value,
            potential_annual_value=synergy.potential_annual_value,
            realization_rate_pct=synergy.realization_rate_pct,
            probability_pct=synergy.probability_pct,
            expected_annual_value=synergy.expected_annual_value,
            one_time_integration_cost=synergy.one_time_integration_cost,
            realization_curve=synergy.realization_curve,
            evidence_citation_ids=synergy.evidence_citation_ids or [],
            owner=synergy.owner,
            realized_annual_value=synergy.realized_annual_value,
            value_capture_rate_pct=capture_rate,
            variance=variance,
            notes=synergy.notes,
            created_by_id=synergy.created_by_id,
            created_at=synergy.created_at,
            updated_at=synergy.updated_at,
        )
