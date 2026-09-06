"""Telemetry Service Layer Managing External Connections and Canonical Telemetry Posture."""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.telemetry.connectors.registry import ConnectorRegistry
from app.domains.telemetry.models import BusinessCustomer, BusinessOpportunity, BusinessRevenueEvent, ExternalConnection, SyncRun
from app.domains.telemetry.repository import TelemetryRepository
from app.domains.telemetry.schemas import (
    ConnectionCredentials,
    ConnectionStatus,
    ConnectionValidationResult,
    ConnectorProvider,
    DataFreshnessStatus,
    ExternalConnectionCreate,
    ExternalConnectionResponse,
    SyncRunResponse,
    TelemetryChangeResponse,
    TelemetrySummaryResponse,
)
from app.domains.telemetry.security import CredentialVault
from app.domains.telemetry.tasks import dispatch_telemetry_sync


class TelemetryService:
    """Service handling third-party integrations, validation, sync triggers, and telemetry summaries."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = TelemetryRepository(session)

    async def register_connection(
        self,
        organization_id: uuid.UUID,
        deal_id: Optional[uuid.UUID],
        payload: ExternalConnectionCreate,
    ) -> ExternalConnectionResponse:
        """Register a new external connection with encrypted credentials."""
        conn = await self.repo.create_connection(
            organization_id=organization_id,
            deal_id=deal_id,
            provider=payload.provider.value,
            connection_name=payload.connection_name,
            credentials=payload.credentials,
            auto_sync_interval_hours=payload.auto_sync_interval_hours,
        )
        await self.session.commit()
        return self._to_response(conn)

    async def create_connection(
        self,
        organization_id: uuid.UUID,
        deal_id: Optional[uuid.UUID] = None,
        payload: Optional[ExternalConnectionCreate] = None,
        user_id: Optional[uuid.UUID] = None,
        **kwargs: Any,
    ) -> ExternalConnectionResponse:
        """Connect and register an external provider with symmetrically encrypted credentials (compatible alias)."""
        if payload is None:
            raise ValueError("payload is required")
        return await self.register_connection(
            organization_id=organization_id,
            deal_id=deal_id,
            payload=payload,
        )

    async def get_connection(
        self,
        organization_id: uuid.UUID,
        connection_id: uuid.UUID,
    ) -> Optional[ExternalConnectionResponse]:
        """Fetch connection by ID with masked secrets."""
        conn = await self.repo.get_connection_by_id(organization_id, connection_id)
        if not conn:
            return None
        return self._to_response(conn)

    async def list_connections(
        self,
        organization_id: uuid.UUID,
        deal_id: Optional[uuid.UUID] = None,
    ) -> List[ExternalConnectionResponse]:
        """List connections for tenant and optionally deal."""
        conns = await self.repo.list_connections(organization_id, deal_id)
        return [self._to_response(c) for c in conns]

    async def validate_connection(
        self,
        organization_id: uuid.UUID,
        connection_id: uuid.UUID,
    ) -> ConnectionValidationResult:
        """Probe external vendor API to test credentials and retrieve capabilities."""
        conn = await self.repo.get_connection_by_id(organization_id, connection_id)
        if not conn:
            raise ValueError(f"Connection '{connection_id}' not found.")

        credentials = CredentialVault.decrypt_credentials(conn.encrypted_credentials)
        provider_enum = ConnectorProvider(conn.provider)
        connector = ConnectorRegistry.create_connector(
            provider=provider_enum,
            credentials=credentials,
            deal_id=str(conn.deal_id) if conn.deal_id else None,
            organization_id=str(organization_id),
        )

        validation_res = await connector.validate_connection()
        new_status = ConnectionStatus.CONNECTED.value if validation_res.is_valid else ConnectionStatus.ERROR.value

        await self.repo.update_connection_status(
            organization_id=organization_id,
            connection_id=connection_id,
            connection_status=new_status,
            capabilities=validation_res.discovered_capabilities if validation_res.is_valid else conn.capabilities,
            error_message=None if validation_res.is_valid else validation_res.message,
        )
        await self.session.commit()
        return validation_res

    async def trigger_sync(
        self,
        organization_id: uuid.UUID,
        connection_id: uuid.UUID,
        is_full_sync: bool = False,
        run_inline: bool = True,
    ) -> Dict[str, Any]:
        """Trigger an incremental or full synchronization run."""
        conn = await self.repo.get_connection_by_id(organization_id, connection_id)
        if not conn:
            raise ValueError(f"Connection '{connection_id}' not found.")

        if not conn.deal_id:
            raise ValueError("Connection is not associated with an active deal.")

        job = await dispatch_telemetry_sync(
            session=self.session,
            organization_id=organization_id,
            deal_id=conn.deal_id,
            connection_id=connection_id,
            is_full_sync=is_full_sync,
            run_inline=run_inline,
        )
        return {
            "message": "Telemetry synchronization dispatched successfully.",
            "job_id": str(job.id),
            "connection_id": str(connection_id),
            "is_full_sync": is_full_sync,
            "status": job.status,
        }

    async def disconnect_connection(
        self,
        organization_id: uuid.UUID,
        connection_id: uuid.UUID,
    ) -> ExternalConnectionResponse:
        """Revoke credentials and disconnect external connection."""
        conn = await self.repo.get_connection_by_id(organization_id, connection_id)
        if not conn:
            raise ValueError(f"Connection '{connection_id}' not found.")

        try:
            credentials = CredentialVault.decrypt_credentials(conn.encrypted_credentials)
            provider_enum = ConnectorProvider(conn.provider)
            connector = ConnectorRegistry.create_connector(
                provider=provider_enum,
                credentials=credentials,
                deal_id=str(conn.deal_id) if conn.deal_id else None,
                organization_id=str(organization_id),
            )
            await connector.disconnect()
        except Exception:
            pass

        updated = await self.repo.update_connection_status(
            organization_id=organization_id,
            connection_id=connection_id,
            connection_status=ConnectionStatus.DISCONNECTED.value,
            auth_status="REVOKED",
        )
        await self.session.commit()
        return self._to_response(updated or conn)

    async def get_telemetry_summary(
        self,
        organization_id: uuid.UUID,
        deal_id: uuid.UUID,
    ) -> TelemetrySummaryResponse:
        """Compute consolidated real business telemetry overview."""
        connections = await self.repo.list_connections(organization_id, deal_id)
        customers = await self.repo.get_customers_for_deal(organization_id, deal_id)
        opportunities = await self.repo.get_opportunities_for_deal(organization_id, deal_id)
        revenues = await self.repo.get_revenue_events_for_deal(organization_id, deal_id)
        expenses = await self.repo.get_expenses_for_deal(organization_id, deal_id)
        unresolved_changes = await self.repo.list_telemetry_changes(organization_id, deal_id, unresolved_only=True)

        active_conns = [
            c for c in connections
            if c.connection_status in (ConnectionStatus.ACTIVE.value, ConnectionStatus.CONNECTED.value)
            and c.is_active
        ]
        providers = sorted(list({c.provider for c in connections}))

        # Determine overall freshness
        overall_freshness = DataFreshnessStatus.NOT_SYNCED
        latest_sync = max([c.last_successful_sync for c in connections if c.last_successful_sync], default=None)

        if latest_sync:
            if latest_sync.tzinfo is None:
                latest_sync = latest_sync.replace(tzinfo=timezone.utc)
            age_hours = (datetime.now(timezone.utc) - latest_sync).total_seconds() / 3600.0
            if age_hours < 1.0:
                overall_freshness = DataFreshnessStatus.LIVE
            elif age_hours < 24.0:
                overall_freshness = DataFreshnessStatus.RECENT
            else:
                overall_freshness = DataFreshnessStatus.STALE

        total_pipe = sum(o.amount_usd for o in opportunities if not o.is_closed)
        realized_rev = sum(r.amount_usd for r in revenues if r.status == "PAID")
        realized_exp = sum(e.amount_usd for e in expenses)
        ebitda_runrate = realized_rev - realized_exp

        return TelemetrySummaryResponse(
            deal_id=deal_id,
            active_connections_count=len(active_conns),
            connected_providers=providers,
            overall_freshness=overall_freshness,
            last_synced_at=latest_sync,
            customer_count=len(customers),
            total_pipeline_arr=round(total_pipe, 2),
            total_realized_revenue=round(realized_rev, 2),
            total_realized_expenses=round(realized_exp, 2),
            detected_ebitda_runrate=round(ebitda_runrate, 2),
            unresolved_telemetry_changes=len(unresolved_changes),
        )

    async def list_telemetry_changes(
        self,
        organization_id: uuid.UUID,
        deal_id: uuid.UUID,
        unresolved_only: bool = True,
    ) -> List[TelemetryChangeResponse]:
        """Fetch metric drift and strategic change detection alerts."""
        changes = await self.repo.list_telemetry_changes(organization_id, deal_id, unresolved_only=unresolved_only)
        return [TelemetryChangeResponse.model_validate(c) for c in changes]

    # --- Helper Mapping ---

    def _to_response(self, conn: ExternalConnection) -> ExternalConnectionResponse:
        """Convert ORM model to safe API response with masked credentials."""
        masked_url = None
        try:
            creds = CredentialVault.decrypt_credentials(conn.encrypted_credentials)
            if creds.instance_url:
                masked_url = creds.instance_url
        except Exception:
            pass

        return ExternalConnectionResponse(
            id=conn.id,
            organization_id=conn.organization_id,
            deal_id=conn.deal_id,
            provider=ConnectorProvider(conn.provider),
            connection_name=conn.connection_name,
            connection_status=ConnectionStatus(conn.connection_status),
            auth_status=conn.auth_status,  # type: ignore
            last_successful_sync=conn.last_successful_sync,
            last_attempted_sync=conn.last_attempted_sync,
            data_freshness_status=DataFreshnessStatus(conn.data_freshness_status)
            if conn.data_freshness_status in [d.value for d in DataFreshnessStatus]
            else DataFreshnessStatus.NOT_SYNCED,
            capabilities=conn.capabilities or [],
            auto_sync_interval_hours=conn.auto_sync_interval_hours,
            is_active=conn.is_active,
            created_at=conn.created_at,
            updated_at=conn.updated_at,
            error_message=conn.error_message,
            masked_instance_url=masked_url,
        )
