"""REST API Endpoints for 100-Day Post-Acquisition Integration Execution Engine."""

import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import validate_deal_membership
from app.core.database import get_db
from app.domains.auth.permissions import PERM_ANALYSIS_RUN, PERM_DEALS_READ
from app.domains.common.context import TenantContext
from app.domains.integration.schemas import (
    BlockerCreateRequest,
    BlockerResolveRequest,
    BlockerResponse,
    CriticalPathResponse,
    DependencyCreateRequest,
    DependencyResponse,
    ExecutiveAttentionResponse,
    IntegrationHealthResponse,
    IntegrationProgramCreateRequest,
    IntegrationProgramResponse,
    IntegrationProgramUpdateRequest,
    MilestoneCreateRequest,
    MilestoneResponse,
    MilestoneStatusUpdateRequest,
    TimelineStageResponse,
    WorkstreamCreateRequest,
    WorkstreamResponse,
    WorkstreamStatusUpdateRequest,
)
from app.domains.integration.service import IntegrationService

router = APIRouter(prefix="/deals/{deal_id}/integration", tags=["integration"])


@router.get(
    "",
    summary="Get 100-Day Integration Program Overview",
    status_code=status.HTTP_200_OK,
    response_model=IntegrationProgramResponse,
)
async def get_integration_program(
    deal_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    context: TenantContext = Depends(validate_deal_membership),
) -> IntegrationProgramResponse:
    """Retrieve the primary 100-Day Integration Program overview, KPIs, and health score."""
    context.require_permission(PERM_DEALS_READ)
    service = IntegrationService(db)
    return await service.get_or_create_program(context, deal_id)


@router.post(
    "",
    summary="Initialize 100-Day Integration Program",
    status_code=status.HTTP_201_CREATED,
    response_model=IntegrationProgramResponse,
)
async def create_integration_program(
    deal_id: uuid.UUID,
    payload: IntegrationProgramCreateRequest,
    db: AsyncSession = Depends(get_db),
    context: TenantContext = Depends(validate_deal_membership),
) -> IntegrationProgramResponse:
    """Explicitly initialize or update 100-day integration program parameters."""
    context.require_permission(PERM_ANALYSIS_RUN)
    service = IntegrationService(db)
    return await service.create_program(context, deal_id, payload)


@router.put(
    "",
    summary="Update Integration Program Parameters",
    status_code=status.HTTP_200_OK,
    response_model=IntegrationProgramResponse,
)
async def update_integration_program(
    deal_id: uuid.UUID,
    payload: IntegrationProgramUpdateRequest,
    db: AsyncSession = Depends(get_db),
    context: TenantContext = Depends(validate_deal_membership),
) -> IntegrationProgramResponse:
    """Update program title, sponsor, or current day offset."""
    context.require_permission(PERM_ANALYSIS_RUN)
    service = IntegrationService(db)
    return await service.update_program(context, deal_id, payload)


# ==========================================
# Workstream Endpoints
# ==========================================

@router.get(
    "/workstreams",
    summary="List Integration Workstreams",
    status_code=status.HTTP_200_OK,
    response_model=List[WorkstreamResponse],
)
async def list_workstreams(
    deal_id: uuid.UUID,
    category: Optional[str] = Query(None, description="Filter by 17-pillar category"),
    db: AsyncSession = Depends(get_db),
    context: TenantContext = Depends(validate_deal_membership),
) -> List[WorkstreamResponse]:
    """List all functional workstreams for the integration program."""
    context.require_permission(PERM_DEALS_READ)
    service = IntegrationService(db)
    return await service.list_workstreams(context, deal_id, category)


@router.post(
    "/workstreams",
    summary="Create Integration Workstream",
    status_code=status.HTTP_201_CREATED,
    response_model=WorkstreamResponse,
)
async def create_workstream(
    deal_id: uuid.UUID,
    payload: WorkstreamCreateRequest,
    db: AsyncSession = Depends(get_db),
    context: TenantContext = Depends(validate_deal_membership),
) -> WorkstreamResponse:
    """Register a new functional integration workstream."""
    context.require_permission(PERM_ANALYSIS_RUN)
    service = IntegrationService(db)
    return await service.create_workstream(context, deal_id, payload)


@router.patch(
    "/workstreams/{workstream_id}/status",
    summary="Update Workstream Lifecycle Status",
    status_code=status.HTTP_200_OK,
    response_model=WorkstreamResponse,
)
async def update_workstream_status(
    deal_id: uuid.UUID,
    workstream_id: uuid.UUID,
    payload: WorkstreamStatusUpdateRequest,
    db: AsyncSession = Depends(get_db),
    context: TenantContext = Depends(validate_deal_membership),
) -> WorkstreamResponse:
    """Transition workstream lifecycle state (e.g. PLANNED -> IN_PROGRESS -> COMPLETED)."""
    context.require_permission(PERM_ANALYSIS_RUN)
    service = IntegrationService(db)
    return await service.update_workstream_status(context, deal_id, workstream_id, payload)


# ==========================================
# Milestone Endpoints
# ==========================================

@router.get(
    "/milestones",
    summary="List Integration Milestones",
    status_code=status.HTTP_200_OK,
    response_model=List[MilestoneResponse],
)
async def list_milestones(
    deal_id: uuid.UUID,
    workstream_id: Optional[uuid.UUID] = Query(None, description="Filter by workstream"),
    db: AsyncSession = Depends(get_db),
    context: TenantContext = Depends(validate_deal_membership),
) -> List[MilestoneResponse]:
    """List milestones across the 100-day program."""
    context.require_permission(PERM_DEALS_READ)
    service = IntegrationService(db)
    return await service.list_milestones(context, deal_id, workstream_id)


@router.post(
    "/milestones",
    summary="Create Integration Milestone",
    status_code=status.HTTP_201_CREATED,
    response_model=MilestoneResponse,
)
async def create_milestone(
    deal_id: uuid.UUID,
    payload: MilestoneCreateRequest,
    db: AsyncSession = Depends(get_db),
    context: TenantContext = Depends(validate_deal_membership),
) -> MilestoneResponse:
    """Add a target deliverable/milestone to a workstream."""
    context.require_permission(PERM_ANALYSIS_RUN)
    service = IntegrationService(db)
    return await service.create_milestone(context, deal_id, payload)


@router.patch(
    "/milestones/{milestone_id}/status",
    summary="Update Milestone Status & Completion",
    status_code=status.HTTP_200_OK,
    response_model=MilestoneResponse,
)
async def update_milestone_status(
    deal_id: uuid.UUID,
    milestone_id: uuid.UUID,
    payload: MilestoneStatusUpdateRequest,
    db: AsyncSession = Depends(get_db),
    context: TenantContext = Depends(validate_deal_membership),
) -> MilestoneResponse:
    """Update milestone completion percentage or transition status."""
    context.require_permission(PERM_ANALYSIS_RUN)
    service = IntegrationService(db)
    return await service.update_milestone_status(context, deal_id, milestone_id, payload)


# ==========================================
# Dependencies & DAG Endpoints
# ==========================================

@router.post(
    "/dependencies",
    summary="Add Milestone Dependency (DAG Validated)",
    status_code=status.HTTP_201_CREATED,
    response_model=DependencyResponse,
)
async def create_dependency(
    deal_id: uuid.UUID,
    payload: DependencyCreateRequest,
    db: AsyncSession = Depends(get_db),
    context: TenantContext = Depends(validate_deal_membership),
) -> DependencyResponse:
    """Link predecessor and successor milestones with deterministic cycle prevention."""
    context.require_permission(PERM_ANALYSIS_RUN)
    service = IntegrationService(db)
    return await service.create_dependency(context, deal_id, payload)


@router.delete(
    "/dependencies/{dependency_id}",
    summary="Delete Milestone Dependency",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_dependency(
    deal_id: uuid.UUID,
    dependency_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    context: TenantContext = Depends(validate_deal_membership),
) -> None:
    """Remove a dependency edge from the execution DAG."""
    context.require_permission(PERM_ANALYSIS_RUN)
    service = IntegrationService(db)
    await service.delete_dependency(context, deal_id, dependency_id)


# ==========================================
# Blockers Endpoints
# ==========================================

@router.get(
    "/blockers",
    summary="List Operational Blockers",
    status_code=status.HTTP_200_OK,
    response_model=List[BlockerResponse],
)
async def list_blockers(
    deal_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    context: TenantContext = Depends(validate_deal_membership),
) -> List[BlockerResponse]:
    """List open and resolved blockers."""
    context.require_permission(PERM_DEALS_READ)
    service = IntegrationService(db)
    return await service.list_blockers(context, deal_id)


@router.post(
    "/blockers",
    summary="Report Operational Blocker",
    status_code=status.HTTP_201_CREATED,
    response_model=BlockerResponse,
)
async def report_blocker(
    deal_id: uuid.UUID,
    payload: BlockerCreateRequest,
    db: AsyncSession = Depends(get_db),
    context: TenantContext = Depends(validate_deal_membership),
) -> BlockerResponse:
    """Report an operational or strategic blocker on a workstream or milestone."""
    context.require_permission(PERM_ANALYSIS_RUN)
    service = IntegrationService(db)
    return await service.create_blocker(context, deal_id, payload)


@router.patch(
    "/blockers/{blocker_id}/resolve",
    summary="Resolve Blocker",
    status_code=status.HTTP_200_OK,
    response_model=BlockerResponse,
)
async def resolve_blocker(
    deal_id: uuid.UUID,
    blocker_id: uuid.UUID,
    payload: BlockerResolveRequest,
    db: AsyncSession = Depends(get_db),
    context: TenantContext = Depends(validate_deal_membership),
) -> BlockerResponse:
    """Mark an operational blocker as resolved with documented commentary."""
    context.require_permission(PERM_ANALYSIS_RUN)
    service = IntegrationService(db)
    return await service.resolve_blocker(context, deal_id, blocker_id, payload)


# ==========================================
# Analytical & Timeline Views
# ==========================================

@router.get(
    "/timeline",
    summary="Get 100-Day Timeline Stage Breakdown",
    status_code=status.HTTP_200_OK,
    response_model=TimelineStageResponse,
)
async def get_timeline(
    deal_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    context: TenantContext = Depends(validate_deal_membership),
) -> TimelineStageResponse:
    """Retrieve 100-Day Timeline grouped into Day 0, Days 1-30, Days 31-60, Days 61-100."""
    context.require_permission(PERM_DEALS_READ)
    service = IntegrationService(db)
    return await service.get_timeline(context, deal_id)


@router.get(
    "/critical-path",
    summary="Get Deterministic Critical Path",
    status_code=status.HTTP_200_OK,
    response_model=CriticalPathResponse,
)
async def get_critical_path(
    deal_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    context: TenantContext = Depends(validate_deal_membership),
) -> CriticalPathResponse:
    """Compute the deterministic critical path of milestones through longest-path DAG analysis."""
    context.require_permission(PERM_DEALS_READ)
    service = IntegrationService(db)
    return await service.get_critical_path(context, deal_id)


@router.get(
    "/health",
    summary="Get Integration Health Score",
    status_code=status.HTTP_200_OK,
    response_model=IntegrationHealthResponse,
)
async def get_integration_health(
    deal_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    context: TenantContext = Depends(validate_deal_membership),
) -> IntegrationHealthResponse:
    """Compute deterministic Integration Health Score (0-100) and penalties breakdown."""
    context.require_permission(PERM_DEALS_READ)
    service = IntegrationService(db)
    return await service.get_health(context, deal_id)


@router.get(
    "/executive-attention",
    summary="Get Executive Attention Escalations",
    status_code=status.HTTP_200_OK,
    response_model=ExecutiveAttentionResponse,
)
async def get_executive_attention(
    deal_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    context: TenantContext = Depends(validate_deal_membership),
) -> ExecutiveAttentionResponse:
    """Retrieve prioritized queue of items requiring steering committee / executive intervention."""
    context.require_permission(PERM_DEALS_READ)
    service = IntegrationService(db)
    return await service.get_executive_attention(context, deal_id)
