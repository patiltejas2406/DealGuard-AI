"""REST API Endpoints for Technology, Operational & Product Diligence Intelligence Engine."""

import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import validate_deal_membership
from app.core.database import get_db
from app.domains.auth.permissions import PERM_ANALYSIS_RUN, PERM_DEALS_READ
from app.domains.common.context import TenantContext
from app.domains.technology.schemas import (
    OperationalMetricResponse,
    TechnologyDependencyResponse,
    TechnologyFindingCreateRequest,
    TechnologyFindingResponse,
    TechnologyFindingStatusUpdateRequest,
    TechnologyScanResponse,
    TechnologySummaryResponse,
)
from app.domains.technology.service import TechnologyService

router = APIRouter(prefix="/deals/{deal_id}/technology", tags=["technology"])


@router.get(
    "",
    summary="Get Executive Technology Diligence Summary",
    status_code=status.HTTP_200_OK,
    response_model=TechnologySummaryResponse,
)
async def get_technology_overview(
    deal_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    context: TenantContext = Depends(validate_deal_membership),
) -> TechnologySummaryResponse:
    """Retrieve executive technology risk score, cloud run rate, uptime SLAs, and SPOF summary."""
    context.require_permission(PERM_DEALS_READ)
    service = TechnologyService(db)
    return await service.get_technology_summary(context, deal_id)


@router.post(
    "/scan",
    summary="Scan Ingested Documents for Technology & Operational Risks",
    status_code=status.HTTP_200_OK,
    response_model=TechnologyScanResponse,
)
async def scan_technology_documents(
    deal_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    context: TenantContext = Depends(validate_deal_membership),
) -> TechnologyScanResponse:
    """Trigger deterministic RAG-grounded technology debt, cloud spend, and operational metrics scan."""
    context.require_permission(PERM_ANALYSIS_RUN)
    service = TechnologyService(db)
    return await service.scan_deal_documents(context, deal_id)


@router.get(
    "/findings",
    summary="List Technology & Architectural Findings",
    status_code=status.HTTP_200_OK,
    response_model=List[TechnologyFindingResponse],
)
async def list_findings(
    deal_id: uuid.UUID,
    category: Optional[str] = Query(None, description="Filter by 30-category taxonomy"),
    severity: Optional[str] = Query(None, description="Filter by severity (CRITICAL, HIGH, etc.)"),
    db: AsyncSession = Depends(get_db),
    context: TenantContext = Depends(validate_deal_membership),
) -> List[TechnologyFindingResponse]:
    """List actionable technical findings with business impacts and remediation plans."""
    context.require_permission(PERM_DEALS_READ)
    service = TechnologyService(db)
    return await service.list_findings(context, deal_id, category, severity)


@router.post(
    "/findings",
    summary="Create Technology Finding",
    status_code=status.HTTP_201_CREATED,
    response_model=TechnologyFindingResponse,
)
async def create_finding(
    deal_id: uuid.UUID,
    payload: TechnologyFindingCreateRequest,
    db: AsyncSession = Depends(get_db),
    context: TenantContext = Depends(validate_deal_membership),
) -> TechnologyFindingResponse:
    """Manually register an engineering or architectural finding."""
    context.require_permission(PERM_ANALYSIS_RUN)
    service = TechnologyService(db)
    return await service.create_finding(context, deal_id, payload)


@router.patch(
    "/findings/{finding_id}/status",
    summary="Update Technology Finding Status",
    status_code=status.HTTP_200_OK,
    response_model=TechnologyFindingResponse,
)
async def update_finding_status(
    deal_id: uuid.UUID,
    finding_id: uuid.UUID,
    payload: TechnologyFindingStatusUpdateRequest,
    db: AsyncSession = Depends(get_db),
    context: TenantContext = Depends(validate_deal_membership),
) -> TechnologyFindingResponse:
    """Transition finding lifecycle state (e.g. IDENTIFIED -> REMEDIATION_PLANNED -> MITIGATED)."""
    context.require_permission(PERM_ANALYSIS_RUN)
    service = TechnologyService(db)
    return await service.update_finding_status(context, deal_id, finding_id, payload)


@router.get(
    "/infrastructure",
    summary="Get Infrastructure & Cloud Cost Metrics",
    status_code=status.HTTP_200_OK,
    response_model=List[OperationalMetricResponse],
)
async def list_infrastructure_metrics(
    deal_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    context: TenantContext = Depends(validate_deal_membership),
) -> List[OperationalMetricResponse]:
    """List cloud compute and infrastructure spend metrics."""
    context.require_permission(PERM_DEALS_READ)
    service = TechnologyService(db)
    return await service.list_metrics(context, deal_id, metric_category="CLOUD_SPEND")


@router.get(
    "/dependencies",
    summary="List External Technical Dependencies & SPOFs",
    status_code=status.HTTP_200_OK,
    response_model=List[TechnologyDependencyResponse],
)
async def list_dependencies(
    deal_id: uuid.UUID,
    criticality: Optional[str] = Query(None, description="Filter by criticality"),
    db: AsyncSession = Depends(get_db),
    context: TenantContext = Depends(validate_deal_membership),
) -> List[TechnologyDependencyResponse]:
    """List external cloud APIs, SaaS dependencies, and single points of failure."""
    context.require_permission(PERM_DEALS_READ)
    service = TechnologyService(db)
    return await service.list_dependencies(context, deal_id, criticality)


@router.get(
    "/reliability",
    summary="List Uptime & Reliability SLAs",
    status_code=status.HTTP_200_OK,
    response_model=List[OperationalMetricResponse],
)
async def list_reliability_metrics(
    deal_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    context: TenantContext = Depends(validate_deal_membership),
) -> List[OperationalMetricResponse]:
    """List SLA adherence, incident MTTR, and backup recovery objectives."""
    context.require_permission(PERM_DEALS_READ)
    service = TechnologyService(db)
    return await service.list_metrics(context, deal_id, metric_category="UPTIME_SLA")


@router.get(
    "/summary",
    summary="Get Detailed Technology Summary Metrics",
    status_code=status.HTTP_200_OK,
    response_model=TechnologySummaryResponse,
)
async def get_summary(
    deal_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    context: TenantContext = Depends(validate_deal_membership),
) -> TechnologySummaryResponse:
    """Retrieve complete technology diligence scorecard."""
    context.require_permission(PERM_DEALS_READ)
    service = TechnologyService(db)
    return await service.get_technology_summary(context, deal_id)
