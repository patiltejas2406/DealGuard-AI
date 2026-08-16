"""Pydantic v2 Request and Response Schemas."""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class BaseResponse(BaseModel):
    """Base API response with ORM mode enabled."""
    model_config = ConfigDict(from_attributes=True)


# --- Organization Schemas ---
class OrganizationResponse(BaseResponse):
    id: uuid.UUID
    name: str
    slug: str
    is_active: bool
    tier: str
    created_at: datetime


class OrganizationCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    slug: str = Field(..., min_length=2, max_length=100)
    admin_email: str = Field(..., min_length=5, max_length=255)
    admin_password: str = Field(..., min_length=8)
    admin_full_name: str = Field(..., min_length=2, max_length=255)


# --- Target Company Schemas ---
class TargetCompanyResponse(BaseResponse):
    id: uuid.UUID
    name: str
    industry: str
    sector: Optional[str] = None
    headquarters: Optional[str] = None
    website: Optional[str] = None
    employee_count: Optional[int] = None
    description: Optional[str] = None


# --- Deal Schemas ---
class DealMemberResponse(BaseResponse):
    id: uuid.UUID
    user_id: uuid.UUID
    deal_role: str
    can_edit: bool


class DealResponse(BaseResponse):
    id: uuid.UUID
    organization_id: uuid.UUID
    target_company_id: uuid.UUID
    title: str
    code_name: Optional[str] = None
    deal_type: str
    stage: str
    status: str
    target_ev: Optional[float] = None
    currency: str
    decision_score: Optional[float] = None
    created_at: datetime
    target_company: Optional[TargetCompanyResponse] = None
    members: Optional[List[DealMemberResponse]] = None


class DealCreateRequest(BaseModel):
    company_name: str = Field(..., min_length=2, max_length=255)
    company_industry: str = Field(..., min_length=2, max_length=100)
    deal_title: str = Field(..., min_length=2, max_length=255)
    code_name: Optional[str] = Field(None, max_length=100)
    deal_type: str = Field(default="M_AND_A_BUY_SIDE")
    stage: str = Field(default="PRE_DILIGENCE")
    target_ev: Optional[float] = None
    currency: str = Field(default="USD", min_length=3, max_length=3)


# --- Document & Citation Schemas ---
class DocumentResponse(BaseResponse):
    id: uuid.UUID
    deal_id: uuid.UUID
    name: str
    file_type: str
    mime_type: str
    size_bytes: int
    sha256_hash: str
    status: str
    doc_category: Optional[str] = None
    created_at: datetime


class CitationResponse(BaseResponse):
    id: uuid.UUID
    document_id: uuid.UUID
    page_number: int
    section: Optional[str] = None
    exact_quote: str
    confidence_score: float


# --- Financial Statement & Metric Schemas ---
class FinancialMetricResponse(BaseResponse):
    id: uuid.UUID
    metric_name: str
    period: str
    value: float
    unit: str
    source_currency: str
    is_normalized: bool
    calculation_formula: Optional[str] = None


class FinancialStatementResponse(BaseResponse):
    id: uuid.UUID
    statement_type: str
    period_type: str
    fiscal_year: int
    fiscal_period: str
    source_currency: str
    is_audited: bool
    is_normalized: bool
    line_items: Dict[str, Any]
    metrics: Optional[List[FinancialMetricResponse]] = None


# --- Risk Schemas ---
class RiskEvidenceResponse(BaseResponse):
    id: uuid.UUID
    citation_id: uuid.UUID
    relevance_explanation: Optional[str] = None
    weight: float
    citation: Optional[CitationResponse] = None


class RiskResponse(BaseResponse):
    id: uuid.UUID
    category: str
    title: str
    description: str
    severity: int
    likelihood: int
    score: int
    status: str
    mitigation_strategy: Optional[str] = None
    evidence_items: Optional[List[RiskEvidenceResponse]] = None
