"""Valuation Intelligence REST Endpoints: DCF, WACC, Comparables, Precedents & Summary."""

import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import validate_deal_membership
from app.api.v1.schemas.valuation import (
    ComparableAnalysisResponse,
    ComparableCompanyCreateRequest,
    ComparableCompanyResponse,
    ComparableCompanyUpdateRequest,
    DcfCalculateRequest,
    DcfResponse,
    PrecedentAnalysisResponse,
    PrecedentTransactionCreateRequest,
    PrecedentTransactionResponse,
    PrecedentTransactionUpdateRequest,
    SensitivityMatrixResponse,
    ValuationAssumptionCreateRequest,
    ValuationAssumptionResponse,
    ValuationResponse,
    ValuationSummaryResponse,
    ValuationUpdateRequest,
    ValuationValidationResponse,
    WaccCalculateRequest,
    WaccResponse,
)
from app.core.database import get_db
from app.domains.auth.permissions import (
    PERM_VALUATION_READ,
    PERM_VALUATION_WRITE,
)
from app.domains.common.context import TenantContext
from app.domains.valuation.engine.wacc import WACCEngine
from app.domains.valuation.service import ValuationService

router = APIRouter(prefix="/deals/{deal_id}/valuation", tags=["Valuation Intelligence Engine"])


# -------------------------------------------------------------
# 1. Valuation Project
# -------------------------------------------------------------
@router.get(
    "",
    summary="Get or Initialize Valuation Project",
    status_code=status.HTTP_200_OK,
    response_model=ValuationResponse,
)
async def get_valuation(
    deal_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    context: TenantContext = Depends(validate_deal_membership),
) -> ValuationResponse:
    context.require_permission(PERM_VALUATION_READ)
    service = ValuationService(db)
    val = await service.get_or_create_valuation(context, deal_id)
    return ValuationResponse.model_validate(val)


@router.patch(
    "/{valuation_id}",
    summary="Update Valuation Project Parameters",
    status_code=status.HTTP_200_OK,
    response_model=ValuationResponse,
)
async def update_valuation(
    deal_id: uuid.UUID,
    valuation_id: uuid.UUID,
    payload: ValuationUpdateRequest,
    db: AsyncSession = Depends(get_db),
    context: TenantContext = Depends(validate_deal_membership),
) -> ValuationResponse:
    context.require_permission(PERM_VALUATION_WRITE)
    service = ValuationService(db)
    val = await service.update_valuation(
        context, deal_id, valuation_id, **payload.model_dump(exclude_unset=True)
    )
    return ValuationResponse.model_validate(val)


# -------------------------------------------------------------
# 2. WACC & Assumptions
# -------------------------------------------------------------
@router.get(
    "/wacc",
    summary="Get WACC Analysis for Deal",
    status_code=status.HTTP_200_OK,
    response_model=WaccResponse,
)
async def get_wacc_analysis(
    deal_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    context: TenantContext = Depends(validate_deal_membership),
) -> WaccResponse:
    context.require_permission(PERM_VALUATION_READ)
    service = ValuationService(db)
    wacc_data = await service.get_wacc_analysis(context, deal_id)
    return WaccResponse(**wacc_data)


@router.post(
    "/wacc/calculate",
    summary="On-Demand WACC Calculation",
    status_code=status.HTTP_200_OK,
    response_model=WaccResponse,
)
async def calculate_wacc_on_demand(
    deal_id: uuid.UUID,
    payload: WaccCalculateRequest,
    context: TenantContext = Depends(validate_deal_membership),
) -> WaccResponse:
    context.require_permission(PERM_VALUATION_READ)
    wacc_data = WACCEngine.calculate_wacc(
        risk_free_rate=payload.risk_free_rate,
        beta=payload.beta,
        equity_risk_premium=payload.equity_risk_premium,
        pre_tax_cost_of_debt=payload.pre_tax_cost_of_debt,
        tax_rate=payload.tax_rate,
        equity_weight=payload.equity_weight,
        debt_weight=payload.debt_weight,
    )
    return WaccResponse(**wacc_data)


@router.get(
    "/assumptions",
    summary="List Valuation Assumptions with Provenance",
    status_code=status.HTTP_200_OK,
    response_model=List[ValuationAssumptionResponse],
)
async def list_assumptions(
    deal_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    context: TenantContext = Depends(validate_deal_membership),
) -> List[ValuationAssumptionResponse]:
    context.require_permission(PERM_VALUATION_READ)
    service = ValuationService(db)
    assumptions = await service.list_assumptions(context, deal_id)
    return [ValuationAssumptionResponse.model_validate(a) for a in assumptions]


@router.post(
    "/assumptions",
    summary="Create or Update Valuation Assumption",
    status_code=status.HTTP_201_CREATED,
    response_model=ValuationAssumptionResponse,
)
async def upsert_assumption(
    deal_id: uuid.UUID,
    payload: ValuationAssumptionCreateRequest,
    db: AsyncSession = Depends(get_db),
    context: TenantContext = Depends(validate_deal_membership),
) -> ValuationAssumptionResponse:
    context.require_permission(PERM_VALUATION_WRITE)
    service = ValuationService(db)
    ass = await service.upsert_assumption(
        context=context,
        deal_id=deal_id,
        name=payload.name,
        value=payload.value,
        unit=payload.unit,
        category=payload.category,
        period=payload.period,
        source_type=payload.source_type,
        is_analyst_entered=payload.is_analyst_entered,
        confidence_score=payload.confidence_score,
        citation_id=payload.citation_id,
        notes=payload.notes,
        valuation_id=payload.valuation_id,
    )
    return ValuationAssumptionResponse.model_validate(ass)


# -------------------------------------------------------------
# 3. DCF
# -------------------------------------------------------------
@router.get(
    "/dcf",
    summary="Get DCF Model Schedule & Valuation",
    status_code=status.HTTP_200_OK,
    response_model=DcfResponse,
)
async def get_dcf_valuation(
    deal_id: uuid.UUID,
    terminal_method: str = Query("PERPETUITY_GROWTH", description="PERPETUITY_GROWTH or EXIT_MULTIPLE"),
    db: AsyncSession = Depends(get_db),
    context: TenantContext = Depends(validate_deal_membership),
) -> DcfResponse:
    context.require_permission(PERM_VALUATION_READ)
    service = ValuationService(db)
    res = await service.compute_dcf_valuation(context, deal_id, terminal_method=terminal_method)
    return DcfResponse(**res)


@router.post(
    "/dcf/calculate",
    summary="On-Demand DCF Calculation",
    status_code=status.HTTP_200_OK,
    response_model=DcfResponse,
)
async def calculate_dcf_on_demand(
    deal_id: uuid.UUID,
    payload: DcfCalculateRequest,
    db: AsyncSession = Depends(get_db),
    context: TenantContext = Depends(validate_deal_membership),
) -> DcfResponse:
    context.require_permission(PERM_VALUATION_READ)
    service = ValuationService(db)
    res = await service.compute_dcf_valuation(
        context=context,
        deal_id=deal_id,
        projections=payload.projections,
        wacc=payload.wacc,
        terminal_growth_rate=payload.terminal_growth_rate,
        exit_multiple=payload.exit_multiple,
        terminal_method=payload.terminal_method,
    )
    return DcfResponse(**res)


# -------------------------------------------------------------
# 4. Trading Comparables (CCA)
# -------------------------------------------------------------
@router.get(
    "/comparables",
    summary="Get Trading Comparables Analysis & Peers",
    status_code=status.HTTP_200_OK,
    response_model=ComparableAnalysisResponse,
)
async def get_comparable_analysis(
    deal_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    context: TenantContext = Depends(validate_deal_membership),
) -> ComparableAnalysisResponse:
    context.require_permission(PERM_VALUATION_READ)
    service = ValuationService(db)
    res = await service.get_comparable_analysis(context, deal_id)
    return ComparableAnalysisResponse(**res)


@router.post(
    "/comparables",
    summary="Add Comparable Peer Company",
    status_code=status.HTTP_201_CREATED,
    response_model=ComparableCompanyResponse,
)
async def create_comparable_company(
    deal_id: uuid.UUID,
    payload: ComparableCompanyCreateRequest,
    db: AsyncSession = Depends(get_db),
    context: TenantContext = Depends(validate_deal_membership),
) -> ComparableCompanyResponse:
    context.require_permission(PERM_VALUATION_WRITE)
    service = ValuationService(db)
    comp = await service.create_comparable(
        context=context,
        deal_id=deal_id,
        company_name=payload.company_name,
        ticker=payload.ticker,
        industry=payload.industry,
        geography=payload.geography,
        revenue=payload.revenue,
        ebitda=payload.ebitda,
        ebit=payload.ebit,
        net_income=payload.net_income,
        enterprise_value=payload.enterprise_value,
        equity_value=payload.equity_value,
        revenue_growth=payload.revenue_growth,
        status=payload.status,
        source=payload.source,
        notes=payload.notes,
        citation_id=payload.citation_id,
        valuation_id=payload.valuation_id,
    )
    return ComparableCompanyResponse.model_validate(comp)


@router.patch(
    "/comparables/{comp_id}",
    summary="Update Comparable Peer Company",
    status_code=status.HTTP_200_OK,
    response_model=ComparableCompanyResponse,
)
async def update_comparable_company(
    deal_id: uuid.UUID,
    comp_id: uuid.UUID,
    payload: ComparableCompanyUpdateRequest,
    db: AsyncSession = Depends(get_db),
    context: TenantContext = Depends(validate_deal_membership),
) -> ComparableCompanyResponse:
    context.require_permission(PERM_VALUATION_WRITE)
    service = ValuationService(db)
    comp = await service.update_comparable(
        context, deal_id, comp_id, **payload.model_dump(exclude_unset=True)
    )
    return ComparableCompanyResponse.model_validate(comp)


@router.delete(
    "/comparables/{comp_id}",
    summary="Delete Comparable Peer Company",
    status_code=status.HTTP_200_OK,
)
async def delete_comparable_company(
    deal_id: uuid.UUID,
    comp_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    context: TenantContext = Depends(validate_deal_membership),
) -> dict:
    context.require_permission(PERM_VALUATION_WRITE)
    service = ValuationService(db)
    await service.delete_comparable(context, deal_id, comp_id)
    return {"success": True, "message": "Comparable peer removed successfully."}


# -------------------------------------------------------------
# 5. Precedent Transactions (PTA)
# -------------------------------------------------------------
@router.get(
    "/precedents",
    summary="Get Precedent Transactions Analysis & Deals",
    status_code=status.HTTP_200_OK,
    response_model=PrecedentAnalysisResponse,
)
async def get_precedent_analysis(
    deal_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    context: TenantContext = Depends(validate_deal_membership),
) -> PrecedentAnalysisResponse:
    context.require_permission(PERM_VALUATION_READ)
    service = ValuationService(db)
    res = await service.get_precedent_analysis(context, deal_id)
    return PrecedentAnalysisResponse(**res)


@router.post(
    "/precedents",
    summary="Add Precedent M&A Transaction",
    status_code=status.HTTP_201_CREATED,
    response_model=PrecedentTransactionResponse,
)
async def create_precedent_transaction(
    deal_id: uuid.UUID,
    payload: PrecedentTransactionCreateRequest,
    db: AsyncSession = Depends(get_db),
    context: TenantContext = Depends(validate_deal_membership),
) -> PrecedentTransactionResponse:
    context.require_permission(PERM_VALUATION_WRITE)
    service = ValuationService(db)
    tx = await service.create_precedent(
        context=context,
        deal_id=deal_id,
        target_name=payload.target_name,
        acquirer_name=payload.acquirer_name,
        announcement_date=payload.announcement_date,
        transaction_value=payload.transaction_value,
        enterprise_value=payload.enterprise_value,
        revenue=payload.revenue,
        ebitda=payload.ebitda,
        transaction_type=payload.transaction_type,
        industry=payload.industry,
        geography=payload.geography,
        status=payload.status,
        source=payload.source,
        notes=payload.notes,
        citation_id=payload.citation_id,
        valuation_id=payload.valuation_id,
    )
    return PrecedentTransactionResponse.model_validate(tx)


@router.patch(
    "/precedents/{tx_id}",
    summary="Update Precedent M&A Transaction",
    status_code=status.HTTP_200_OK,
    response_model=PrecedentTransactionResponse,
)
async def update_precedent_transaction(
    deal_id: uuid.UUID,
    tx_id: uuid.UUID,
    payload: PrecedentTransactionUpdateRequest,
    db: AsyncSession = Depends(get_db),
    context: TenantContext = Depends(validate_deal_membership),
) -> PrecedentTransactionResponse:
    context.require_permission(PERM_VALUATION_WRITE)
    service = ValuationService(db)
    tx = await service.update_precedent(
        context, deal_id, tx_id, **payload.model_dump(exclude_unset=True)
    )
    return PrecedentTransactionResponse.model_validate(tx)


@router.delete(
    "/precedents/{tx_id}",
    summary="Delete Precedent M&A Transaction",
    status_code=status.HTTP_200_OK,
)
async def delete_precedent_transaction(
    deal_id: uuid.UUID,
    tx_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    context: TenantContext = Depends(validate_deal_membership),
) -> dict:
    context.require_permission(PERM_VALUATION_WRITE)
    service = ValuationService(db)
    await service.delete_precedent(context, deal_id, tx_id)
    return {"success": True, "message": "Precedent transaction removed successfully."}


# -------------------------------------------------------------
# 6. Sensitivity, Summary & Validation
# -------------------------------------------------------------
@router.get(
    "/sensitivity",
    summary="Get 2D Valuation Sensitivity Grid",
    status_code=status.HTTP_200_OK,
    response_model=SensitivityMatrixResponse,
)
async def get_sensitivity_matrix(
    deal_id: uuid.UUID,
    matrix_type: str = Query("WACC_VS_GROWTH", description="WACC_VS_GROWTH or WACC_VS_EXIT_MULTIPLE"),
    db: AsyncSession = Depends(get_db),
    context: TenantContext = Depends(validate_deal_membership),
) -> SensitivityMatrixResponse:
    context.require_permission(PERM_VALUATION_READ)
    service = ValuationService(db)
    matrix_res = await service.get_sensitivity_matrix(context, deal_id, matrix_type=matrix_type)
    return SensitivityMatrixResponse(**matrix_res)


@router.get(
    "/summary",
    summary="Get Football Field Valuation Range & Methodology Summary",
    status_code=status.HTTP_200_OK,
    response_model=ValuationSummaryResponse,
)
async def get_valuation_summary(
    deal_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    context: TenantContext = Depends(validate_deal_membership),
) -> ValuationSummaryResponse:
    context.require_permission(PERM_VALUATION_READ)
    service = ValuationService(db)
    summary_res = await service.get_valuation_summary(context, deal_id)
    return ValuationSummaryResponse(**summary_res)


@router.get(
    "/validation",
    summary="Validate Valuation Assumptions & Consistency",
    status_code=status.HTTP_200_OK,
    response_model=ValuationValidationResponse,
)
async def validate_valuation_model(
    deal_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    context: TenantContext = Depends(validate_deal_membership),
) -> ValuationValidationResponse:
    context.require_permission(PERM_VALUATION_READ)
    service = ValuationService(db)
    report = await service.validate_valuation_model(context, deal_id)
    return ValuationValidationResponse(**report)
