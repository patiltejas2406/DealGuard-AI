"""Pydantic Request & Response Schemas for Post-Acquisition Intelligence & Value Creation."""

import uuid
from datetime import date, datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class CustomerAccountBase(BaseModel):
    account_name: str
    segment: str = "MID_MARKET"
    arr: float = 0.0
    mrr: float = 0.0
    contract_start_date: Optional[date] = None
    contract_end_date: Optional[date] = None
    churn_risk_score: float = 0.15
    health_status: str = "HEALTHY"
    nps: Optional[int] = None
    is_churned: bool = False
    expansion_potential_usd: float = 0.0
    industry: Optional[str] = None
    products_used: List[str] = Field(default_factory=list)
    notes: Optional[str] = None


class CustomerAccountCreate(CustomerAccountBase):
    company_id: Optional[uuid.UUID] = None


class CustomerAccountResponse(CustomerAccountBase):
    id: uuid.UUID
    deal_id: uuid.UUID
    organization_id: uuid.UUID
    company_id: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PostAcquisitionMetricBase(BaseModel):
    fiscal_period: str
    metric_category: str
    metric_name: str
    baseline_value: float = 0.0
    target_value: float = 0.0
    actual_value: float = 0.0
    variance_pct: float = 0.0
    unit: str = "USD"
    notes: Optional[str] = None


class PostAcquisitionMetricCreate(PostAcquisitionMetricBase):
    pass


class PostAcquisitionMetricResponse(PostAcquisitionMetricBase):
    id: uuid.UUID
    deal_id: uuid.UUID
    organization_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AcquisitionThesisBase(BaseModel):
    thesis_pillar: str
    target_metric: str
    baseline_value: float = 0.0
    target_value: float = 0.0
    actual_value: Optional[float] = None
    variance_pct: Optional[float] = None
    status: str = "INSUFFICIENT_DATA"
    rationale: Optional[str] = None
    citations: List[Dict[str, Any]] = Field(default_factory=list)


class AcquisitionThesisCreate(AcquisitionThesisBase):
    pass


class AcquisitionThesisResponse(AcquisitionThesisBase):
    id: uuid.UUID
    deal_id: uuid.UUID
    organization_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ValueCreationInitiativeBase(BaseModel):
    pillar: str
    title: str
    description: Optional[str] = None
    owner: Optional[str] = None
    target_ebitda_impact: float = 0.0
    realized_ebitda_impact: float = 0.0
    status: str = "IDENTIFIED"
    timeline_quarter: str = "Q1_POST_CLOSE"
    notes: Optional[str] = None


class ValueCreationInitiativeCreate(ValueCreationInitiativeBase):
    pass


class ValueCreationInitiativeResponse(ValueCreationInitiativeBase):
    id: uuid.UUID
    deal_id: uuid.UUID
    organization_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# High-Level Domain View Schemas
class PostAcquisitionOverviewResponse(BaseModel):
    deal_id: uuid.UUID
    deal_title: str
    company_name: str
    overall_thesis_status: str
    health_score: float
    total_arr: float
    nrr_pct: Optional[float] = None
    synergy_realization_pct: Optional[float] = None
    integration_completion_pct: float = 0.0
    open_blockers_count: int = 0
    at_risk_customers_count: int = 0
    active_initiatives_count: int = 0
    pillars: Dict[str, Any] = Field(default_factory=dict)
    key_highlights: List[str] = Field(default_factory=list)
    top_risks: List[str] = Field(default_factory=list)


class PostAcquisitionPerformanceResponse(BaseModel):
    deal_id: uuid.UUID
    metrics: List[PostAcquisitionMetricResponse]
    revenue_growth_pct: Optional[float] = None
    ebitda_margin_pct: Optional[float] = None
    historical_periods: List[str] = Field(default_factory=list)
    data_gaps: List[str] = Field(default_factory=list)


class PostAcquisitionIntegrationResponse(BaseModel):
    deal_id: uuid.UUID
    program_name: Optional[str] = None
    total_milestones: int = 0
    completed_milestones: int = 0
    overdue_milestones: int = 0
    critical_path_milestones: int = 0
    completion_pct: float = 0.0
    health_score: float = 0.0
    open_blockers: List[Dict[str, Any]] = Field(default_factory=list)
    workstreams: List[Dict[str, Any]] = Field(default_factory=list)
    data_gaps: List[str] = Field(default_factory=list)


class PostAcquisitionSynergiesResponse(BaseModel):
    deal_id: uuid.UUID
    total_expected_annual_synergy: float = 0.0
    total_realized_annual_synergy: float = 0.0
    realization_rate_pct: Optional[float] = None
    cost_synergies_realized: float = 0.0
    revenue_synergies_realized: float = 0.0
    opportunities_count: int = 0
    realization_logs: List[Dict[str, Any]] = Field(default_factory=list)
    data_gaps: List[str] = Field(default_factory=list)


class PostAcquisitionCustomersResponse(BaseModel):
    deal_id: uuid.UUID
    total_accounts: int = 0
    total_arr: float = 0.0
    average_churn_risk: float = 0.0
    at_risk_arr: float = 0.0
    at_risk_accounts: List[CustomerAccountResponse] = Field(default_factory=list)
    expansion_pipeline_usd: float = 0.0
    nrr_pct: Optional[float] = None
    churn_rate_pct: Optional[float] = None
    data_gaps: List[str] = Field(default_factory=list)


class PostAcquisitionRisksResponse(BaseModel):
    deal_id: uuid.UUID
    total_risks_count: int = 0
    critical_risks_count: int = 0
    high_risks_count: int = 0
    emerging_post_close_risks: List[Dict[str, Any]] = Field(default_factory=list)
    data_gaps: List[str] = Field(default_factory=list)


class PostAcquisitionThesisResponse(BaseModel):
    deal_id: uuid.UUID
    overall_status: str
    theses: List[AcquisitionThesisResponse]
    initiatives: List[ValueCreationInitiativeResponse]
    data_gaps: List[str] = Field(default_factory=list)
