"""REST API Endpoints for Machine Learning Architecture, Inference & Explainability."""

import uuid
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_tenant_context, require_permission, validate_deal_membership
from app.domains.auth.permissions import PERM_ANALYSIS_RUN, PERM_DEALS_READ
from app.domains.common.context import TenantContext
from app.domains.deals.models import Deal
from app.domains.ml.registry import ExtendedModelRegistry
from app.domains.ml.schemas import ModelMetadata, PredictionResult, TrainingRun
from app.domains.ml.service import MLPredictionService

router = APIRouter(tags=["ml"])


class DealPredictRequest(BaseModel):
    """Payload for executing an ML prediction on a deal workspace."""
    model_id: str
    features_override: Optional[Dict[str, Any]] = None


class ModelMetricsResponse(BaseModel):
    """Evaluation metrics and baseline comparison response."""
    model_id: str
    task_type: str
    status: str
    evaluation_metrics: Dict[str, Any]
    baseline_metrics: Optional[Dict[str, Any]] = None


@router.get(
    "/ml/models",
    summary="List Registered ML Models",
    status_code=status.HTTP_200_OK,
    response_model=List[ModelMetadata],
    dependencies=[Depends(require_permission(PERM_DEALS_READ))],
)
async def list_ml_models(
    context: TenantContext = Depends(get_tenant_context),
) -> List[ModelMetadata]:
    """List all registered production machine learning model architectures and evaluation metrics."""
    return ExtendedModelRegistry.list_all_models()


@router.get(
    "/ml/models/{model_id}",
    summary="Get ML Model Metadata",
    status_code=status.HTTP_200_OK,
    response_model=ModelMetadata,
    dependencies=[Depends(require_permission(PERM_DEALS_READ))],
)
async def get_ml_model(
    model_id: str,
    context: TenantContext = Depends(get_tenant_context),
) -> ModelMetadata:
    """Retrieve detailed architecture, features, and evaluation metrics for a specific ML model."""
    meta = ExtendedModelRegistry.get_metadata(model_id)
    if not meta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ML Model '{model_id}' is not registered in the model catalog.",
        )
    return meta


@router.get(
    "/ml/models/{model_id}/metrics",
    summary="Get ML Model Evaluation Metrics & Baselines",
    status_code=status.HTTP_200_OK,
    response_model=ModelMetricsResponse,
    dependencies=[Depends(require_permission(PERM_DEALS_READ))],
)
async def get_ml_model_metrics(
    model_id: str,
    context: TenantContext = Depends(get_tenant_context),
) -> ModelMetricsResponse:
    """Retrieve test evaluation metrics and statistical baseline comparison."""
    meta = ExtendedModelRegistry.get_metadata(model_id)
    if not meta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ML Model '{model_id}' is not registered in the model catalog.",
        )

    trained = ExtendedModelRegistry.get_trained_model(model_id)
    base_metrics = trained.baseline_metrics if trained else None

    return ModelMetricsResponse(
        model_id=meta.model_id,
        task_type=meta.task_type.value,
        status=meta.status.value,
        evaluation_metrics=meta.evaluation_metrics,
        baseline_metrics=base_metrics,
    )


@router.get(
    "/ml/training-runs",
    summary="List ML Model Training Runs",
    status_code=status.HTTP_200_OK,
    response_model=List[TrainingRun],
    dependencies=[Depends(require_permission(PERM_DEALS_READ))],
)
async def list_training_runs(
    context: TenantContext = Depends(get_tenant_context),
) -> List[TrainingRun]:
    """List historical reproducible model training runs and parameter lineages."""
    return ExtendedModelRegistry.list_training_runs()


@router.get(
    "/ml/predictions/{prediction_id}",
    summary="Get Prediction Lineage and SHAP Explanation",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_permission(PERM_DEALS_READ))],
)
async def get_prediction_record(
    prediction_id: uuid.UUID,
    context: TenantContext = Depends(get_tenant_context),
    session: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Retrieve a persisted ML inference record with exact SHAP feature explanations."""
    service = MLPredictionService(session)
    pred = await service.get_prediction_record(context, prediction_id)
    if not pred:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prediction record '{prediction_id}' not found.",
        )

    return {
        "id": str(pred.id),
        "model_id": pred.model_id,
        "model_version": pred.model_version,
        "task_type": pred.task_type,
        "predicted_value": pred.predicted_value_json,
        "prediction_confidence": pred.prediction_confidence,
        "features": pred.features_json,
        "explanation": pred.explanation_json,
        "created_at": pred.created_at.isoformat() if pred.created_at else None,
    }


@router.post(
    "/deals/{deal_id}/ml/predict",
    summary="Execute ML Prediction for Deal Workspace",
    status_code=status.HTTP_200_OK,
    response_model=PredictionResult,
    dependencies=[Depends(require_permission(PERM_ANALYSIS_RUN))],
)
async def predict_deal_ml(
    deal_id: uuid.UUID,
    payload: DealPredictRequest,
    context: TenantContext = Depends(get_tenant_context),
    session: AsyncSession = Depends(get_db),
    deal: Deal = Depends(validate_deal_membership),
) -> PredictionResult:
    """
    Execute real ML inference for a target deal, compute exact SHAP attributions,
    and persist audit record.
    """
    service = MLPredictionService(session)
    try:
        result = await service.predict(
            context=context,
            deal_id=deal_id,
            model_id=payload.model_id,
            features_override=payload.features_override,
        )
        return result
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
