"""Decision Intelligence Business Service orchestrating cross-domain scoring and explainability."""

import uuid
from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import NotFoundException
from app.domains.audit.models import AuditEvent
from app.domains.common.context import TenantContext
from app.domains.decision.config import get_band_description
from app.domains.decision.engine import calculate_composite_decision_score
from app.domains.decision.models import DecisionScore
from app.domains.decision.repository import DecisionRepository
from app.domains.decision.schemas import (
    DecisionScoreCalculateRequest,
    DecisionScoreHistoryItem,
    DecisionScoreHistoryResponse,
    DecisionScoreResponse,
    DriverItem,
    ScoreComponentDetail,
)


class DecisionService:
    """Business service for calculating and retrieving explainable decision intelligence scores."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = DecisionRepository(session)

    async def get_or_calculate_score(
        self,
        context: TenantContext,
        deal_id: uuid.UUID,
        force_recalculate: bool = False,
        custom_weights: Optional[Dict[str, float]] = None,
    ) -> DecisionScoreResponse:
        """Fetch latest persisted score or calculate a fresh score if none exists or if forced."""
        context.validate_deal_access(deal_id)

        if not force_recalculate and not custom_weights:
            latest = await self.repo.get_latest_decision_score(context.organization_id, deal_id)
            if latest:
                return self._format_decision_response(latest)

        # Calculate fresh score
        return await self.calculate_and_persist_score(
            context, deal_id, custom_weights=custom_weights
        )

    async def calculate_and_persist_score(
        self,
        context: TenantContext,
        deal_id: uuid.UUID,
        custom_weights: Optional[Dict[str, float]] = None,
    ) -> DecisionScoreResponse:
        """Run complete deterministic calculation, save to database, and log audit event."""
        context.validate_deal_access(deal_id)

        data = await self.repo.get_complete_deal_diligence_context(
            context.organization_id, deal_id
        )
        if not data:
            raise NotFoundException("Deal", deal_id)

        deal = data["deal"]
        calculated = calculate_composite_decision_score(
            deal=deal,
            statements=data["statements"],
            metrics=data["metrics"],
            qoe_adjustments=data["qoe_adjustments"],
            valuation=data["valuation"],
            valuation_outputs=data["valuation_outputs"],
            risks=data["risks"],
            documents=data["documents"],
            citations=data["citations"],
            custom_weights=custom_weights,
        )

        record = await self.repo.save_decision_score(
            organization_id=context.organization_id,
            deal_id=deal_id,
            company_id=getattr(deal, "target_company_id", None),
            score_data=calculated,
            user_id=context.user_id,
        )

        # Audit Event Logging
        audit_event = AuditEvent(
            organization_id=context.organization_id,
            actor_user_id=context.user_id,
            deal_id=deal_id,
            action="DECISION_SCORE_CALCULATED",
            entity_type="DecisionScore",
            entity_id=record.id,
            details={
                "overall_score": calculated["overall_score"],
                "decision_band": calculated["decision_band"],
                "confidence_score": calculated["confidence_score"],
                "scoring_version": calculated["scoring_version"],
            },
        )
        self.session.add(audit_event)
        await self.session.commit()

        return self._format_decision_response(record)

    async def get_history(
        self, context: TenantContext, deal_id: uuid.UUID, limit: int = 50
    ) -> DecisionScoreHistoryResponse:
        """Retrieve chronological history of decision score calculations for a deal."""
        context.validate_deal_access(deal_id)
        records = await self.repo.get_decision_score_history(
            context.organization_id, deal_id, limit=limit
        )

        history_items = [
            DecisionScoreHistoryItem(
                id=r.id,
                overall_score=r.overall_score,
                decision_band=r.decision_band,
                confidence_score=r.confidence_score,
                scoring_version=r.scoring_version,
                created_at=r.created_at,
                calculated_by_id=r.calculated_by_id,
            )
            for r in records
        ]

        return DecisionScoreHistoryResponse(
            deal_id=deal_id,
            total_calculations=len(history_items),
            history=history_items,
        )

    def _format_decision_response(self, record: DecisionScore) -> DecisionScoreResponse:
        """Convert ORM DecisionScore model into typed response schema."""
        raw_components = record.component_scores or {}
        components: Dict[str, ScoreComponentDetail] = {}

        for name, comp_data in raw_components.items():
            components[name] = ScoreComponentDetail(
                name=comp_data.get("name", name),
                score=comp_data.get("score", 0.0),
                weight=comp_data.get("weight", 0.0),
                weighted_contribution=comp_data.get("weighted_contribution", 0.0),
                status=comp_data.get("status", "AVAILABLE"),
                confidence=comp_data.get("confidence", 1.0),
                raw_inputs=comp_data.get("raw_inputs", {}),
                explanation=comp_data.get("explanation", ""),
                drivers=comp_data.get("drivers", []),
            )

        pos_drivers = [
            DriverItem(
                driver=d.get("driver", ""),
                type=d.get("type", "POSITIVE"),
                impact=d.get("impact", "MEDIUM"),
                component=d.get("component"),
            )
            for d in (record.positive_drivers or [])
        ]

        neg_drivers = [
            DriverItem(
                driver=d.get("driver", ""),
                type=d.get("type", "NEGATIVE"),
                impact=d.get("impact", "MEDIUM"),
                component=d.get("component"),
            )
            for d in (record.negative_drivers or [])
        ]

        return DecisionScoreResponse(
            id=record.id,
            deal_id=record.deal_id,
            company_id=record.company_id,
            score_type=record.score_type,
            overall_score=record.overall_score,
            decision_band=record.decision_band,
            decision_band_description=get_band_description(record.decision_band),
            confidence_score=record.confidence_score,
            scoring_version=record.scoring_version,
            created_at=record.created_at,
            components=components,
            positive_drivers=pos_drivers,
            negative_drivers=neg_drivers,
            missing_information=record.missing_information or [],
            recommendations=record.recommendations or [],
        )
