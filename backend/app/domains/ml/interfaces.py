"""Machine Learning Interfaces & Production Model Registry."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from app.domains.ml.schemas import (
    FeatureSet,
    ModelMetadata,
    PredictionRequest,
    PredictionResult,
    XAIExplanation,
)


class BasePredictionModel(ABC):
    """
    Abstract interface for all institutional machine learning prediction models.
    Enforces feature validation, reproducible inference, confidence scoring,
    and explainability (XAI) contracts.
    """

    @property
    @abstractmethod
    def metadata(self) -> ModelMetadata:
        """Production metadata describing the model architecture, task, and metrics."""
        pass

    @abstractmethod
    def validate_features(self, features: Dict[str, Any]) -> tuple[bool, List[str]]:
        """Validate that input feature dict contains all required features."""
        pass

    @abstractmethod
    async def predict(self, request: PredictionRequest) -> PredictionResult:
        """Execute model inference and return standardized PredictionResult."""
        pass

    @abstractmethod
    async def explain(
        self, request: PredictionRequest, result: PredictionResult
    ) -> Optional[XAIExplanation]:
        """Generate explainability attributions (e.g. SHAP values / feature importance)."""
        pass


class ModelRegistry:
    """Production registry of registered and validated machine learning models."""

    _models: Dict[str, BasePredictionModel] = {}
    _metadata_catalog: Dict[str, ModelMetadata] = {}

    @classmethod
    def register_model(cls, model: BasePredictionModel) -> None:
        """Register an active prediction model instance."""
        meta = model.metadata
        cls._models[meta.model_id] = model
        cls._metadata_catalog[meta.model_id] = meta

    @classmethod
    def register_metadata_only(cls, metadata: ModelMetadata) -> None:
        """Register metadata for a scheduled or pipeline model."""
        cls._metadata_catalog[metadata.model_id] = metadata

    @classmethod
    def get_model(cls, model_id: str) -> Optional[BasePredictionModel]:
        """Retrieve an active model instance by ID."""
        return cls._models.get(model_id)

    @classmethod
    def get_metadata(cls, model_id: str) -> Optional[ModelMetadata]:
        """Retrieve model metadata by ID."""
        return cls._metadata_catalog.get(model_id)

    @classmethod
    def list_all_models(cls) -> List[ModelMetadata]:
        """List metadata for all registered models."""
        return list(cls._metadata_catalog.values())
