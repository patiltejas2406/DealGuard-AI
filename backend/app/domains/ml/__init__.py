"""Machine Learning & Explainable AI (XAI) Domain."""

from app.domains.ml.schemas import (
    ModelTaskType,
    ModelStatus,
    ModelMetadata,
    FeatureSet,
    PredictionRequest,
    PredictionResult,
    FeatureImportance,
    SHAPValue,
    XAIExplanation,
    TrainingRun,
)
from app.domains.ml.interfaces import BasePredictionModel, ModelRegistry
from app.domains.ml.registry import initialize_standard_ml_catalog

__all__ = [
    "ModelTaskType",
    "ModelStatus",
    "ModelMetadata",
    "FeatureSet",
    "PredictionRequest",
    "PredictionResult",
    "FeatureImportance",
    "SHAPValue",
    "XAIExplanation",
    "TrainingRun",
    "BasePredictionModel",
    "ModelRegistry",
    "initialize_standard_ml_catalog",
]
