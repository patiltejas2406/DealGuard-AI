"""Pydantic Request and Response Schemas for Technology & Operational Diligence."""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class TechnologyFindingCreateRequest(BaseModel):
    category: str
    title: str = Field(..., max_length=255)
    technical_fact: str
    business_impact: Optional[str] = None
    recommendation: Optional[str] = None
    severity: str = Field(default="MEDIUM")
    likelihood: str = Field(default="MEDIUM")
    confidence: str = Field(default="HIGH")
    monetary_exposure: float = Field(default=0.0, ge=0.0)


class TechnologyFindingStatusUpdateRequest(BaseModel):
    status: str = Field(..., description="IDENTIFIED, REQUIRES_REVIEW, REMEDIATION_PLANNED, MITIGATED, ACCEPTED")
    notes: Optional[str] = None


class TechnologyFindingResponse(BaseModel):
    id: uuid.UUID
    deal_id: uuid.UUID
    company_id: Optional[uuid.UUID] = None
    document_id: Optional[uuid.UUID] = None
    category: str
    title: str
    technical_fact: str
    business_impact: Optional[str] = None
    recommendation: Optional[str] = None
    severity: str
    likelihood: str
    confidence: str
    monetary_exposure: float
    status: str
    linked_risk_id: Optional[uuid.UUID] = None
    linked_workstream_id: Optional[uuid.UUID] = None
    linked_milestone_id: Optional[uuid.UUID] = None
    citation_id: Optional[uuid.UUID] = None
    fingerprint: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OperationalMetricResponse(BaseModel):
    id: uuid.UUID
    deal_id: uuid.UUID
    company_id: Optional[uuid.UUID] = None
    metric_category: str
    metric_name: str
    observed_value: float
    target_value: Optional[float] = None
    unit: str
    deviation: Optional[float] = None
    status: str
    evidence_summary: Optional[str] = None
    citation_id: Optional[uuid.UUID] = None
    fingerprint: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TechnologyDependencyResponse(BaseModel):
    id: uuid.UUID
    deal_id: uuid.UUID
    dependency_name: str
    dependency_type: str
    provider: str
    purpose: Optional[str] = None
    criticality: str
    failure_impact: Optional[str] = None
    replacement_difficulty: str
    is_single_point_of_failure: bool
    annual_cost: float
    contract_id: Optional[uuid.UUID] = None
    citation_id: Optional[uuid.UUID] = None
    fingerprint: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TechnologySummaryResponse(BaseModel):
    deal_id: uuid.UUID
    technology_risk_score: float
    technology_health_score: float
    risk_band: str
    spof_count: int
    annual_cloud_spend: float
    monthly_run_rate: float
    total_findings_count: int
    critical_findings_count: int
    high_findings_count: int
    medium_findings_count: int
    low_findings_count: int
    total_dependencies_count: int
    critical_dependencies_count: int
    average_uptime_pct: float
    sla_breaches_count: int
    total_monetary_exposure: float


class TechnologyScanResponse(BaseModel):
    deal_id: uuid.UUID
    findings_extracted: int
    metrics_recorded: int
    dependencies_identified: int
    message: str
