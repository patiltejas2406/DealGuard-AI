"""REST API Endpoints for Post-Acquisition Intelligence, Value Creation & Business Growth."""

import uuid
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_tenant_context, validate_deal_membership
from app.core.database import get_db
from app.domains.agents.contract import AgentId
from app.domains.agents.service import AgentOrchestrationService
from app.domains.auth.permissions import PERM_ANALYSIS_RUN, PERM_DEALS_READ, PERM_DEALS_UPDATE
from app.domains.common.context import TenantContext
from app.domains.post_deal.schemas import (
    AcquisitionThesisCreate,
    AcquisitionThesisResponse,
    CustomerAccountCreate,
    CustomerAccountResponse,
    PostAcquisitionCustomersResponse,
    PostAcquisitionIntegrationResponse,
    PostAcquisitionMetricCreate,
    PostAcquisitionMetricResponse,
    PostAcquisitionOverviewResponse,
    PostAcquisitionPerformanceResponse,
    PostAcquisitionRisksResponse,
    PostAcquisitionSynergiesResponse,
    PostAcquisitionThesisResponse,
    ValueCreationInitiativeCreate,
    ValueCreationInitiativeResponse,
)
from app.domains.post_deal.service import PostDealService

router = APIRouter(tags=["post-acquisition"])


class PostAcquisitionAnalyzePayload(BaseModel):
    query: Optional[str] = Field(
        default=None,
        description="Strategic query or hypothesis to guide post-acquisition value creation analysis.",
    )
    target_agent_ids: Optional[List[str]] = Field(
        default=None,
        description="Optional list of post-deal specialist agent IDs to invoke.",
    )


# 1. Executive Post-Acquisition Overview
@router.get(
    "/deals/{deal_id}/post-acquisition/overview",
    summary="Get Post-Acquisition Executive Overview",
    status_code=status.HTTP_200_OK,
    response_model=PostAcquisitionOverviewResponse,
)
async def get_overview(
    deal_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    context: TenantContext = Depends(validate_deal_membership),
) -> PostAcquisitionOverviewResponse:
    """Retrieve executive value creation summary, health score, ARR, synergies, and thesis tracking."""
    context.require_permission(PERM_DEALS_READ)
    service = PostDealService(db)
    return await service.get_overview(context, deal_id)


# 2. Operating & Financial Performance
@router.get(
    "/deals/{deal_id}/post-acquisition/performance",
    summary="Get Post-Acquisition Operating Performance",
    status_code=status.HTTP_200_OK,
    response_model=PostAcquisitionPerformanceResponse,
)
async def get_performance(
    deal_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    context: TenantContext = Depends(validate_deal_membership),
) -> PostAcquisitionPerformanceResponse:
    """Retrieve post-close actual financial metrics, revenue growth, and EBITDA variances vs plan."""
    context.require_permission(PERM_DEALS_READ)
    service = PostDealService(db)
    return await service.get_performance(context, deal_id)


# 3. 100-Day Integration Execution Telemetry
@router.get(
    "/deals/{deal_id}/post-acquisition/integration",
    summary="Get Post-Acquisition Integration Telemetry",
    status_code=status.HTTP_200_OK,
    response_model=PostAcquisitionIntegrationResponse,
)
async def get_integration(
    deal_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    context: TenantContext = Depends(validate_deal_membership),
) -> PostAcquisitionIntegrationResponse:
    """Retrieve 100-day integration milestone completion rates, critical path items, and active blockers."""
    context.require_permission(PERM_DEALS_READ)
    service = PostDealService(db)
    return await service.get_integration(context, deal_id)


# 4. Synergy Realization Tracking
@router.get(
    "/deals/{deal_id}/post-acquisition/synergies",
    summary="Get Post-Acquisition Synergy Realization",
    status_code=status.HTTP_200_OK,
    response_model=PostAcquisitionSynergiesResponse,
)
async def get_synergies(
    deal_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    context: TenantContext = Depends(validate_deal_membership),
) -> PostAcquisitionSynergiesResponse:
    """Retrieve expected vs realized deal synergies and period-by-period realization logs."""
    context.require_permission(PERM_DEALS_READ)
    service = PostDealService(db)
    return await service.get_synergies(context, deal_id)


# 5. Customer Intelligence & Churn Risk
@router.get(
    "/deals/{deal_id}/post-acquisition/customers",
    summary="Get Post-Acquisition Customer Intelligence",
    status_code=status.HTTP_200_OK,
    response_model=PostAcquisitionCustomersResponse,
)
async def get_customers(
    deal_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    context: TenantContext = Depends(validate_deal_membership),
) -> PostAcquisitionCustomersResponse:
    """Retrieve customer concentration, NRR retention cohorts, and account-level churn risks."""
    context.require_permission(PERM_DEALS_READ)
    service = PostDealService(db)
    return await service.get_customers(context, deal_id)


# 6. Emerging Post-Close Risks
@router.get(
    "/deals/{deal_id}/post-acquisition/risks",
    summary="Get Emerging Post-Acquisition Risks",
    status_code=status.HTTP_200_OK,
    response_model=PostAcquisitionRisksResponse,
)
async def get_risks(
    deal_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    context: TenantContext = Depends(validate_deal_membership),
) -> PostAcquisitionRisksResponse:
    """Retrieve emerging post-close operational, compliance, SLA, and customer risks."""
    context.require_permission(PERM_DEALS_READ)
    service = PostDealService(db)
    return await service.get_risks(context, deal_id)


# 7. Acquisition Thesis Scorecard
@router.get(
    "/deals/{deal_id}/post-acquisition/thesis",
    summary="Get Acquisition Thesis Scorecard",
    status_code=status.HTTP_200_OK,
    response_model=PostAcquisitionThesisResponse,
)
async def get_theses(
    deal_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    context: TenantContext = Depends(validate_deal_membership),
) -> PostAcquisitionThesisResponse:
    """Retrieve pre-deal expectations vs post-close actual results and strategic initiatives."""
    context.require_permission(PERM_DEALS_READ)
    service = PostDealService(db)
    return await service.get_theses(context, deal_id)


# 8. Data Ingestion Endpoints (Customer, Metric, Thesis, Initiative)
@router.post(
    "/deals/{deal_id}/post-acquisition/customers",
    summary="Create Customer Account Record",
    status_code=status.HTTP_201_CREATED,
    response_model=CustomerAccountResponse,
)
async def create_customer_account(
    deal_id: uuid.UUID,
    payload: CustomerAccountCreate,
    db: AsyncSession = Depends(get_db),
    context: TenantContext = Depends(validate_deal_membership),
) -> CustomerAccountResponse:
    """Create a new customer account record in the post-acquisition workspace."""
    context.require_permission(PERM_DEALS_UPDATE)
    service = PostDealService(db)
    account = await service.repo.create_customer_account(context.organization_id, deal_id, payload)
    await db.commit()
    return CustomerAccountResponse.model_validate(account)


@router.post(
    "/deals/{deal_id}/post-acquisition/metrics",
    summary="Log Post-Acquisition Metric",
    status_code=status.HTTP_201_CREATED,
    response_model=PostAcquisitionMetricResponse,
)
async def create_post_acquisition_metric(
    deal_id: uuid.UUID,
    payload: PostAcquisitionMetricCreate,
    db: AsyncSession = Depends(get_db),
    context: TenantContext = Depends(validate_deal_membership),
) -> PostAcquisitionMetricResponse:
    """Log a post-close financial or operational performance metric."""
    context.require_permission(PERM_DEALS_UPDATE)
    service = PostDealService(db)
    metric = await service.repo.create_post_acquisition_metric(context.organization_id, deal_id, payload)
    await db.commit()
    return PostAcquisitionMetricResponse.model_validate(metric)


@router.post(
    "/deals/{deal_id}/post-acquisition/thesis",
    summary="Add Acquisition Thesis Pillar",
    status_code=status.HTTP_201_CREATED,
    response_model=AcquisitionThesisResponse,
)
async def create_acquisition_thesis(
    deal_id: uuid.UUID,
    payload: AcquisitionThesisCreate,
    db: AsyncSession = Depends(get_db),
    context: TenantContext = Depends(validate_deal_membership),
) -> AcquisitionThesisResponse:
    """Register an acquisition thesis target and tracking status."""
    context.require_permission(PERM_DEALS_UPDATE)
    service = PostDealService(db)
    thesis = await service.repo.create_acquisition_thesis(context.organization_id, deal_id, payload)
    await db.commit()
    return AcquisitionThesisResponse.model_validate(thesis)


@router.post(
    "/deals/{deal_id}/post-acquisition/initiatives",
    summary="Create Value Creation Initiative",
    status_code=status.HTTP_201_CREATED,
    response_model=ValueCreationInitiativeResponse,
)
async def create_value_creation_initiative(
    deal_id: uuid.UUID,
    payload: ValueCreationInitiativeCreate,
    db: AsyncSession = Depends(get_db),
    context: TenantContext = Depends(validate_deal_membership),
) -> ValueCreationInitiativeResponse:
    """Create a post-acquisition strategic value creation initiative."""
    context.require_permission(PERM_DEALS_UPDATE)
    service = PostDealService(db)
    initiative = await service.repo.create_value_creation_initiative(context.organization_id, deal_id, payload)
    await db.commit()
    return ValueCreationInitiativeResponse.model_validate(initiative)


# 9. Multi-Agent Post-Acquisition Orchestrated Analysis
@router.post(
    "/deals/{deal_id}/post-acquisition/analyze",
    summary="Run Post-Acquisition Multi-Agent Value Creation Analysis",
    status_code=status.HTTP_200_OK,
)
async def analyze_post_acquisition(
    deal_id: uuid.UUID,
    payload: PostAcquisitionAnalyzePayload,
    db: AsyncSession = Depends(get_db),
    context: TenantContext = Depends(validate_deal_membership),
) -> Dict[str, Any]:
    """Execute post-acquisition multi-agent orchestration across value creation specialists."""
    context.require_permission(PERM_ANALYSIS_RUN)
    agent_service = AgentOrchestrationService(db)
    target_agents = payload.target_agent_ids
    if not target_agents:
        target_agents = [
            AgentId.STRATEGY.value,
            AgentId.MONITORING.value,
            AgentId.CUSTOMER.value,
            AgentId.GROWTH.value,
            AgentId.REVENUE.value,
            AgentId.COST_OPT.value,
            AgentId.OPERATIONS.value,
            AgentId.FP_AND_A.value,
            AgentId.INTEGRATION.value,
            AgentId.SYNERGY.value,
        ]

    result = await agent_service.run_orchestrated_diligence(
        context=context,
        deal_id=deal_id,
        orchestration_mode="POST_ACQUISITION_VALUE_CREATION",
        query=payload.query,
        target_agent_ids=target_agents,
    )
    return result.to_dict()
