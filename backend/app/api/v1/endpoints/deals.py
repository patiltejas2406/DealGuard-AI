"""Deal Workspace, Diligence Data Room, Risk & Financials Endpoints with RBAC."""

import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import (
    get_tenant_context,
    require_permission,
    validate_deal_membership,
)
from app.api.v1.schemas.common import (
    DealCreateRequest,
    DealResponse,
    DocumentResponse,
    FinancialMetricResponse,
    FinancialStatementResponse,
    RiskResponse,
)
from app.core.database import get_db
from app.domains.auth.permissions import (
    PERM_DEALS_CREATE,
    PERM_DEALS_READ,
    PERM_DOCS_READ,
    PERM_FINANCIALS_READ,
    PERM_RISKS_READ,
)
from app.domains.common.context import TenantContext
from app.domains.deals.service import DealService
from app.domains.documents.service import DocumentService
from app.domains.financials.service import FinancialService
from app.domains.risk.service import RiskService

router = APIRouter(prefix="/deals", tags=["Deals & Diligence Workspace"])


@router.get(
    "",
    summary="List Deals for Authenticated Organization",
    status_code=status.HTTP_200_OK,
    response_model=List[DealResponse],
)
async def list_deals(
    stage: Optional[str] = Query(None, description="Filter by deal stage"),
    deal_status: Optional[str] = Query(None, alias="status", description="Filter by status"),
    db: AsyncSession = Depends(get_db),
    context: TenantContext = Depends(require_permission(PERM_DEALS_READ)),
) -> List[DealResponse]:
    service = DealService(db)
    deals = await service.list_deals(context, stage=stage, status=deal_status)
    return [DealResponse.model_validate(d) for d in deals]


@router.post(
    "",
    summary="Create New Deal Workspace and Target Company",
    status_code=status.HTTP_201_CREATED,
    response_model=DealResponse,
)
async def create_deal(
    payload: DealCreateRequest,
    db: AsyncSession = Depends(get_db),
    context: TenantContext = Depends(require_permission(PERM_DEALS_CREATE)),
) -> DealResponse:
    service = DealService(db)
    deal = await service.create_deal_with_target(
        context=context,
        company_name=payload.company_name,
        company_industry=payload.company_industry,
        deal_title=payload.deal_title,
        code_name=payload.code_name,
        deal_type=payload.deal_type,
        stage=payload.stage,
        target_ev=payload.target_ev,
        currency=payload.currency,
    )
    return DealResponse.model_validate(deal)


@router.get(
    "/{deal_id}",
    summary="Get Deal Workspace Details",
    status_code=status.HTTP_200_OK,
    response_model=DealResponse,
)
async def get_deal(
    deal_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    context: TenantContext = Depends(validate_deal_membership),
) -> DealResponse:
    service = DealService(db)
    deal = await service.get_deal(context, deal_id)
    return DealResponse.model_validate(deal)


@router.get(
    "/{deal_id}/documents",
    summary="List Diligence Documents for Deal",
    status_code=status.HTTP_200_OK,
    response_model=List[DocumentResponse],
)
async def list_deal_documents(
    deal_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    context: TenantContext = Depends(validate_deal_membership),
) -> List[DocumentResponse]:
    context.require_permission(PERM_DOCS_READ)
    service = DocumentService(db)
    docs = await service.list_documents(context, deal_id)
    return [DocumentResponse.model_validate(doc) for doc in docs]


@router.get(
    "/{deal_id}/financials",
    summary="Get 3-Statement Financials and Metrics for Deal",
    status_code=status.HTTP_200_OK,
    response_model=List[FinancialStatementResponse],
)
async def list_deal_financials(
    deal_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    context: TenantContext = Depends(validate_deal_membership),
) -> List[FinancialStatementResponse]:
    context.require_permission(PERM_FINANCIALS_READ)
    service = FinancialService(db)
    stmts = await service.list_statements(context, deal_id)
    return [FinancialStatementResponse.model_validate(s) for s in stmts]
