"""System Capabilities and Configuration Information Endpoint."""

from typing import Any, Dict
from fastapi import APIRouter, status
from app.core.config import settings

router = APIRouter(tags=["System Info"])


@router.get(
    "/system/info",
    summary="Get System Capabilities & Architecture Version",
    status_code=status.HTTP_200_OK,
    response_model=Dict[str, Any],
)
async def get_system_info() -> Dict[str, Any]:
    """Exposes system architecture capabilities and frozen configuration metadata."""
    return {
        "platform": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "architecture": {
            "type": "Modular Monolith",
            "deterministic_financial_engine": True,
            "evidence_grounding_enforced": True,
            "prompt_injection_defense": True,
        },
        "ai_spec": {
            "embedding_provider": settings.EMBEDDING_PROVIDER,
            "embedding_model": settings.EMBEDDING_MODEL,
            "embedding_dimension": settings.EMBEDDING_DIMENSION,
            "vector_store": "PostgreSQL 16 + pgvector",
        },
        "background_jobs": {
            "engine": "Celery + Redis",
            "states_supported": ["QUEUED", "RUNNING", "SUCCEEDED", "FAILED", "RETRYING", "CANCELLED"],
        },
        "security": {
            "password_hasher": "Argon2id",
            "session_type": "JWT",
            "tenant_isolation": "Server-Enforced (org_id + deal_id)",
        },
    }
