"""Pydantic v2 Request/Response Schemas for Valuation Intelligence & Deal Valuation Engine."""

import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from app.api.v1.schemas.common import BaseResponse


# -------------------------------------------------------------
# 1. Valuation Project
# -------------------------------------------------------------
class ValuationResponse(BaseResponse):
    id: uuid.UUID
    deal_id: uuid.UUID
    title: str
    status: str
    selected_method: str
    currency: str
    proposed_ev: Optional[float] = None
    proposed_equity_value: Optional[float] = None
    notes: Optional[str] = None
    created_by_id: Optional[uuid.UUID] = None


class ValuationUpdateRequest(BaseModel):
    title: Optional[str] = None
    status: Optional[str] = None
    selected_method: Optional[str] = None
    currency: Optional[str] = None
    proposed_ev: Optional[float] = None
    proposed_equity_value: Optional[float] = None
    notes: Optional[str] = None


# -------------------------------------------------------------
# 2. Assumptions & WACC
# -------------------------------------------------------------
class ValuationAssumptionCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    value: float = Field(...)
    unit: str = Field(default="PERCENTAGE", max_length=20)
    category: str = Field(default="WACC", max_length=50)
    period: Optional[str] = None
    source_type: str = Field(default="ANALYST_INPUT", max_length=30)
    is_analyst_entered: bool = Field(default=True)
    confidence_score: Optional[float] = None
    citation_id: Optional[uuid.UUID] = None
    notes: Optional[str] = None
    valuation_id: Optional[uuid.UUID] = None


class ValuationAssumptionResponse(BaseResponse):
    id: uuid.UUID
    deal_id: uuid.UUID
    valuation_id: Optional[uuid.UUID] = None
    name: str
    category: str
    value: float
    unit: str
    period: Optional[str] = None
    source_type: str
    is_analyst_entered: bool
    confidence_score: Optional[float] = None
    citation_id: Optional[uuid.UUID] = None
    notes: Optional[str] = None


class WaccCalculateRequest(BaseModel):
    risk_free_rate: float = Field(default=4.5)
    beta: float = Field(default=1.15)
    equity_risk_premium: float = Field(default=5.5)
    pre_tax_cost_of_debt: float = Field(default=6.5)
    tax_rate: float = Field(default=25.0)
    equity_weight: float = Field(default=80.0)
    debt_weight: float = Field(default=20.0)


class WaccResponse(BaseModel):
    wacc: Optional[float] = None
    cost_of_equity: Optional[float] = None
    after_tax_cost_of_debt: Optional[float] = None
    equity_weight: Optional[float] = None
    debt_weight: Optional[float] = None
    formula: Optional[str] = None
    components: Optional[Dict[str, Any]] = None
    is_calculable: bool = True
    missing_inputs: Optional[List[str]] = None


# -------------------------------------------------------------
# 3. DCF
# -------------------------------------------------------------
class DcfCalculateRequest(BaseModel):
    projections: Optional[List[Dict[str, Any]]] = None
    wacc: Optional[float] = None
    terminal_growth_rate: Optional[float] = 3.0
    exit_multiple: Optional[float] = 10.0
    terminal_method: str = "PERPETUITY_GROWTH"
    cash: Optional[float] = 0.0
    debt: Optional[float] = 0.0
    minority_interest: Optional[float] = 0.0
    preferred_equity: Optional[float] = 0.0


class DcfResponse(BaseModel):
    valuation_id: str
    deal_id: str
    dcf: Dict[str, Any]


# -------------------------------------------------------------
# 4. Trading Comparables (CCA)
# -------------------------------------------------------------
class ComparableCompanyCreateRequest(BaseModel):
    company_name: str = Field(..., min_length=2, max_length=255)
    ticker: Optional[str] = None
    industry: Optional[str] = None
    geography: Optional[str] = None
    revenue: Optional[float] = None
    ebitda: Optional[float] = None
    ebit: Optional[float] = None
    net_income: Optional[float] = None
    enterprise_value: Optional[float] = None
    equity_value: Optional[float] = None
    revenue_growth: Optional[float] = None
    status: str = Field(default="INCLUDED")
    source: str = Field(default="ANALYST_INPUT")
    notes: Optional[str] = None
    citation_id: Optional[uuid.UUID] = None
    valuation_id: Optional[uuid.UUID] = None


class ComparableCompanyUpdateRequest(BaseModel):
    company_name: Optional[str] = None
    ticker: Optional[str] = None
    industry: Optional[str] = None
    geography: Optional[str] = None
    revenue: Optional[float] = None
    ebitda: Optional[float] = None
    ebit: Optional[float] = None
    net_income: Optional[float] = None
    enterprise_value: Optional[float] = None
    equity_value: Optional[float] = None
    revenue_growth: Optional[float] = None
    status: Optional[str] = None
    source: Optional[str] = None
    notes: Optional[str] = None


class ComparableCompanyResponse(BaseResponse):
    id: uuid.UUID
    deal_id: uuid.UUID
    valuation_id: Optional[uuid.UUID] = None
    company_name: str
    ticker: Optional[str] = None
    industry: Optional[str] = None
    geography: Optional[str] = None
    revenue: Optional[float] = None
    ebitda: Optional[float] = None
    ebit: Optional[float] = None
    net_income: Optional[float] = None
    enterprise_value: Optional[float] = None
    equity_value: Optional[float] = None
    ev_to_revenue: Optional[float] = None
    ev_to_ebitda: Optional[float] = None
    pe_ratio: Optional[float] = None
    revenue_growth: Optional[float] = None
    status: str
    source: str
    notes: Optional[str] = None
    citation_id: Optional[uuid.UUID] = None


class ComparableAnalysisResponse(BaseModel):
    valuation_id: str
    deal_id: str
    companies: List[Dict[str, Any]]
    statistics: Dict[str, Any]
    implied_valuation_revenue: Dict[str, Any]
    implied_valuation_ebitda: Dict[str, Any]


# -------------------------------------------------------------
# 5. Precedent Transactions (PTA)
# -------------------------------------------------------------
class PrecedentTransactionCreateRequest(BaseModel):
    target_name: str = Field(..., min_length=2, max_length=255)
    acquirer_name: Optional[str] = None
    announcement_date: Optional[str] = None
    transaction_value: Optional[float] = None
    enterprise_value: Optional[float] = None
    revenue: Optional[float] = None
    ebitda: Optional[float] = None
    transaction_type: str = Field(default="100%_ACQUISITION")
    industry: Optional[str] = None
    geography: Optional[str] = None
    status: str = Field(default="INCLUDED")
    source: str = Field(default="ANALYST_INPUT")
    notes: Optional[str] = None
    citation_id: Optional[uuid.UUID] = None
    valuation_id: Optional[uuid.UUID] = None


class PrecedentTransactionUpdateRequest(BaseModel):
    target_name: Optional[str] = None
    acquirer_name: Optional[str] = None
    announcement_date: Optional[str] = None
    transaction_value: Optional[float] = None
    enterprise_value: Optional[float] = None
    revenue: Optional[float] = None
    ebitda: Optional[float] = None
    transaction_type: Optional[str] = None
    industry: Optional[str] = None
    geography: Optional[str] = None
    status: Optional[str] = None
    source: Optional[str] = None
    notes: Optional[str] = None


class PrecedentTransactionResponse(BaseResponse):
    id: uuid.UUID
    deal_id: uuid.UUID
    valuation_id: Optional[uuid.UUID] = None
    target_name: str
    acquirer_name: Optional[str] = None
    announcement_date: Optional[str] = None
    transaction_value: Optional[float] = None
    enterprise_value: Optional[float] = None
    revenue: Optional[float] = None
    ebitda: Optional[float] = None
    ev_to_revenue: Optional[float] = None
    ev_to_ebitda: Optional[float] = None
    transaction_type: str
    industry: Optional[str] = None
    geography: Optional[str] = None
    status: str
    source: str
    notes: Optional[str] = None
    citation_id: Optional[uuid.UUID] = None


class PrecedentAnalysisResponse(BaseModel):
    valuation_id: str
    deal_id: str
    transactions: List[Dict[str, Any]]
    statistics: Dict[str, Any]
    implied_valuation_revenue: Dict[str, Any]
    implied_valuation_ebitda: Dict[str, Any]


# -------------------------------------------------------------
# 6. Sensitivity, Summary & Validation
# -------------------------------------------------------------
class SensitivityMatrixResponse(BaseModel):
    type: str
    row_variable: str
    column_variable: str
    row_values: List[float]
    column_values: List[float]
    base_row_index: int
    base_column_index: int
    enterprise_value_matrix: List[List[Optional[float]]]
    equity_value_matrix: List[List[Optional[float]]]


class MethodologyRange(BaseModel):
    methodology: str
    label: str
    ev_low: Optional[float] = None
    ev_base: Optional[float] = None
    ev_high: Optional[float] = None
    equity_low: Optional[float] = None
    equity_base: Optional[float] = None
    equity_high: Optional[float] = None


class ValuationSummaryResponse(BaseModel):
    valuation_id: str
    deal_id: str
    currency: str
    proposed_ev: Optional[float] = None
    proposed_equity_value: Optional[float] = None
    methodologies: List[MethodologyRange]
    transaction_comparison: Optional[Dict[str, Any]] = None


class ValuationValidationCheck(BaseModel):
    check_name: str
    passed: bool
    severity: str
    message: str


class ValuationValidationResponse(BaseModel):
    deal_id: str
    status: str
    checks: List[ValuationValidationCheck]
