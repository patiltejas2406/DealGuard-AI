"""REST API Endpoints for Machine Learning Architecture & Models."""

from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_tenant_context
from app.domains.common.context import TenantContext
from app.domains.ml.interfaces import ModelRegistry
from app.domains.ml.schemas import ModelMetadata

router = APIRouter(prefix="/ml", tags=["ml"])


@router.get(
    "/models",
    summary="List Registered ML Models",
    status_code=status.HTTP_200_OK,
    response_model=List[ModelMetadata],
)
async def list_ml_models(
    context: TenantContext = Depends(get_tenant_context),
) -> List[ModelMetadata]:
    """List all registered production machine learning model architectures and evaluation metrics."""
    return ModelRegistry.list_all_models()


@router.get(
    "/models/{model_id}",
    summary="Get ML Model Metadata",
    status_code=status.HTTP_200_OK,
    response_model=ModelMetadata,
)
async def get_ml_model(
    model_id: str,
    context: TenantContext = Depends(get_tenant_context),
) -> ModelMetadata:
    """Retrieve detailed architecture, features, and evaluation metrics for a specific ML model."""
    meta = ModelRegistry.get_metadata(model_id)
    if not meta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ML Model '{model_id}' is not registered in the model catalog.",
        )
    return meta
