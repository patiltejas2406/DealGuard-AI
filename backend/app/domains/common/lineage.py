"""Model Provenance, Decision Lineage & Closed-Loop Telemetry Contracts."""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class PredictionMetadata(BaseModel):
    """Metadata capturing machine learning or algorithmic prediction lineage."""
    model_name: str = Field(description="Identifier of model or engine: e.g. 'decision-score-v1', 'churn-classifier-v1'")
    model_version: str = Field(default="1.0.0")
    prediction_type: str = Field(description="CLASSIFICATION, REGRESSION, PROBABILITY, INDEX_SCORE")
    input_feature_hash: Optional[str] = None
    confidence_score: Optional[float] = Field(ge=0.0, le=1.0, default=None)
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ClosedLoopDecisionTrace(BaseModel):
    """
    Closed-loop provenance record tracking:
    Observe -> Understand -> Predict -> Recommend -> Act -> Measure -> Learn -> Optimize
    """
    trace_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    organization_id: uuid.UUID
    deal_id: Optional[uuid.UUID] = None
    company_id: Optional[uuid.UUID] = None
    
    # 1. Observation & Evidence
    evidence_citation_ids: List[uuid.UUID] = Field(default_factory=list)
    
    # 2. Prediction / Finding
    prediction: Optional[PredictionMetadata] = None
    predicted_value: Optional[Any] = None
    
    # 3. Recommendation
    recommended_action: Optional[str] = None
    recommendation_rationale: Optional[str] = None
    
    # 4. Action & Human-in-the-Loop
    human_approval_status: str = Field(default="PENDING")  # PENDING, APPROVED, REJECTED, OVERRIDDEN
    action_executed: bool = False
    action_executed_at: Optional[datetime] = None
    
    # 5. Measurement & Outcome
    actual_outcome_value: Optional[Any] = None
    outcome_recorded_at: Optional[datetime] = None
    value_delta: Optional[float] = None
    
    metadata: Dict[str, Any] = Field(default_factory=dict)
