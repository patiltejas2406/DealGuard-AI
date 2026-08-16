"""Pydantic v2 Request/Response Schemas for Financial Statements, Metrics & QoE."""

import uuid
from datetime import date, datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from app.api.v1.schemas.common import BaseResponse


class FinancialStatementCreateRequest(BaseModel):
    statement_type: str = Field(..., description="INCOME_STATEMENT, BALANCE_SHEET, CASH_FLOW")
    fiscal_year: int = Field(..., ge=1990, le=2100)
    fiscal_period: str = Field(..., min_length=2, max_length=20, description="e.g. FY2023")
    line_items: Dict[str, Any] = Field(..., description="Structured dictionary of line items")

    source_currency: str = Field(default="USD", max_length=3)
    period_type: str = Field(default="ANNUAL", max_length=20)
    is_audited: bool = Field(default=False)
    is_normalized: bool = Field(default=False)
    source_document_id: Optional[uuid.UUID] = None


class FinancialStatementResponse(BaseResponse):
    id: uuid.UUID
    deal_id: uuid.UUID
    statement_type: str
    period_type: str
    fiscal_year: int
    fiscal_period: str
    period_end_date: Optional[date] = None
    source_currency: str
    is_audited: bool
    is_normalized: bool
    source_document_id: Optional[uuid.UUID] = None
    line_items: Dict[str, Any]


class FinancialMetricResponse(BaseResponse):
    id: uuid.UUID
    deal_id: uuid.UUID
    statement_id: Optional[uuid.UUID] = None
    citation_id: Optional[uuid.UUID] = None
    metric_name: str
    period: str
    value: float
    unit: str
    source_currency: str
    is_normalized: bool
    calculation_formula: Optional[str] = None


class QoEAdjustmentCreateRequest(BaseModel):
    category: str = Field(..., description="ONE_TIME_EXPENSE, LEGAL_NON_RECURRING, RESTRUCTURING, OWNER_PERSONAL, PRO_FORMA, OTHER")
    description: str = Field(..., min_length=3, max_length=255)
    amount: float = Field(...)
    currency: str = Field(default="USD", max_length=3)
    period: str = Field(default="FY2023", max_length=20)
    treatment: str = Field(default="ADD_BACK", description="ADD_BACK or DEDUCTION")
    status: str = Field(default="PROPOSED", description="PROPOSED, APPROVED, REJECTED")
    notes: Optional[str] = None
    citation_id: Optional[uuid.UUID] = None


class QoEAdjustmentUpdateRequest(BaseModel):
    category: Optional[str] = None
    description: Optional[str] = None
    amount: Optional[float] = None
    treatment: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None


class QoEAdjustmentResponse(BaseResponse):
    id: uuid.UUID
    deal_id: uuid.UUID
    category: str
    description: str
    amount: float
    currency: str
    period: str
    treatment: str
    status: str
    notes: Optional[str] = None
    citation_id: Optional[uuid.UUID] = None
    created_by_id: Optional[uuid.UUID] = None


class QoEBridgeSummary(BaseModel):
    reported_ebitda: Optional[float] = None
    total_add_backs: float = 0.0
    total_deductions: float = 0.0
    net_adjustment: float = 0.0
    adjusted_ebitda: Optional[float] = None
    adjustment_count: int = 0
    applied_adjustments_count: int = 0
    category_breakdown: Dict[str, float] = Field(default_factory=dict)


class QoEBridgeResponse(BaseModel):
    deal_id: str
    period: str
    bridge: QoEBridgeSummary
    adjustments: List[Dict[str, Any]]


class CagrAnalysisResponse(BaseModel):
    start_period: Optional[str] = None
    end_period: Optional[str] = None
    years: Optional[int] = None
    revenue_start: Optional[float] = None
    revenue_end: Optional[float] = None
    revenue_cagr: Optional[float] = None
    ebitda_start: Optional[float] = None
    ebitda_end: Optional[float] = None
    ebitda_cagr: Optional[float] = None
    message: Optional[str] = None


class FinancialValidationCheck(BaseModel):
    statement_type: str
    period: str
    check_name: str
    passed: bool
    severity: str
    message: str


class FinancialValidationResponse(BaseModel):
    deal_id: str
    status: str
    total_statements_checked: int
    checks: List[FinancialValidationCheck]
