"""Machine Learning Architecture, Datasets, Training Runs & Prediction Persistence Models."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, Optional
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domains.common.models import TenantScopedModel
from app.domains.common.types import CompatibleJSON

if TYPE_CHECKING:
    from app.domains.deals.models import Deal


class MLDatasetRecord(TenantScopedModel):
    """Registry record tracking an ML training or benchmark dataset."""
    __tablename__ = "ml_datasets"

    dataset_key: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    version: Mapped[str] = mapped_column(String(30), default="1.0.0", nullable=False)
    source: Mapped[str] = mapped_column(String(255), nullable=False)
    task_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    target_name: Mapped[str] = mapped_column(String(100), nullable=False)
    row_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    feature_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    data_checksum: Mapped[str] = mapped_column(String(64), nullable=False)
    is_benchmark: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    metadata_json: Mapped[Dict[str, Any]] = mapped_column(CompatibleJSON, default=dict, nullable=False)

    __table_args__ = (
        Index("ix_ml_datasets_org_task", "organization_id", "task_type"),
    )


class MLTrainingRunRecord(TenantScopedModel):
    """Audit record of an automated or triggered ML training execution."""
    __tablename__ = "ml_training_runs"

    model_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    dataset_key: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(30), default="COMPLETED", nullable=False)
    parameters_json: Mapped[Dict[str, Any]] = mapped_column(CompatibleJSON, default=dict, nullable=False)
    metrics_json: Mapped[Dict[str, Any]] = mapped_column(CompatibleJSON, default=dict, nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    duration_ms: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    __table_args__ = (
        Index("ix_ml_training_runs_model", "organization_id", "model_id"),
    )


class MLModelRecord(TenantScopedModel):
    """Registry record tracking an ML model architecture, version, and metrics."""
    __tablename__ = "ml_models"

    model_key: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    version: Mapped[str] = mapped_column(String(30), default="1.0.0", nullable=False)
    task_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    framework: Mapped[str] = mapped_column(String(50), default="scikit-learn", nullable=False)
    training_dataset_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    metrics_json: Mapped[Dict[str, Any]] = mapped_column(CompatibleJSON, default=dict, nullable=False)
    hyperparameters_json: Mapped[Dict[str, Any]] = mapped_column(CompatibleJSON, default=dict, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="REGISTERED", nullable=False)

    __table_args__ = (
        Index("ix_ml_models_org_task", "organization_id", "task_type"),
    )


class MLPredictionRecord(TenantScopedModel):
    """Audit record of an ML prediction inference with XAI explainability metadata."""
    __tablename__ = "ml_predictions"

    model_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    model_version: Mapped[str] = mapped_column(String(30), default="1.0.0", nullable=False)
    deal_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("deals.id", ondelete="CASCADE"), nullable=True, index=True
    )
    task_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    predicted_value_json: Mapped[Any] = mapped_column(CompatibleJSON, nullable=False)
    prediction_confidence: Mapped[float] = mapped_column(Float, default=0.90, nullable=False)
    features_json: Mapped[Dict[str, Any]] = mapped_column(CompatibleJSON, default=dict, nullable=False)
    explanation_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(CompatibleJSON, nullable=True)

    __table_args__ = (
        Index("ix_ml_preds_lookup", "organization_id", "deal_id", "task_type"),
    )
