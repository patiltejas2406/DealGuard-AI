"""Machine Learning & Explainable AI (XAI) Domain Package."""

from app.domains.ml.data_contracts import (
    DataType,
    DatasetMetadata,
    DatasetSnapshot,
    DatasetSuitabilityReport,
    FeatureDefinition,
    SplitMethod,
    TargetDefinition,
    TargetType,
)
from app.domains.ml.evaluation import ModelEvaluator
from app.domains.ml.feature_engineering import DealFeatureExtractor, TabularPreprocessor
from app.domains.ml.models import (
    MLDatasetRecord,
    MLModelRecord,
    MLPredictionRecord,
    MLTrainingRunRecord,
)
from app.domains.ml.pipeline import MLTrainingPipeline, TrainedModelWrapper
from app.domains.ml.registry import ExtendedModelRegistry, ModelRegistry
from app.domains.ml.schemas import (
    FeatureImportance,
    FeatureSet,
    ModelMetadata,
    ModelStatus,
    ModelTaskType,
    PredictionRequest,
    PredictionResult,
    SHAPValue,
    TrainingRun,
    XAIExplanation,
)
from app.domains.ml.service import MLPredictionService
from app.domains.ml.xai_engine import XAIEngine

__all__ = [
    "DataType",
    "DatasetMetadata",
    "DatasetSnapshot",
    "DatasetSuitabilityReport",
    "FeatureDefinition",
    "SplitMethod",
    "TargetDefinition",
    "TargetType",
    "ModelEvaluator",
    "DealFeatureExtractor",
    "TabularPreprocessor",
    "MLDatasetRecord",
    "MLTrainingRunRecord",
    "MLModelRecord",
    "MLPredictionRecord",
    "MLTrainingPipeline",
    "TrainedModelWrapper",
    "ExtendedModelRegistry",
    "ModelRegistry",
    "FeatureImportance",
    "FeatureSet",
    "ModelMetadata",
    "ModelStatus",
    "ModelTaskType",
    "PredictionRequest",
    "PredictionResult",
    "SHAPValue",
    "TrainingRun",
    "XAIExplanation",
    "MLPredictionService",
    "XAIEngine",
]
