"""Synchronization Engine Orchestrating Connector Execution, Idempotent Upserts & Change Detection."""

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.telemetry.connectors.base import BaseConnector, SyncBatchResult
from app.domains.telemetry.connectors.registry import ConnectorRegistry
from app.domains.telemetry.models import ExternalConnection, SyncRun
from app.domains.telemetry.repository import TelemetryRepository
from app.domains.telemetry.schemas import (
    ConnectionStatus,
    ConnectorProvider,
    DataFreshnessStatus,
    SyncStatus,
    TelemetryChangeSeverity,
)
from app.domains.telemetry.security import CredentialVault

logger = logging.getLogger(__name__)


class TelemetrySyncEngine:
    """Core synchronization engine for continuous external business telemetry ingestion."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = TelemetryRepository(session)

    async def execute_sync(
        self,
        connection_id: Optional[uuid.UUID] = None,
        organization_id: Optional[uuid.UUID] = None,
        is_full_sync: bool = False,
        incremental: Optional[bool] = None,
        **kwargs: Any,
    ) -> SyncRun:
        """Execute an automated or on-demand synchronization run for an authorized connection."""
        if incremental is not None:
            is_full_sync = not incremental

        # In case called positionally as execute_sync(org_id, conn_id, ...)
        if connection_id and organization_id and isinstance(organization_id, uuid.UUID) and isinstance(connection_id, uuid.UUID):
            # Check if connection_id was actually org_id
            conn_check = await self.session.get(ExternalConnection, connection_id)
            if not conn_check:
                # Inverted positional args: (org_id, conn_id)
                actual_conn = await self.session.get(ExternalConnection, organization_id)
                if actual_conn:
                    organization_id = connection_id
                    connection_id = actual_conn.id

        if organization_id is None:
            conn_entity = await self.session.get(ExternalConnection, connection_id)
            if not conn_entity:
                raise ValueError(f"Connection '{connection_id}' not found.")
            organization_id = conn_entity.organization_id
            conn = conn_entity
        else:
            conn = await self.repo.get_connection_by_id(organization_id, connection_id)

        if not conn:
            raise ValueError(f"Connection '{connection_id}' not found for tenant.")

        if not conn.is_active:
            raise ValueError(f"Connection '{conn.connection_name}' is currently disabled.")

        deal_id = conn.deal_id
        if not deal_id:
            raise ValueError("Telemetry synchronization requires an associated deal context.")

        # 1. Initialize SyncRun record
        sync_run = await self.repo.create_sync_run(
            organization_id=organization_id,
            connection_id=connection_id,
            deal_id=deal_id,
            is_full_sync=is_full_sync,
        )
        await self.session.commit()

        # Update connection status to SYNCING
        await self.repo.update_connection_status(
            organization_id=organization_id,
            connection_id=connection_id,
            connection_status=ConnectionStatus.SYNCING.value,
            last_attempted_sync=datetime.now(timezone.utc),
        )
        await self.session.commit()

        # 2. Decrypt credentials and initialize connector
        try:
            credentials = CredentialVault.decrypt_credentials(conn.encrypted_credentials)
            provider_enum = ConnectorProvider(conn.provider)
            connector = ConnectorRegistry.create_connector(
                provider=provider_enum,
                credentials=credentials,
                deal_id=str(deal_id),
                organization_id=str(organization_id),
            )
        except Exception as exc:
            err_msg = f"Failed to initialize connector for {conn.provider}: {str(exc)}"
            logger.error(err_msg, exc_info=True)
            await self.repo.update_sync_run(
                organization_id=organization_id,
                sync_run_id=sync_run.id,
                status=SyncStatus.FAILED.value,
                records_fetched=0,
                records_normalized=0,
                records_upserted=0,
                records_failed=0,
                error_message=err_msg,
            )
            await self.repo.update_connection_status(
                organization_id=organization_id,
                connection_id=connection_id,
                connection_status=ConnectionStatus.ERROR.value,
                error_message=err_msg,
            )
            await self.session.commit()
            return sync_run

        # 3. Retrieve incremental checkpoints if not a forced full sync
        checkpoints: Dict[str, str] = {}
        if not is_full_sync:
            for entity_key in ["LastModifiedDate", "SystemModstamp", "LastUpdatedTime"]:
                val = await self.repo.get_checkpoint(connection_id, entity_key)
                if val:
                    checkpoints[entity_key] = val

        # 4. Ingest raw batches from external provider
        try:
            if is_full_sync or not checkpoints:
                batch_result = await connector.initial_sync(batch_size=200)
            else:
                batch_result = await connector.incremental_sync(checkpoints=checkpoints, batch_size=200)
        except Exception as exc:
            err_msg = f"Connector API fetch exception: {str(exc)}"
            logger.error(err_msg, exc_info=True)
            await self.repo.update_sync_run(
                organization_id=organization_id,
                sync_run_id=sync_run.id,
                status=SyncStatus.FAILED.value,
                records_fetched=0,
                records_normalized=0,
                records_upserted=0,
                records_failed=0,
                error_message=err_msg,
            )
            await self.repo.update_connection_status(
                organization_id=organization_id,
                connection_id=connection_id,
                connection_status=ConnectionStatus.ERROR.value,
                error_message=err_msg,
            )
            await self.session.commit()
            return sync_run

        # 5. Capture pre-sync baseline metrics for change detection
        pre_sync_metrics = await self._calculate_telemetry_snapshot(organization_id, deal_id)

        # 6. Idempotently upsert canonical records inside transaction boundary
        upserted_count = 0
        failed_count = batch_result.records_failed
        breakdown = {
            "customers": 0,
            "opportunities": 0,
            "revenue_events": 0,
            "expenses": 0,
        }

        # A. Upsert Customers
        for cust in batch_result.customers:
            try:
                await self.repo.upsert_customer(organization_id, deal_id, cust)
                upserted_count += 1
                breakdown["customers"] += 1
            except Exception as exc:
                failed_count += 1
                logger.warning(f"Error upserting customer {cust.external_id}: {str(exc)}")

        # B. Upsert Opportunities
        for opp in batch_result.opportunities:
            try:
                await self.repo.upsert_opportunity(organization_id, deal_id, opp)
                upserted_count += 1
                breakdown["opportunities"] += 1
            except Exception as exc:
                failed_count += 1
                logger.warning(f"Error upserting opportunity {opp.external_id}: {str(exc)}")

        # C. Upsert Revenue Events
        for rev in batch_result.revenue_events:
            try:
                await self.repo.upsert_revenue_event(organization_id, deal_id, rev)
                upserted_count += 1
                breakdown["revenue_events"] += 1
            except Exception as exc:
                failed_count += 1
                logger.warning(f"Error upserting revenue event {rev.external_id}: {str(exc)}")

        # D. Upsert Expenses
        for exp in batch_result.expenses:
            try:
                await self.repo.upsert_expense(organization_id, deal_id, exp)
                upserted_count += 1
                breakdown["expenses"] += 1
            except Exception as exc:
                failed_count += 1
                logger.warning(f"Error upserting expense {exp.external_id}: {str(exc)}")

        # 7. Update checkpoint cursors
        for cp_key, cp_val in batch_result.new_checkpoints.items():
            await self.repo.set_checkpoint(organization_id, connection_id, cp_key, cp_val)

        # 8. Run Continuous Intelligence Change Detection
        post_sync_metrics = await self._calculate_telemetry_snapshot(organization_id, deal_id)
        await self._detect_telemetry_changes(
            organization_id=organization_id,
            deal_id=deal_id,
            provider=conn.provider,
            pre_metrics=pre_sync_metrics,
            post_metrics=post_sync_metrics,
        )

        # 9. Update SyncRun and Connection states
        final_status = (
            SyncStatus.COMPLETED.value
            if failed_count == 0
            else (SyncStatus.PARTIAL_SUCCESS.value if upserted_count > 0 else SyncStatus.FAILED.value)
        )
        now_dt = datetime.now(timezone.utc)

        await self.repo.update_sync_run(
            organization_id=organization_id,
            sync_run_id=sync_run.id,
            status=final_status,
            records_fetched=batch_result.records_fetched,
            records_normalized=len(batch_result.customers)
            + len(batch_result.opportunities)
            + len(batch_result.revenue_events)
            + len(batch_result.expenses),
            records_upserted=upserted_count,
            records_failed=failed_count,
            error_message="; ".join(batch_result.errors) if batch_result.errors else None,
            entity_breakdown=breakdown,
        )

        capabilities = await connector.discover_capabilities()
        await self.repo.update_connection_status(
            organization_id=organization_id,
            connection_id=connection_id,
            connection_status=ConnectionStatus.CONNECTED.value,
            auth_status="AUTHENTICATED",
            capabilities=capabilities,
            last_successful_sync=now_dt if upserted_count > 0 else conn.last_successful_sync,
            data_freshness_status=DataFreshnessStatus.LIVE.value,
            error_message=None if failed_count == 0 else f"{failed_count} records failed normalization",
        )

        await self.session.commit()
        return sync_run

    # --- Change Detection Engine ---

    async def _calculate_telemetry_snapshot(
        self, organization_id: uuid.UUID, deal_id: uuid.UUID
    ) -> Dict[str, float]:
        """Compute aggregated operational metrics from canonical records."""
        customers = await self.repo.get_customers_for_deal(organization_id, deal_id)
        opportunities = await self.repo.get_opportunities_for_deal(organization_id, deal_id)
        revenues = await self.repo.get_revenue_events_for_deal(organization_id, deal_id)
        expenses = await self.repo.get_expenses_for_deal(organization_id, deal_id)

        total_arr = sum(c.arr_usd for c in customers)
        total_pipeline = sum(o.amount_usd for o in opportunities if not o.is_closed)
        weighted_pipeline = sum(o.expected_revenue_usd for o in opportunities if not o.is_closed)
        realized_revenue = sum(r.amount_usd for r in revenues if r.status == "PAID")
        realized_expenses = sum(e.amount_usd for e in expenses)
        ebitda_runrate = realized_revenue - realized_expenses

        return {
            "total_arr": round(total_arr, 2),
            "total_pipeline": round(total_pipeline, 2),
            "weighted_pipeline": round(weighted_pipeline, 2),
            "realized_revenue": round(realized_revenue, 2),
            "realized_expenses": round(realized_expenses, 2),
            "ebitda_runrate": round(ebitda_runrate, 2),
        }

    async def _detect_telemetry_changes(
        self,
        organization_id: uuid.UUID,
        deal_id: uuid.UUID,
        provider: str,
        pre_metrics: Dict[str, float],
        post_metrics: Dict[str, float],
    ) -> None:
        """Evaluate metric drift against pre-deal acquisition thesis and value creation initiatives."""
        # 1. Total ARR change
        arr_pre = pre_metrics.get("total_arr", 0.0)
        arr_post = post_metrics.get("total_arr", 0.0)
        if arr_pre > 0 and arr_post > 0 and abs(arr_post - arr_pre) / arr_pre > 0.05:
            delta = arr_post - arr_pre
            severity = TelemetryChangeSeverity.HIGH.value if delta < 0 else TelemetryChangeSeverity.MEDIUM.value
            await self.repo.log_telemetry_change(
                organization_id=organization_id,
                deal_id=deal_id,
                metric_name="TOTAL_CONTRACTUAL_ARR",
                previous_value=arr_pre,
                new_value=arr_post,
                severity=severity,
                affected_kpi="ARR_GROWTH_RATE",
                affected_thesis_pillar="CUSTOMER",
                affected_initiatives=["Customer Retention & Health Tracking"],
                suggested_agent_id="customer_retention_agent",
                evidence_source=f"{provider} Account Ledger Ingestion",
            )

        # 2. Realized Revenue change
        rev_pre = pre_metrics.get("realized_revenue", 0.0)
        rev_post = post_metrics.get("realized_revenue", 0.0)
        if rev_pre > 0 and rev_post > 0 and abs(rev_post - rev_pre) / rev_pre > 0.08:
            delta = rev_post - rev_pre
            severity = TelemetryChangeSeverity.CRITICAL.value if delta < -100000 else TelemetryChangeSeverity.HIGH.value
            await self.repo.log_telemetry_change(
                organization_id=organization_id,
                deal_id=deal_id,
                metric_name="REALIZED_ACCOUNTING_REVENUE",
                previous_value=rev_pre,
                new_value=rev_post,
                severity=severity,
                affected_kpi="REVENUE_REALIZATION_RATE",
                affected_thesis_pillar="REVENUE",
                affected_initiatives=["Invoiced Revenue Optimization"],
                suggested_agent_id="revenue_optimization_agent",
                evidence_source=f"{provider} Billing & Invoices Ledger",
            )

        # 3. Pipeline Expansion change
        pipe_pre = pre_metrics.get("weighted_pipeline", 0.0)
        pipe_post = post_metrics.get("weighted_pipeline", 0.0)
        if pipe_pre > 0 and pipe_post > 0 and abs(pipe_post - pipe_pre) / pipe_pre > 0.10:
            await self.repo.log_telemetry_change(
                organization_id=organization_id,
                deal_id=deal_id,
                metric_name="WEIGHTED_SALES_PIPELINE",
                previous_value=pipe_pre,
                new_value=pipe_post,
                severity=TelemetryChangeSeverity.MEDIUM.value,
                affected_kpi="PIPELINE_CONVERSION_RATE",
                affected_thesis_pillar="GROWTH",
                affected_initiatives=["Organic Sales Acceleration"],
                suggested_agent_id="growth_intelligence_agent",
                evidence_source=f"{provider} Opportunity Pipeline Ingestion",
            )
