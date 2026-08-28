"""Machine Learning Interfaces & Base Estimator Contracts."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from app.domains.ml.schemas import (
    FeatureSet,
    ModelMetadata,
    PredictionRequest,
    PredictionResult,
    XAIExplanation,
)
from app.domains.ml.registry import ExtendedModelRegistry, ModelRegistry


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


__all__ = ["BasePredictionModel", "ModelRegistry", "ExtendedModelRegistry"]
