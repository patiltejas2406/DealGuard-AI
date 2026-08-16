"""Financial Statements, Metrics, CAGR & Quality of Earnings (QoE) REST Endpoints."""

import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import require_permission, validate_deal_membership
from app.api.v1.schemas.financials import (
    CagrAnalysisResponse,
    FinancialMetricResponse,
    FinancialStatementCreateRequest,
    FinancialStatementResponse,
    FinancialValidationResponse,
    QoEAdjustmentCreateRequest,
    QoEAdjustmentResponse,
    QoEAdjustmentUpdateRequest,
    QoEBridgeResponse,
)
from app.core.database import get_db
from app.domains.auth.permissions import (
    PERM_FINANCIALS_READ,
    PERM_FINANCIALS_WRITE,
)
from app.domains.common.context import TenantContext
from app.domains.financials.service import FinancialService

router = APIRouter(prefix="/deals/{deal_id}/financials", tags=["Financial Statements & QoE Engine"])


# -------------------------------------------------------------
# 1. Financial Statements
# -------------------------------------------------------------
@router.get(
    "/statements",
    summary="List 3-Statements for Deal",
    status_code=status.HTTP_200_OK,
    response_model=List[FinancialStatementResponse],
)
async def list_deal_statements(
    deal_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    context: TenantContext = Depends(validate_deal_membership),
) -> List[FinancialStatementResponse]:
    context.require_permission(PERM_FINANCIALS_READ)
    service = FinancialService(db)
    stmts = await service.list_statements(context, deal_id)
    return [FinancialStatementResponse.model_validate(s) for s in stmts]


@router.post(
    "/statements",
    summary="Upsert and Derive Financial Statement",
    status_code=status.HTTP_201_CREATED,
    response_model=FinancialStatementResponse,
)
async def upsert_deal_statement(
    deal_id: uuid.UUID,
    payload: FinancialStatementCreateRequest,
    db: AsyncSession = Depends(get_db),
    context: TenantContext = Depends(validate_deal_membership),
) -> FinancialStatementResponse:
    context.require_permission(PERM_FINANCIALS_WRITE)
    service = FinancialService(db)
    stmt = await service.upsert_statement(
        context=context,
        deal_id=deal_id,
        statement_type=payload.statement_type,
        fiscal_year=payload.fiscal_year,
        fiscal_period=payload.fiscal_period,
        line_items=payload.line_items,
        source_currency=payload.source_currency,
        period_type=payload.period_type,
        is_audited=payload.is_audited,
        is_normalized=payload.is_normalized,
        source_document_id=payload.source_document_id,
    )
    return FinancialStatementResponse.model_validate(stmt)


# -------------------------------------------------------------
# 2. Financial Metrics & Multi-Year CAGR
# -------------------------------------------------------------
@router.get(
    "/metrics",
    summary="List Derived Metrics & Ratios",
    status_code=status.HTTP_200_OK,
    response_model=List[FinancialMetricResponse],
)
async def list_deal_metrics(
    deal_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    context: TenantContext = Depends(validate_deal_membership),
) -> List[FinancialMetricResponse]:
    context.require_permission(PERM_FINANCIALS_READ)
    service = FinancialService(db)
    metrics = await service.list_metrics(context, deal_id)
    return [FinancialMetricResponse.model_validate(m) for m in metrics]


@router.get(
    "/cagr",
    summary="Compute Multi-Year Revenue & EBITDA CAGR",
    status_code=status.HTTP_200_OK,
    response_model=CagrAnalysisResponse,
)
async def get_deal_cagr_analysis(
    deal_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    context: TenantContext = Depends(validate_deal_membership),
) -> CagrAnalysisResponse:
    context.require_permission(PERM_FINANCIALS_READ)
    service = FinancialService(db)
    res = await service.compute_cagr_analysis(context, deal_id)
    return CagrAnalysisResponse(**res)


# -------------------------------------------------------------
# 3. Quality of Earnings (QoE) Adjustments & Bridge
# -------------------------------------------------------------
@router.get(
    "/qoe",
    summary="Get Quality of Earnings Bridge and Adjustments",
    status_code=status.HTTP_200_OK,
    response_model=QoEBridgeResponse,
)
async def get_deal_qoe_bridge(
    deal_id: uuid.UUID,
    period: str = Query("FY2023", description="Target fiscal period for normalization bridge"),
    db: AsyncSession = Depends(get_db),
    context: TenantContext = Depends(validate_deal_membership),
) -> QoEBridgeResponse:
    context.require_permission(PERM_FINANCIALS_READ)
    service = FinancialService(db)
    bridge_data = await service.get_qoe_bridge(context, deal_id, period)
    return QoEBridgeResponse(**bridge_data)


@router.post(
    "/qoe",
    summary="Create Quality of Earnings Adjustment (Add-Back/Deduction)",
    status_code=status.HTTP_201_CREATED,
    response_model=QoEAdjustmentResponse,
)
async def create_qoe_adjustment(
    deal_id: uuid.UUID,
    payload: QoEAdjustmentCreateRequest,
    db: AsyncSession = Depends(get_db),
    context: TenantContext = Depends(validate_deal_membership),
) -> QoEAdjustmentResponse:
    context.require_permission(PERM_FINANCIALS_WRITE)
    service = FinancialService(db)
    adj = await service.create_qoe_adjustment(
        context=context,
        deal_id=deal_id,
        category=payload.category,
        description=payload.description,
        amount=payload.amount,
        currency=payload.currency,
        period=payload.period,
        treatment=payload.treatment,
        status=payload.status,
        notes=payload.notes,
        citation_id=payload.citation_id,
    )
    return QoEAdjustmentResponse.model_validate(adj)


@router.patch(
    "/qoe/{adjustment_id}",
    summary="Update or Approve/Reject QoE Adjustment",
    status_code=status.HTTP_200_OK,
    response_model=QoEAdjustmentResponse,
)
async def update_qoe_adjustment(
    deal_id: uuid.UUID,
    adjustment_id: uuid.UUID,
    payload: QoEAdjustmentUpdateRequest,
    db: AsyncSession = Depends(get_db),
    context: TenantContext = Depends(validate_deal_membership),
) -> QoEAdjustmentResponse:
    context.require_permission(PERM_FINANCIALS_WRITE)
    service = FinancialService(db)
    adj = await service.update_qoe_adjustment(
        context=context,
        deal_id=deal_id,
        adjustment_id=adjustment_id,
        **payload.model_dump(exclude_unset=True),
    )
    return QoEAdjustmentResponse.model_validate(adj)


@router.delete(
    "/qoe/{adjustment_id}",
    summary="Delete QoE Adjustment",
    status_code=status.HTTP_200_OK,
)
async def delete_qoe_adjustment(
    deal_id: uuid.UUID,
    adjustment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    context: TenantContext = Depends(validate_deal_membership),
) -> dict:
    context.require_permission(PERM_FINANCIALS_WRITE)
    service = FinancialService(db)
    await service.delete_qoe_adjustment(context, deal_id, adjustment_id)
    return {"success": True, "message": "Adjustment removed successfully."}


# -------------------------------------------------------------
# 4. Model Accounting Validation Checks
# -------------------------------------------------------------
@router.get(
    "/validation",
    summary="Validate 3-Statement Balancing and Consistency",
    status_code=status.HTTP_200_OK,
    response_model=FinancialValidationResponse,
)
async def get_financial_validation_report(
    deal_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    context: TenantContext = Depends(validate_deal_membership),
) -> FinancialValidationResponse:
    context.require_permission(PERM_FINANCIALS_READ)
    service = FinancialService(db)
    report = await service.validate_deal_financials(context, deal_id)
    return FinancialValidationResponse(**report)
