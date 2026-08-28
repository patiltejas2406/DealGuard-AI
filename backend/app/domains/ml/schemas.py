"""Machine Learning Foundation & Model Architecture Schemas."""

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field


class ModelTaskType(str, Enum):
    """Predictive and analytical ML task types."""
    REVENUE_FORECAST = "REVENUE_FORECAST"
    CHURN_PREDICTION = "CHURN_PREDICTION"
    EBITDA_FORECAST = "EBITDA_FORECAST"
    RISK_PROBABILITY = "RISK_PROBABILITY"
    INTEGRATION_FAILURE_PROBABILITY = "INTEGRATION_FAILURE_PROBABILITY"
    SYNERGY_REALIZATION_PROBABILITY = "SYNERGY_REALIZATION_PROBABILITY"
    POST_ACQUISITION_HEALTH = "POST_ACQUISITION_HEALTH"


class ModelStatus(str, Enum):
    """Lifecycle status of an institutional ML model."""
    REGISTERED = "REGISTERED"
    TRAINING = "TRAINING"
    VALIDATED = "VALIDATED"
    DEPLOYED = "DEPLOYED"
    DEPRECATED = "DEPRECATED"


class ModelMetadata(BaseModel):
    """Production metadata describing an ML model architecture and training lineage."""
    model_id: str
    name: str
    version: str = "1.0.0"
    task_type: ModelTaskType
    framework: str = "scikit-learn"  # e.g., scikit-learn, xgboost, lightgbm, pytorch
    training_dataset_id: Optional[str] = None
    feature_names: List[str] = Field(default_factory=list)
    hyperparameters: Dict[str, Any] = Field(default_factory=dict)
    evaluation_metrics: Dict[str, float] = Field(
        default_factory=dict,
        description="Validated evaluation metrics (e.g. RMSE, R2, AUC-ROC, F1, MAE)."
    )
    status: ModelStatus = ModelStatus.REGISTERED
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class FeatureSet(BaseModel):
    """Standardized feature vector snapshot passed into a prediction model."""
    feature_set_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    entity_type: str = "Deal"
    entity_id: uuid.UUID
    features: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class PredictionRequest(BaseModel):
    """Request payload for executing a model inference."""
    model_id: str
    model_version: Optional[str] = None
    deal_id: Optional[uuid.UUID] = None
    organization_id: uuid.UUID
    features: Dict[str, Any]
    request_explanation: bool = True


class FeatureImportance(BaseModel):
    """Feature importance ranking for model interpretability."""
    feature_name: str
    importance_score: float
    rank: int
    direction: str = "POSITIVE"  # POSITIVE, NEGATIVE, NEUTRAL


class SHAPValue(BaseModel):
    """Exact SHAP attribution value for a specific feature input."""
    feature_name: str
    base_value: float
    shap_value: float
    actual_value: Any


class XAIExplanation(BaseModel):
    """Explainable AI (XAI) attribution payload accompanying a prediction."""
    explanation_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    prediction_id: uuid.UUID
    model_id: str
    method: str = "SHAP_TREE"  # SHAP_TREE, SHAP_KERNEL, PERMUTATION_IMPORTANCE, FEATURE_ATTRIBUTION
    top_features: List[FeatureImportance] = Field(default_factory=list)
    shap_values: Optional[List[SHAPValue]] = None
    feature_snapshot: Dict[str, Any] = Field(default_factory=dict)
    narrative_summary: str
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class PredictionResult(BaseModel):
    """Standardized output from an ML model inference."""
    prediction_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    model_id: str
    model_version: str
    task_type: ModelTaskType
    predicted_value: Any
    probability_distribution: Optional[Dict[str, float]] = None
    confidence_interval: Optional[Tuple[float, float]] = None
    prediction_confidence: float = Field(ge=0.0, le=1.0, default=0.90)
    explanation: Optional[XAIExplanation] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class TrainingRun(BaseModel):
    """Audit record of an ML model training execution."""
    run_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    model_id: str
    dataset_uri: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    metrics: Dict[str, float] = Field(default_factory=dict)
    status: str = "COMPLETED"
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
