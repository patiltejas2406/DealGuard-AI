"""Pydantic Schemas for Synergy Realization & Value Creation APIs."""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class SynergyCreateRequest(BaseModel):
    """Payload to register a new synergy opportunity."""
    name: str = Field(..., max_length=255, description="Synergy title (e.g. 'Global Cloud Hosting Consolidation')")
    description: Optional[str] = Field(None, description="Detailed strategic rationale and operational plan")
    synergy_type: str = Field(..., description="REVENUE, COST, OPERATIONAL")
    category: str = Field(..., description="CROSS_SELLING, PROCUREMENT, HEADCOUNT, etc.")
    confidence: str = Field("MEDIUM", description="HIGH, MEDIUM, LOW")
    baseline_value: float = Field(0.0, ge=0.0, description="Current baseline annual revenue/spend")
    target_value: float = Field(..., ge=0.0, description="Target post-synergy annual revenue/spend")
    realization_rate_pct: float = Field(100.0, ge=0.0, le=100.0, description="Execution realization rate (%)")
    probability_pct: float = Field(80.0, ge=0.0, le=100.0, description="Probability of achievement (%)")
    one_time_integration_cost: float = Field(0.0, ge=0.0, description="Upfront integration/migration CapEx/OpEx")
    realization_curve: Optional[Dict[str, float]] = Field(
        None, description="5-year ramp schedule (e.g. {'year_1': 20, 'year_2': 50, ...})"
    )
    evidence_citation_ids: Optional[List[str]] = Field(default_factory=list, description="Associated citation UUIDs")
    owner: Optional[str] = Field(None, description="Assigned integration lead")


class SynergyUpdateRequest(BaseModel):
    """Payload to update an existing synergy opportunity."""
    name: Optional[str] = None
    description: Optional[str] = None
    synergy_type: Optional[str] = None
    category: Optional[str] = None
    confidence: Optional[str] = None
    baseline_value: Optional[float] = None
    target_value: Optional[float] = None
    realization_rate_pct: Optional[float] = None
    probability_pct: Optional[float] = None
    one_time_integration_cost: Optional[float] = None
    realization_curve: Optional[Dict[str, float]] = None
    evidence_citation_ids: Optional[List[str]] = None
    owner: Optional[str] = None
    notes: Optional[str] = None


class SynergyStatusUpdateRequest(BaseModel):
    """Payload to transition synergy lifecycle status."""
    status: str = Field(..., description="IDENTIFIED, VALIDATED, PLANNED, IN_PROGRESS, PARTIALLY_REALIZED, REALIZED, AT_RISK, ABANDONED")
    notes: Optional[str] = Field(None, description="Status transition rationale / committee notes")


class SynergyActualLogRequest(BaseModel):
    """Payload to log realized performance for a fiscal period."""
    fiscal_period: str = Field(..., description="e.g. 'Q1-2024', 'FY2024'")
    planned_value: float = Field(..., description="Target planned savings / revenue for this period")
    actual_value: float = Field(..., description="Actual captured savings / revenue")
    notes: Optional[str] = None


class SynergyResponse(BaseModel):
    """Authoritative synergy opportunity response."""
    id: uuid.UUID
    deal_id: uuid.UUID
    company_id: Optional[uuid.UUID] = None
    organization_id: uuid.UUID
    name: str
    description: Optional[str] = None
    synergy_type: str
    category: str
    status: str
    confidence: str
    baseline_value: float
    target_value: float
    potential_annual_value: float
    realization_rate_pct: float
    probability_pct: float
    expected_annual_value: float
    one_time_integration_cost: float
    realization_curve: Optional[Dict[str, float]] = None
    evidence_citation_ids: Optional[List[str]] = None
    owner: Optional[str] = None
    realized_annual_value: float
    value_capture_rate_pct: float = 0.0
    variance: float = 0.0
    notes: Optional[str] = None
    created_by_id: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SynergySummaryResponse(BaseModel):
    """Aggregate portfolio synergy metrics."""
    deal_id: uuid.UUID
    total_opportunities_count: int
    total_potential_annual_value: float
    total_expected_annual_value: float
    total_realized_annual_value: float
    total_one_time_integration_cost: float
    net_annual_expected_value: float
    overall_value_capture_rate_pct: float
    by_type: Dict[str, Any]
    by_status: Dict[str, int]
    by_confidence: Dict[str, int]


class ValueBridgeResponse(BaseModel):
    """Value Creation Waterfall Bridge and Decision Score improvement."""
    deal_id: uuid.UUID
    standalone_ev: float
    pv_revenue_synergies: float
    pv_cost_synergies: float
    total_integration_costs: float
    realization_risk_discount: float
    synergy_adjusted_ev: float
    net_value_created: float
    value_creation_pct: float
    base_decision_score: float
    base_decision_band: str
    synergy_adjusted_decision_score: float
    synergy_adjusted_decision_band: str
    score_delta: float
    waterfall_steps: List[Dict[str, Any]]


class RealizationScheduleResponse(BaseModel):
    """5-year phased trajectory schedule."""
    deal_id: uuid.UUID
    schedule: List[Dict[str, Any]]
    total_5yr_expected_ebitda_impact: float
    total_5yr_net_cash_flow_impact: float
