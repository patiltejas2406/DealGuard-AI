"""Machine Learning Data Contracts, Feature Definitions & Dataset Schemas."""

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field


def utc_now() -> datetime:
    """Return timezone-aware current UTC datetime."""
    return datetime.now(timezone.utc)


class DataType(str, Enum):
    """Primitive and structured data types for features."""
    FLOAT = "FLOAT"
    INT = "INT"
    CATEGORICAL = "CATEGORICAL"
    BOOLEAN = "BOOLEAN"
    TIMESTAMP = "TIMESTAMP"


class TargetType(str, Enum):
    """Target variable classification."""
    REGRESSION = "REGRESSION"
    BINARY_CLASSIFICATION = "BINARY_CLASSIFICATION"
    MULTICLASS_CLASSIFICATION = "MULTICLASS_CLASSIFICATION"


class SplitMethod(str, Enum):
    """Dataset partition methodology."""
    STRATIFIED = "STRATIFIED"
    TIME_AWARE = "TIME_AWARE"
    RANDOM = "RANDOM"


class FeatureDefinition(BaseModel):
    """Specification of an individual feature in a dataset schema."""
    name: str
    data_type: DataType = DataType.FLOAT
    description: str
    domain: str  # FINANCIAL, RISK, VALUATION, OPERATIONAL, LEGAL, SYNERGY
    is_nullable: bool = False
    default_value: Optional[Any] = None
    expected_bounds: Optional[Tuple[float, float]] = None
    allowed_categories: Optional[List[str]] = None
    leakage_risk_notes: Optional[str] = None


class TargetDefinition(BaseModel):
    """Specification of the prediction target variable."""
    name: str
    target_type: TargetType
    description: str
    class_labels: Optional[List[str]] = None  # e.g., ["NO_CHURN", "CHURN"] or ["LOW_RISK", "HIGH_RISK"]
    valid_range: Optional[Tuple[float, float]] = None
    unit: Optional[str] = None


class DatasetMetadata(BaseModel):
    """Immutable metadata describing a training, validation, or benchmark dataset."""
    dataset_id: str
    version: str = "1.0.0"
    name: str
    source: str
    task_type: str
    target_name: str
    row_count: int
    feature_count: int
    split_method: SplitMethod = SplitMethod.STRATIFIED
    train_ratio: float = 0.70
    val_ratio: float = 0.15
    test_ratio: float = 0.15
    data_checksum: str
    is_benchmark: bool = False
    is_synthetic: bool = False
    created_at: datetime = Field(default_factory=utc_now)
    leakage_notes: Optional[str] = None


class DatasetSnapshot(BaseModel):
    """Serialized dataset snapshot with feature records and target vectors."""
    metadata: DatasetMetadata
    features: List[Dict[str, Any]]
    targets: List[Any]
    feature_definitions: List[FeatureDefinition]
    target_definition: TargetDefinition


class DatasetSuitabilityReport(BaseModel):
    """Assessment of dataset readiness for empirical machine learning training."""
    dataset_id: str
    is_suitable_for_training: bool
    total_rows: int
    missing_value_pct: float
    duplicate_rows_count: int
    class_imbalance_ratio: Optional[float] = None
    leakage_risks: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
