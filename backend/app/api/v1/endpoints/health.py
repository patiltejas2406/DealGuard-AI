"""Health Check and Readiness Probes."""

from datetime import datetime, timezone
from typing import Any, Dict
from fastapi import APIRouter, status
from app.core.config import settings
from app.core.database import check_database_health

router = APIRouter(tags=["Health & Monitoring"])


@router.get(
    "/health",
    summary="System Liveness Probe",
    status_code=status.HTTP_200_OK,
    response_model=Dict[str, Any],
)
async def liveness_check() -> Dict[str, Any]:
    """Lightweight liveness probe indicating the HTTP server is responsive."""
    return {
        "status": "ok",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get(
    "/health/ready",
    summary="System Readiness Probe",
    status_code=status.HTTP_200_OK,
    response_model=Dict[str, Any],
)
async def readiness_check() -> Dict[str, Any]:
    """Comprehensive readiness probe checking downstream dependencies (Postgres)."""
    db_healthy = await check_database_health()
    all_ready = db_healthy

    return {
        "status": "ready" if all_ready else "degraded",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "dependencies": {
            "database": "connected" if db_healthy else "disconnected",
            "storage_provider": settings.STORAGE_PROVIDER,
            "embedding_provider": settings.EMBEDDING_PROVIDER,
        },
    }
