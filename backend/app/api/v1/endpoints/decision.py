"""REST API Endpoints for Composite DealGuard Decision Score & Explainable Intelligence."""

import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import validate_deal_membership
from app.core.database import get_db
from app.domains.common.context import TenantContext
from app.domains.auth.permissions import PERM_ANALYSIS_RUN, PERM_DEALS_READ
from app.domains.decision.schemas import (
    DecisionScoreCalculateRequest,
    DecisionScoreHistoryResponse,
    DecisionScoreResponse,
)
from app.domains.decision.service import DecisionService

router = APIRouter(prefix="/deals/{deal_id}/decision-score", tags=["decision-score"])


@router.get(
    "",
    summary="Get Current Composite DealGuard Decision Score",
    status_code=status.HTTP_200_OK,
    response_model=DecisionScoreResponse,
)
async def get_decision_score(
    deal_id: uuid.UUID,
    force_recalculate: bool = Query(False, description="Force fresh recalculation of score"),
    db: AsyncSession = Depends(get_db),
    context: TenantContext = Depends(validate_deal_membership),
) -> DecisionScoreResponse:
    """Retrieve the authoritative Decision Score, components, drivers, and recommendations."""
    context.require_permission(PERM_DEALS_READ)
    service = DecisionService(db)
    return await service.get_or_calculate_score(
        context, deal_id, force_recalculate=force_recalculate
    )


@router.post(
    "/calculate",
    summary="Calculate or Recalculate Decision Score with Audit Logging",
    status_code=status.HTTP_201_CREATED,
    response_model=DecisionScoreResponse,
)
async def calculate_decision_score(
    deal_id: uuid.UUID,
    payload: Optional[DecisionScoreCalculateRequest] = None,
    db: AsyncSession = Depends(get_db),
    context: TenantContext = Depends(validate_deal_membership),
) -> DecisionScoreResponse:
    """Trigger explicit deterministic recalculation across all cross-domain intelligence inputs."""
    context.require_permission(PERM_ANALYSIS_RUN)
    service = DecisionService(db)
    custom_weights = payload.custom_weights if payload else None
    return await service.calculate_and_persist_score(
        context, deal_id, custom_weights=custom_weights
    )


@router.get(
    "/breakdown",
    summary="Get Detailed Component Breakdown and Explainability Drivers",
    status_code=status.HTTP_200_OK,
    response_model=DecisionScoreResponse,
)
async def get_decision_score_breakdown(
    deal_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    context: TenantContext = Depends(validate_deal_membership),
) -> DecisionScoreResponse:
    """Get deep-dive explainability details, raw evaluated metrics, and factor lineage."""
    context.require_permission(PERM_DEALS_READ)
    service = DecisionService(db)
    return await service.get_or_calculate_score(context, deal_id, force_recalculate=False)


@router.get(
    "/history",
    summary="Get Historical Decision Score Calculations",
    status_code=status.HTTP_200_OK,
    response_model=DecisionScoreHistoryResponse,
)
async def get_decision_score_history(
    deal_id: uuid.UUID,
    limit: int = Query(50, ge=1, le=100, description="Max history records to return"),
    db: AsyncSession = Depends(get_db),
    context: TenantContext = Depends(validate_deal_membership),
) -> DecisionScoreHistoryResponse:
    """Retrieve chronological calculation audit history and score version comparisons."""
    context.require_permission(PERM_DEALS_READ)
    service = DecisionService(db)
    return await service.get_history(context, deal_id, limit=limit)
