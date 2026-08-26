"""Pydantic Schemas for Composite Decision Score & Explainability APIs."""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class ScoreComponentDetail(BaseModel):
    """Detailed breakdown for an individual scoring component."""
    name: str = Field(..., description="Component identifier (e.g. FINANCIAL_HEALTH, RISK_EXPOSURE)")
    score: float = Field(..., ge=0.0, le=100.0, description="Normalized score 0-100")
    weight: float = Field(..., ge=0.0, le=1.0, description="Component weight allocation")
    weighted_contribution: float = Field(..., description="Contribution points to overall score")
    status: str = Field(..., description="Data availability status (AVAILABLE, PARTIAL, INSUFFICIENT_DATA)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Component confidence 0-1")
    raw_inputs: Dict[str, Any] = Field(default_factory=dict, description="Raw domain metrics and ratios evaluated")
    explanation: str = Field(..., description="Human-readable calculation explanation")
    drivers: List[Dict[str, Any]] = Field(default_factory=list, description="Specific positive or negative factors")

    model_config = ConfigDict(from_attributes=True)


class DriverItem(BaseModel):
    """Specific positive or downside driver affecting the investment score."""
    driver: str
    type: str = Field(..., description="POSITIVE, NEGATIVE, or NEUTRAL")
    impact: str = Field(..., description="CRITICAL, HIGH, MEDIUM, LOW")
    component: Optional[str] = None


class DecisionScoreResponse(BaseModel):
    """Authoritative Composite DealGuard Decision Score summary response."""
    id: Optional[uuid.UUID] = None
    deal_id: uuid.UUID
    company_id: Optional[uuid.UUID] = None
    score_type: str = "DEAL"
    overall_score: float = Field(..., ge=0.0, le=100.0)
    decision_band: str = Field(..., description="STRONG, FAVORABLE, CAUTION, HIGH_RISK, AVOID")
    decision_band_description: str
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    scoring_version: str = "1.0"
    created_at: Optional[datetime] = None

    # High-level summary components
    components: Dict[str, ScoreComponentDetail]
    positive_drivers: List[DriverItem] = Field(default_factory=list)
    negative_drivers: List[DriverItem] = Field(default_factory=list)
    missing_information: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class DecisionScoreCalculateRequest(BaseModel):
    """Explicit score calculation request with optional custom weights for sensitivity modeling."""
    custom_weights: Optional[Dict[str, float]] = Field(
        None, description="Optional custom weights summing to 1.00 (e.g. {'FINANCIAL_HEALTH': 0.30, ...})"
    )


class DecisionScoreHistoryItem(BaseModel):
    """Summary of a past decision score calculation."""
    id: uuid.UUID
    overall_score: float
    decision_band: str
    confidence_score: float
    scoring_version: str
    created_at: datetime
    calculated_by_id: Optional[uuid.UUID] = None

    model_config = ConfigDict(from_attributes=True)


class DecisionScoreHistoryResponse(BaseModel):
    """Historical timeline of calculated decision scores for a deal workspace."""
    deal_id: uuid.UUID
    total_calculations: int
    history: List[DecisionScoreHistoryItem]
