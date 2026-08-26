"""Pydantic Schemas for What-If Scenario Simulation & Monte Carlo Intelligence."""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class ScenarioCreateRequest(BaseModel):
    """Payload to create a new persistent What-If deal scenario."""
    name: str = Field(..., max_length=255, description="Descriptive scenario label (e.g. 'Bear Case Churn Spike')")
    description: Optional[str] = Field(None, description="Investment committee context / rationale")
    scenario_type: str = Field("WHAT_IF", description="WHAT_IF, DOWNSIDE, UPSIDE, STRESS_TEST")
    assumptions: Dict[str, float] = Field(
        ..., description="Whitelisted assumption deltas (e.g. {'revenue_growth_pct': -10.0, 'ebitda_margin_pct': 18.0})"
    )


class ScenarioUpdateRequest(BaseModel):
    """Payload to update an existing scenario's parameters."""
    name: Optional[str] = None
    description: Optional[str] = None
    assumptions: Optional[Dict[str, float]] = None
    status: Optional[str] = None


class ScenarioResponse(BaseModel):
    """Complete persistent scenario response with evaluated outcomes."""
    id: uuid.UUID
    deal_id: uuid.UUID
    organization_id: uuid.UUID
    name: str
    description: Optional[str] = None
    scenario_type: str
    status: str
    assumptions: Dict[str, Any]
    results: Optional[Dict[str, Any]] = None
    created_by_id: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SensitivityRequest(BaseModel):
    """Request payload for 1D or 2D deterministic sensitivity analysis."""
    # 1D params
    variable_name: Optional[str] = None
    steps: Optional[List[float]] = None

    # 2D params
    row_variable: Optional[str] = None
    row_steps: Optional[List[float]] = None
    col_variable: Optional[str] = None
    col_steps: Optional[List[float]] = None


class SensitivityResponse(BaseModel):
    """1D curve or 2D matrix sensitivity response with tipping-point inflection analysis."""
    type: str = Field(..., description="1D_SWEEP or 2D_MATRIX")
    data: Dict[str, Any]


class DistributionConfig(BaseModel):
    """Configuration for an individual Monte Carlo variable distribution."""
    distribution_type: str = Field("TRIANGULAR", description="TRIANGULAR, NORMAL, UNIFORM, LOGNORMAL")
    min_val: Optional[float] = None
    mode_val: Optional[float] = None
    max_val: Optional[float] = None
    mean: Optional[float] = None
    std_dev: Optional[float] = None
    sigma: Optional[float] = None


class MonteCarloRequest(BaseModel):
    """Payload to configure and trigger a Monte Carlo simulation run."""
    variable_distributions: Dict[str, DistributionConfig] = Field(
        ..., description="Distributions for uncertain variables (e.g. revenue_growth_pct, ebitda_margin_pct)"
    )
    iterations: int = Field(1000, ge=100, le=50000, description="Simulation draw count")
    random_seed: Optional[int] = Field(42, description="Deterministic seed for reproducibility")


class MonteCarloResponse(BaseModel):
    """Statistical Monte Carlo simulation outputs, percentiles, histograms, and risk metrics."""
    run_id: Optional[uuid.UUID] = None
    deal_id: uuid.UUID
    engine_version: str = "1.0"
    iterations_requested: int
    iterations_completed: int
    random_seed: Optional[int] = None
    valuation_statistics: Dict[str, Any]
    decision_score_statistics: Dict[str, Any]
    band_probabilities: Dict[str, float]
    downside_metrics: Dict[str, Any]
