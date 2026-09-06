"""Repository Layer for External Connections, Sync State, and Canonical Telemetry."""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy import delete, desc, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.telemetry.models import (
    BusinessCustomer,
    BusinessExpense,
    BusinessOpportunity,
    BusinessRevenueEvent,
    BusinessTelemetryChange,
    ExternalConnection,
    ExternalObjectMapping,
    SyncCheckpoint,
    SyncRun,
)
from app.domains.telemetry.schemas import (
    CanonicalCustomer,
    CanonicalExpense,
    CanonicalOpportunity,
    CanonicalRevenueEvent,
    ConnectionCredentials,
    ConnectionStatus,
    DataFreshnessStatus,
    SyncStatus,
)
from app.domains.telemetry.security import CredentialVault


class TelemetryRepository:
    """Enterprise repository for external business telemetry with strict tenant isolation."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # --- Connection Management ---

    async def create_connection(
        self,
        organization_id: uuid.UUID,
        deal_id: Optional[uuid.UUID],
        provider: str,
        connection_name: str,
        credentials: ConnectionCredentials,
        auto_sync_interval_hours: int = 6,
    ) -> ExternalConnection:
        """Create a new external system connection with encrypted credentials."""
        encrypted = CredentialVault.encrypt_credentials(credentials)
        conn = ExternalConnection(
            organization_id=organization_id,
            deal_id=deal_id,
            provider=provider,
            connection_name=connection_name,
            encrypted_credentials=encrypted,
            connection_status=ConnectionStatus.ACTIVE.value,
            auth_status="AUTHENTICATED",
            auto_sync_interval_hours=auto_sync_interval_hours,
            capabilities=[],
        )
        self.session.add(conn)
        await self.session.flush()
        return conn

    async def get_connection_by_id(
        self,
        organization_id: uuid.UUID,
        connection_id: uuid.UUID,
    ) -> Optional[ExternalConnection]:
        """Fetch connection ensuring tenant ownership."""
        stmt = select(ExternalConnection).where(
            ExternalConnection.id == connection_id,
            ExternalConnection.organization_id == organization_id,
        )
        res = await self.session.execute(stmt)
        return res.scalars().first()

    async def list_connections(
        self,
        organization_id: uuid.UUID,
        deal_id: Optional[uuid.UUID] = None,
    ) -> List[ExternalConnection]:
        """List active connections filtered by organization and optionally deal."""
        stmt = select(ExternalConnection).where(
            ExternalConnection.organization_id == organization_id
        )
        if deal_id is not None:
            stmt = stmt.where(ExternalConnection.deal_id == deal_id)
        stmt = stmt.order_by(desc(ExternalConnection.created_at))
        res = await self.session.execute(stmt)
        return list(res.scalars().all())

    async def update_connection_status(
        self,
        organization_id: uuid.UUID,
        connection_id: uuid.UUID,
        connection_status: Optional[str] = None,
        auth_status: Optional[str] = None,
        capabilities: Optional[List[str]] = None,
        error_message: Optional[str] = None,
        last_attempted_sync: Optional[datetime] = None,
        last_successful_sync: Optional[datetime] = None,
        data_freshness_status: Optional[str] = None,
    ) -> Optional[ExternalConnection]:
        """Update operational status and sync metadata of a connection."""
        conn = await self.get_connection_by_id(organization_id, connection_id)
        if not conn:
            return None

        if connection_status is not None:
            conn.connection_status = connection_status
        if auth_status is not None:
            conn.auth_status = auth_status
        if capabilities is not None:
            conn.capabilities = capabilities
        if error_message is not None:
            conn.error_message = error_message
        if last_attempted_sync is not None:
            conn.last_attempted_sync = last_attempted_sync
        if last_successful_sync is not None:
            conn.last_successful_sync = last_successful_sync
        if data_freshness_status is not None:
            conn.data_freshness_status = data_freshness_status

        conn.updated_at = datetime.now(timezone.utc)
        await self.session.flush()
        return conn

    # --- Sync Runs & Checkpoints ---

    async def create_sync_run(
        self,
        organization_id: uuid.UUID,
        connection_id: uuid.UUID,
        deal_id: Optional[uuid.UUID],
        is_full_sync: bool = False,
    ) -> SyncRun:
        """Create a new tracked sync execution log."""
        run = SyncRun(
            organization_id=organization_id,
            connection_id=connection_id,
            deal_id=deal_id,
            status=SyncStatus.RUNNING.value,
            is_full_sync=is_full_sync,
            records_fetched=0,
            records_normalized=0,
            records_upserted=0,
            records_failed=0,
            started_at=datetime.now(timezone.utc),
        )
        self.session.add(run)
        await self.session.flush()
        return run

    async def update_sync_run(
        self,
        organization_id: uuid.UUID,
        sync_run_id: uuid.UUID,
        status: str,
        records_fetched: int,
        records_normalized: int,
        records_upserted: int,
        records_failed: int,
        error_message: Optional[str] = None,
        entity_breakdown: Optional[Dict[str, Any]] = None,
    ) -> Optional[SyncRun]:
        """Complete or update a sync run execution record."""
        stmt = select(SyncRun).where(
            SyncRun.id == sync_run_id,
            SyncRun.organization_id == organization_id,
        )
        res = await self.session.execute(stmt)
        run = res.scalars().first()
        if not run:
            return None

        now = datetime.now(timezone.utc)
        run.status = status
        run.records_fetched = records_fetched
        run.records_normalized = records_normalized
        run.records_upserted = records_upserted
        run.records_failed = records_failed
        run.completed_at = now
        run.error_message = error_message
        if entity_breakdown is not None:
            run.entity_breakdown = entity_breakdown

        if run.started_at:
            delta = now - run.started_at
            run.duration_seconds = round(delta.total_seconds(), 2)

        await self.session.flush()
        return run

    async def get_checkpoint(
        self,
        connection_id: uuid.UUID,
        entity_type: str,
    ) -> Optional[str]:
        """Fetch the high-water-mark incremental sync cursor."""
        stmt = select(SyncCheckpoint.cursor_value).where(
            SyncCheckpoint.connection_id == connection_id,
            SyncCheckpoint.entity_type == entity_type,
        )
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def set_checkpoint(
        self,
        organization_id: uuid.UUID,
        connection_id: uuid.UUID,
        entity_type: str,
        cursor_value: str,
    ) -> None:
        """Upsert the incremental sync cursor checkpoint."""
        stmt = select(SyncCheckpoint).where(
            SyncCheckpoint.connection_id == connection_id,
            SyncCheckpoint.entity_type == entity_type,
        )
        res = await self.session.execute(stmt)
        cp = res.scalars().first()
        if cp:
            cp.cursor_value = cursor_value
            cp.last_success_at = datetime.now(timezone.utc)
        else:
            cp = SyncCheckpoint(
                organization_id=organization_id,
                connection_id=connection_id,
                entity_type=entity_type,
                cursor_value=cursor_value,
                last_success_at=datetime.now(timezone.utc),
            )
            self.session.add(cp)
        await self.session.flush()

    # --- Idempotent Canonical Telemetry Upserts ---

    async def upsert_customer(
        self,
        organization_id: uuid.UUID,
        deal_id: uuid.UUID,
        customer: CanonicalCustomer,
    ) -> BusinessCustomer:
        """Idempotently insert or update a canonical business customer."""
        stmt = select(BusinessCustomer).where(
            BusinessCustomer.deal_id == deal_id,
            BusinessCustomer.source_provider == customer.provider.value,
            BusinessCustomer.external_id == customer.external_id,
        )
        res = await self.session.execute(stmt)
        existing = res.scalars().first()

        if existing:
            existing.account_name = customer.account_name
            existing.segment = customer.segment
            existing.arr_usd = customer.arr_usd
            existing.mrr_usd = customer.mrr_usd
            existing.churn_risk_score = customer.churn_risk_score
            existing.health_status = customer.health_status
            existing.renewal_date = customer.renewal_date
            existing.is_churned = customer.is_churned
            existing.industry = customer.industry
            existing.expansion_potential_usd = customer.expansion_potential_usd
            existing.synced_at = datetime.now(timezone.utc)
            await self.session.flush()
            return existing
        else:
            new_cust = BusinessCustomer(
                organization_id=organization_id,
                deal_id=deal_id,
                source_provider=customer.provider.value,
                external_id=customer.external_id,
                account_name=customer.account_name,
                segment=customer.segment,
                arr_usd=customer.arr_usd,
                mrr_usd=customer.mrr_usd,
                churn_risk_score=customer.churn_risk_score,
                health_status=customer.health_status,
                renewal_date=customer.renewal_date,
                is_churned=customer.is_churned,
                industry=customer.industry,
                expansion_potential_usd=customer.expansion_potential_usd,
                provenance_metadata={"source": customer.provider.value, "external_id": customer.external_id},
                synced_at=datetime.now(timezone.utc),
            )
            self.session.add(new_cust)
            await self.session.flush()
            return new_cust

    async def upsert_opportunity(
        self,
        organization_id: uuid.UUID,
        deal_id: uuid.UUID,
        opp: CanonicalOpportunity,
    ) -> BusinessOpportunity:
        """Idempotently insert or update a canonical sales opportunity."""
        stmt = select(BusinessOpportunity).where(
            BusinessOpportunity.deal_id == deal_id,
            BusinessOpportunity.source_provider == opp.provider.value,
            BusinessOpportunity.external_id == opp.external_id,
        )
        res = await self.session.execute(stmt)
        existing = res.scalars().first()

        if existing:
            existing.opportunity_name = opp.opportunity_name
            existing.customer_external_id = opp.customer_external_id
            existing.amount_usd = opp.amount_usd
            existing.stage = opp.stage
            existing.probability_pct = opp.probability_pct
            existing.expected_revenue_usd = opp.expected_revenue_usd
            existing.close_date = opp.close_date
            existing.is_closed = opp.is_closed
            existing.is_won = opp.is_won
            existing.synced_at = datetime.now(timezone.utc)
            await self.session.flush()
            return existing
        else:
            new_opp = BusinessOpportunity(
                organization_id=organization_id,
                deal_id=deal_id,
                source_provider=opp.provider.value,
                external_id=opp.external_id,
                opportunity_name=opp.opportunity_name,
                customer_external_id=opp.customer_external_id,
                amount_usd=opp.amount_usd,
                stage=opp.stage,
                probability_pct=opp.probability_pct,
                expected_revenue_usd=opp.expected_revenue_usd,
                close_date=opp.close_date,
                is_closed=opp.is_closed,
                is_won=opp.is_won,
                provenance_metadata={"source": opp.provider.value, "external_id": opp.external_id},
                synced_at=datetime.now(timezone.utc),
            )
            self.session.add(new_opp)
            await self.session.flush()
            return new_opp

    async def upsert_revenue_event(
        self,
        organization_id: uuid.UUID,
        deal_id: uuid.UUID,
        rev: CanonicalRevenueEvent,
    ) -> BusinessRevenueEvent:
        """Idempotently insert or update a canonical revenue event."""
        stmt = select(BusinessRevenueEvent).where(
            BusinessRevenueEvent.deal_id == deal_id,
            BusinessRevenueEvent.source_provider == rev.provider.value,
            BusinessRevenueEvent.external_id == rev.external_id,
        )
        res = await self.session.execute(stmt)
        existing = res.scalars().first()

        if existing:
            existing.amount_usd = rev.amount_usd
            existing.customer_external_id = rev.customer_external_id
            existing.invoice_number = rev.invoice_number
            existing.event_date = rev.event_date
            existing.fiscal_period = rev.fiscal_period
            existing.status = rev.status
            existing.synced_at = datetime.now(timezone.utc)
            await self.session.flush()
            return existing
        else:
            new_rev = BusinessRevenueEvent(
                organization_id=organization_id,
                deal_id=deal_id,
                source_provider=rev.provider.value,
                external_id=rev.external_id,
                customer_external_id=rev.customer_external_id,
                invoice_number=rev.invoice_number,
                event_date=rev.event_date,
                fiscal_period=rev.fiscal_period,
                amount_usd=rev.amount_usd,
                status=rev.status,
                provenance_metadata={"source": rev.provider.value, "external_id": rev.external_id},
                synced_at=datetime.now(timezone.utc),
            )
            self.session.add(new_rev)
            await self.session.flush()
            return new_rev

    async def upsert_expense(
        self,
        organization_id: uuid.UUID,
        deal_id: uuid.UUID,
        exp: CanonicalExpense,
    ) -> BusinessExpense:
        """Idempotently insert or update a canonical expense event."""
        stmt = select(BusinessExpense).where(
            BusinessExpense.deal_id == deal_id,
            BusinessExpense.source_provider == exp.provider.value,
            BusinessExpense.external_id == exp.external_id,
        )
        res = await self.session.execute(stmt)
        existing = res.scalars().first()

        if existing:
            existing.amount_usd = exp.amount_usd
            existing.expense_date = exp.expense_date
            existing.fiscal_period = exp.fiscal_period
            existing.category = exp.category
            existing.vendor_name = exp.vendor_name
            existing.synced_at = datetime.now(timezone.utc)
            await self.session.flush()
            return existing
        else:
            new_exp = BusinessExpense(
                organization_id=organization_id,
                deal_id=deal_id,
                source_provider=exp.provider.value,
                external_id=exp.external_id,
                expense_date=exp.expense_date,
                fiscal_period=exp.fiscal_period,
                category=exp.category,
                vendor_name=exp.vendor_name,
                amount_usd=exp.amount_usd,
                provenance_metadata={"source": exp.provider.value, "external_id": exp.external_id},
                synced_at=datetime.now(timezone.utc),
            )
            self.session.add(new_exp)
            await self.session.flush()
            return new_exp

    # --- Telemetry Change Detection ---

    async def log_telemetry_change(
        self,
        organization_id: uuid.UUID,
        deal_id: uuid.UUID,
        metric_name: str,
        previous_value: float,
        new_value: float,
        severity: str,
        affected_kpi: str,
        affected_thesis_pillar: Optional[str],
        affected_initiatives: List[str],
        suggested_agent_id: str,
        evidence_source: str,
    ) -> BusinessTelemetryChange:
        """Log detected metric drift and its strategic impact."""
        delta_val = round(new_value - previous_value, 2)
        pct = round((delta_val / previous_value * 100.0), 2) if previous_value != 0 else 0.0
        change = BusinessTelemetryChange(
            organization_id=organization_id,
            deal_id=deal_id,
            metric_name=metric_name,
            previous_value=previous_value,
            new_value=new_value,
            delta_value=delta_val,
            delta_percentage=pct,
            severity=severity,
            affected_kpi=affected_kpi,
            affected_thesis_pillar=affected_thesis_pillar,
            affected_initiatives=affected_initiatives,
            suggested_agent_id=suggested_agent_id,
            evidence_source=evidence_source,
            is_resolved=False,
            detected_at=datetime.now(timezone.utc),
        )
        self.session.add(change)
        await self.session.flush()
        return change

    async def list_telemetry_changes(
        self,
        organization_id: uuid.UUID,
        deal_id: uuid.UUID,
        unresolved_only: bool = True,
    ) -> List[BusinessTelemetryChange]:
        """Query detected changes for a deal workspace."""
        stmt = select(BusinessTelemetryChange).where(
            BusinessTelemetryChange.deal_id == deal_id,
            BusinessTelemetryChange.organization_id == organization_id,
        )
        if unresolved_only:
            stmt = stmt.where(BusinessTelemetryChange.is_resolved.is_(False))
        stmt = stmt.order_by(desc(BusinessTelemetryChange.detected_at))
        res = await self.session.execute(stmt)
        return list(res.scalars().all())

    # --- Consolidated Telemetry Queries for Agents & KPI Engine ---

    async def get_customers_for_deal(
        self,
        organization_id: uuid.UUID,
        deal_id: uuid.UUID,
    ) -> List[BusinessCustomer]:
        """Fetch all canonical customers for a deal."""
        stmt = select(BusinessCustomer).where(
            BusinessCustomer.deal_id == deal_id,
            BusinessCustomer.organization_id == organization_id,
        )
        res = await self.session.execute(stmt)
        return list(res.scalars().all())

    async def get_opportunities_for_deal(
        self,
        organization_id: uuid.UUID,
        deal_id: uuid.UUID,
    ) -> List[BusinessOpportunity]:
        """Fetch all canonical opportunities for a deal."""
        stmt = select(BusinessOpportunity).where(
            BusinessOpportunity.deal_id == deal_id,
            BusinessOpportunity.organization_id == organization_id,
        )
        res = await self.session.execute(stmt)
        return list(res.scalars().all())

    async def get_revenue_events_for_deal(
        self,
        organization_id: uuid.UUID,
        deal_id: uuid.UUID,
    ) -> List[BusinessRevenueEvent]:
        """Fetch all canonical revenue events for a deal."""
        stmt = select(BusinessRevenueEvent).where(
            BusinessRevenueEvent.deal_id == deal_id,
            BusinessRevenueEvent.organization_id == organization_id,
        )
        res = await self.session.execute(stmt)
        return list(res.scalars().all())

    async def get_expenses_for_deal(
        self,
        organization_id: uuid.UUID,
        deal_id: uuid.UUID,
    ) -> List[BusinessExpense]:
        """Fetch all canonical expenses for a deal."""
        stmt = select(BusinessExpense).where(
            BusinessExpense.deal_id == deal_id,
            BusinessExpense.organization_id == organization_id,
        )
        res = await self.session.execute(stmt)
        return list(res.scalars().all())
