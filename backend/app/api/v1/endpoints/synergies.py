"""REST API Endpoints for Synergy Realization & Value Creation Intelligence."""

import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import validate_deal_membership
from app.core.database import get_db
from app.domains.auth.permissions import PERM_ANALYSIS_RUN, PERM_DEALS_READ
from app.domains.common.context import TenantContext
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
from app.domains.synergy.service import SynergyService

router = APIRouter(prefix="/deals/{deal_id}/synergies", tags=["synergies"])


@router.get(
    "",
    summary="List Synergy Opportunities for Deal Workspace",
    status_code=status.HTTP_200_OK,
    response_model=List[SynergyResponse],
)
async def list_synergies(
    deal_id: uuid.UUID,
    synergy_type: Optional[str] = Query(None, description="Filter by REVENUE, COST, OPERATIONAL"),
    db: AsyncSession = Depends(get_db),
    context: TenantContext = Depends(validate_deal_membership),
) -> List[SynergyResponse]:
    """Retrieve all identified, planned, and realized synergy opportunities for a deal."""
    context.require_permission(PERM_DEALS_READ)
    service = SynergyService(db)
    return await service.list_synergies(context, deal_id, synergy_type)


@router.post(
    "",
    summary="Create New Synergy Opportunity",
    status_code=status.HTTP_201_CREATED,
    response_model=SynergyResponse,
)
async def create_synergy(
    deal_id: uuid.UUID,
    payload: SynergyCreateRequest,
    db: AsyncSession = Depends(get_db),
    context: TenantContext = Depends(validate_deal_membership),
) -> SynergyResponse:
    """Register and compute expected values for a new synergy value creation opportunity."""
    context.require_permission(PERM_ANALYSIS_RUN)
    service = SynergyService(db)
    return await service.create_synergy(context, deal_id, payload)


@router.get(
    "/summary",
    summary="Get Synergy Portfolio Summary & Value Capture Rate",
    status_code=status.HTTP_200_OK,
    response_model=SynergySummaryResponse,
)
async def get_synergy_summary(
    deal_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    context: TenantContext = Depends(validate_deal_membership),
) -> SynergySummaryResponse:
    """Retrieve aggregate potential, expected, and realized synergy values and capture percentages."""
    context.require_permission(PERM_DEALS_READ)
    service = SynergyService(db)
    return await service.get_summary(context, deal_id)


@router.get(
    "/value-bridge",
    summary="Get Value Creation Waterfall Bridge",
    status_code=status.HTTP_200_OK,
    response_model=ValueBridgeResponse,
)
async def get_value_bridge(
    deal_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    context: TenantContext = Depends(validate_deal_membership),
) -> ValueBridgeResponse:
    """Compute mathematical Value Creation Waterfall Bridge and synergy impact on EV and Decision Score."""
    context.require_permission(PERM_DEALS_READ)
    service = SynergyService(db)
    return await service.get_value_bridge(context, deal_id)


@router.get(
    "/realization",
    summary="Get 5-Year Synergy Realization Schedule",
    status_code=status.HTTP_200_OK,
    response_model=RealizationScheduleResponse,
)
async def get_realization_schedule(
    deal_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    context: TenantContext = Depends(validate_deal_membership),
) -> RealizationScheduleResponse:
    """Retrieve phased 5-year trajectory schedule of revenue, cost, EBITDA, and cash flows."""
    context.require_permission(PERM_DEALS_READ)
    service = SynergyService(db)
    return await service.get_realization_schedule(context, deal_id)


@router.get(
    "/{synergy_id}",
    summary="Get Specific Synergy Opportunity Details",
    status_code=status.HTTP_200_OK,
    response_model=SynergyResponse,
)
async def get_synergy(
    deal_id: uuid.UUID,
    synergy_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    context: TenantContext = Depends(validate_deal_membership),
) -> SynergyResponse:
    """Retrieve details, metrics, and realization status for a specific synergy."""
    context.require_permission(PERM_DEALS_READ)
    service = SynergyService(db)
    return await service.get_synergy(context, deal_id, synergy_id)


@router.put(
    "/{synergy_id}",
    summary="Update Synergy Opportunity",
    status_code=status.HTTP_200_OK,
    response_model=SynergyResponse,
)
async def update_synergy(
    deal_id: uuid.UUID,
    synergy_id: uuid.UUID,
    payload: SynergyUpdateRequest,
    db: AsyncSession = Depends(get_db),
    context: TenantContext = Depends(validate_deal_membership),
) -> SynergyResponse:
    """Update synergy attributes, targets, or realization parameters."""
    context.require_permission(PERM_ANALYSIS_RUN)
    service = SynergyService(db)
    return await service.update_synergy(context, deal_id, synergy_id, payload)


@router.patch(
    "/{synergy_id}/status",
    summary="Transition Synergy Lifecycle Status",
    status_code=status.HTTP_200_OK,
    response_model=SynergyResponse,
)
async def update_synergy_status(
    deal_id: uuid.UUID,
    synergy_id: uuid.UUID,
    payload: SynergyStatusUpdateRequest,
    db: AsyncSession = Depends(get_db),
    context: TenantContext = Depends(validate_deal_membership),
) -> SynergyResponse:
    """Advance or update synergy status (e.g. VALIDATED -> PLANNED -> IN_PROGRESS -> REALIZED)."""
    context.require_permission(PERM_ANALYSIS_RUN)
    service = SynergyService(db)
    return await service.update_synergy_status(context, deal_id, synergy_id, payload)


@router.post(
    "/{synergy_id}/actual",
    summary="Log Actual Realized Synergy Value",
    status_code=status.HTTP_200_OK,
    response_model=SynergyResponse,
)
async def log_actual_realization(
    deal_id: uuid.UUID,
    synergy_id: uuid.UUID,
    payload: SynergyActualLogRequest,
    db: AsyncSession = Depends(get_db),
    context: TenantContext = Depends(validate_deal_membership),
) -> SynergyResponse:
    """Log actual performance for a fiscal period and update cumulative capture rate."""
    context.require_permission(PERM_ANALYSIS_RUN)
    service = SynergyService(db)
    return await service.log_actual_realization(context, deal_id, synergy_id, payload)


@router.delete(
    "/{synergy_id}",
    summary="Delete Synergy Opportunity",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_synergy(
    deal_id: uuid.UUID,
    synergy_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    context: TenantContext = Depends(validate_deal_membership),
) -> None:
    """Delete a synergy opportunity."""
    context.require_permission(PERM_ANALYSIS_RUN)
    service = SynergyService(db)
    await service.delete_synergy(context, deal_id, synergy_id)
