"""REST API Endpoints for Business Telemetry, External Connectors & Continuous Sync."""

import uuid
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import validate_deal_membership
from app.core.database import get_db
from app.domains.common.context import TenantContext
from app.domains.telemetry.connectors.registry import ConnectorRegistry
from app.domains.telemetry.schemas import (
    BusinessTelemetryChangeResponse,
    ConnectorMetadata,
    ConnectorProvider,
    DataFreshnessStatus,
    ExternalConnectionCreate,
    ExternalConnectionResponse,
    SyncRunResponse,
    TelemetrySummaryResponse,
)
from app.domains.telemetry.service import TelemetryService

router = APIRouter(tags=["telemetry"])


class SyncTriggerRequest(BaseModel):
    """Payload for manually triggering a connection sync."""
    incremental: bool = Field(default=True, description="Perform incremental cursor-based sync instead of full sync")
    run_inline: bool = Field(default=False, description="Run sync synchronously instead of scheduling background job")


# 1. Available Connectors Catalog
@router.get(
    "/deals/{deal_id}/telemetry/catalog",
    summary="List Supported Telemetry Connectors",
    status_code=status.HTTP_200_OK,
    response_model=List[ConnectorMetadata],
)
async def get_connector_catalog(
    deal_id: uuid.UUID,
    context: TenantContext = Depends(validate_deal_membership),
) -> List[ConnectorMetadata]:
    """Retrieve metadata, supported sync objects, and status for all available enterprise connectors."""
    return ConnectorRegistry.get_all_providers()


# 2. List Configured Connections
@router.get(
    "/deals/{deal_id}/telemetry/connections",
    summary="List Configured External Connections",
    status_code=status.HTTP_200_OK,
    response_model=List[ExternalConnectionResponse],
)
async def list_connections(
    deal_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    context: TenantContext = Depends(validate_deal_membership),
) -> List[ExternalConnectionResponse]:
    """List all external telemetry connections configured for this deal with safe masked credentials."""
    service = TelemetryService(db)
    return await service.list_connections(deal_id=deal_id, organization_id=context.organization_id)


# 3. Connect New System
@router.post(
    "/deals/{deal_id}/telemetry/connections",
    summary="Connect External Telemetry Provider",
    status_code=status.HTTP_201_CREATED,
    response_model=ExternalConnectionResponse,
)
async def create_connection(
    deal_id: uuid.UUID,
    payload: ExternalConnectionCreate,
    db: AsyncSession = Depends(get_db),
    context: TenantContext = Depends(validate_deal_membership),
) -> ExternalConnectionResponse:
    """Connect and validate an external enterprise system (e.g., Salesforce CRM or QuickBooks Online)."""
    service = TelemetryService(db)
    try:
        connection = await service.create_connection(
            deal_id=deal_id,
            organization_id=context.organization_id,
            user_id=context.user_id,
            payload=payload,
        )
        return connection
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# 4. Get Connection Details
@router.get(
    "/deals/{deal_id}/telemetry/connections/{connection_id}",
    summary="Get External Connection Details",
    status_code=status.HTTP_200_OK,
    response_model=ExternalConnectionResponse,
)
async def get_connection(
    deal_id: uuid.UUID,
    connection_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    context: TenantContext = Depends(validate_deal_membership),
) -> ExternalConnectionResponse:
    """Get connection details, status, and freshness badge."""
    service = TelemetryService(db)
    conn = await service.get_connection(
        connection_id=connection_id,
        deal_id=deal_id,
        organization_id=context.organization_id,
    )
    if not conn:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Connection {connection_id} not found in deal.",
        )
    return conn


# 5. Validate Connection Credentials
@router.post(
    "/deals/{deal_id}/telemetry/connections/{connection_id}/validate",
    summary="Validate External Connection Credentials",
    status_code=status.HTTP_200_OK,
)
async def validate_connection(
    deal_id: uuid.UUID,
    connection_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    context: TenantContext = Depends(validate_deal_membership),
) -> Dict[str, Any]:
    """Test live credentials and API connectivity against the external provider."""
    service = TelemetryService(db)
    conn = await service.get_connection(
        connection_id=connection_id,
        deal_id=deal_id,
        organization_id=context.organization_id,
    )
    if not conn:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Connection {connection_id} not found in deal.",
        )
    
    is_valid, err = await service.validate_connection(connection_id)
    return {
        "connection_id": str(connection_id),
        "is_valid": is_valid,
        "error": err,
    }


# 6. Trigger Synchronization
@router.post(
    "/deals/{deal_id}/telemetry/connections/{connection_id}/sync",
    summary="Trigger External Telemetry Sync",
    status_code=status.HTTP_202_ACCEPTED,
)
async def trigger_sync(
    deal_id: uuid.UUID,
    connection_id: uuid.UUID,
    payload: SyncTriggerRequest = SyncTriggerRequest(),
    db: AsyncSession = Depends(get_db),
    context: TenantContext = Depends(validate_deal_membership),
) -> Dict[str, Any]:
    """Trigger a cursor-based incremental or initial sync from the external provider."""
    service = TelemetryService(db)
    conn = await service.get_connection(
        connection_id=connection_id,
        deal_id=deal_id,
        organization_id=context.organization_id,
    )
    if not conn:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Connection {connection_id} not found in deal.",
        )

    result = await service.trigger_sync(
        connection_id=connection_id,
        incremental=payload.incremental,
        run_inline=payload.run_inline,
    )
    return result


# 7. Disconnect / Remove Connection
@router.delete(
    "/deals/{deal_id}/telemetry/connections/{connection_id}",
    summary="Disconnect External System",
    status_code=status.HTTP_200_OK,
)
async def disconnect_connection(
    deal_id: uuid.UUID,
    connection_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    context: TenantContext = Depends(validate_deal_membership),
) -> Dict[str, Any]:
    """Safely disconnect external system, wipe stored credentials, and mark connection revoked."""
    service = TelemetryService(db)
    conn = await service.get_connection(
        connection_id=connection_id,
        deal_id=deal_id,
        organization_id=context.organization_id,
    )
    if not conn:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Connection {connection_id} not found in deal.",
        )

    success = await service.disconnect(connection_id)
    return {
        "connection_id": str(connection_id),
        "status": "DISCONNECTED",
        "success": success,
    }


# 8. Sync Run History
@router.get(
    "/deals/{deal_id}/telemetry/connections/{connection_id}/sync-runs",
    summary="Get Connection Sync Runs",
    status_code=status.HTTP_200_OK,
    response_model=List[SyncRunResponse],
)
async def get_sync_runs(
    deal_id: uuid.UUID,
    connection_id: uuid.UUID,
    limit: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    context: TenantContext = Depends(validate_deal_membership),
) -> List[SyncRunResponse]:
    """Retrieve audit history of synchronization runs for a connection."""
    service = TelemetryService(db)
    conn = await service.get_connection(
        connection_id=connection_id,
        deal_id=deal_id,
        organization_id=context.organization_id,
    )
    if not conn:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Connection {connection_id} not found in deal.",
        )

    return await service.get_sync_runs(connection_id=connection_id, limit=limit)


# 9. Aggregated Telemetry Summary
@router.get(
    "/deals/{deal_id}/telemetry/summary",
    summary="Get Aggregated Business Telemetry Summary",
    status_code=status.HTTP_200_OK,
    response_model=TelemetrySummaryResponse,
)
async def get_telemetry_summary(
    deal_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    context: TenantContext = Depends(validate_deal_membership),
) -> TelemetrySummaryResponse:
    """Retrieve aggregated telemetry metrics, ARR, expenses, freshness status, and connection health."""
    service = TelemetryService(db)
    return await service.get_telemetry_summary(deal_id=deal_id, organization_id=context.organization_id)


# 10. Detected Changes & Drift Alerts
@router.get(
    "/deals/{deal_id}/telemetry/changes",
    summary="Get Detected Telemetry Changes & Drift Alerts",
    status_code=status.HTTP_200_OK,
    response_model=List[BusinessTelemetryChangeResponse],
)
async def get_detected_changes(
    deal_id: uuid.UUID,
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    context: TenantContext = Depends(validate_deal_membership),
) -> List[BusinessTelemetryChangeResponse]:
    """Retrieve detected metric changes, thesis drift warnings, and telemetry variances."""
    service = TelemetryService(db)
    return await service.get_detected_changes(deal_id=deal_id, organization_id=context.organization_id, limit=limit)
