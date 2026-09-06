"""Database Models for External Business System Connectors and Canonical Telemetry."""

import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.domains.common.models import TenantScopedModel
from app.domains.common.types import CompatibleJSON

if TYPE_CHECKING:
    from app.domains.deals.models import Deal


class ExternalConnection(TenantScopedModel):
    """Authorized external business system connection (Salesforce, QuickBooks, etc.)."""
    __tablename__ = "external_connections"

    deal_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("deals.id", ondelete="CASCADE"), nullable=True, index=True
    )
    provider: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    connection_name: Mapped[str] = mapped_column(String(255), nullable=False)
    connection_status: Mapped[str] = mapped_column(String(50), default="DISCONNECTED", nullable=False)
    auth_status: Mapped[str] = mapped_column(String(50), default="PENDING", nullable=False)
    
    # Encrypted credentials (AES-128 Fernet) - NEVER plaintext
    encrypted_credentials: Mapped[str] = mapped_column(Text, nullable=False)
    
    capabilities: Mapped[Optional[list]] = mapped_column(CompatibleJSON, default=list, nullable=True)
    auto_sync_interval_hours: Mapped[int] = mapped_column(Integer, default=6, nullable=False)
    last_successful_sync: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_attempted_sync: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    data_freshness_status: Mapped[str] = mapped_column(String(50), default="NOT_SYNCED", nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    deal: Mapped[Optional["Deal"]] = relationship("Deal", backref="external_connections")
    sync_runs: Mapped[List["SyncRun"]] = relationship("SyncRun", back_populates="connection", cascade="all, delete-orphan")
    checkpoints: Mapped[List["SyncCheckpoint"]] = relationship("SyncCheckpoint", back_populates="connection", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_ext_conn_org_provider", "organization_id", "provider"),
        Index("ix_ext_conn_deal_status", "deal_id", "connection_status"),
    )


class ExternalObjectMapping(TenantScopedModel):
    """Idempotent mapping registry between external system IDs and internal canonical UUIDs."""
    __tablename__ = "external_object_mappings"

    connection_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("external_connections.id", ondelete="CASCADE"), nullable=False, index=True
    )
    deal_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("deals.id", ondelete="CASCADE"), nullable=True, index=True
    )
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    external_object_type: Mapped[str] = mapped_column(String(100), nullable=False)  # Account, Opportunity, Invoice, etc.
    external_object_id: Mapped[str] = mapped_column(String(255), nullable=False)
    canonical_entity_type: Mapped[str] = mapped_column(String(100), nullable=False)  # BusinessCustomer, BusinessOpportunity, etc.
    canonical_entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    last_synced_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint("organization_id", "provider", "external_object_type", "external_object_id", name="uq_ext_obj_mapping"),
        Index("ix_obj_mapping_lookup", "provider", "external_object_type", "external_object_id"),
    )


class SyncRun(TenantScopedModel):
    """Historical audit log for synchronization jobs."""
    __tablename__ = "sync_runs"

    connection_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("external_connections.id", ondelete="CASCADE"), nullable=False, index=True
    )
    deal_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("deals.id", ondelete="CASCADE"), nullable=True, index=True
    )
    status: Mapped[str] = mapped_column(String(50), default="QUEUED", nullable=False, index=True)
    is_full_sync: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    records_fetched: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    records_normalized: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    records_upserted: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    records_failed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    entity_breakdown: Mapped[Optional[dict]] = mapped_column(CompatibleJSON, default=dict, nullable=True)

    # Relationships
    connection: Mapped["ExternalConnection"] = relationship("ExternalConnection", back_populates="sync_runs")

    __table_args__ = (
        Index("ix_sync_runs_org_conn", "organization_id", "connection_id"),
        Index("ix_sync_runs_status_started", "status", "started_at"),
    )


class SyncCheckpoint(TenantScopedModel):
    """High-water-mark cursor per connection and entity type for incremental sync."""
    __tablename__ = "sync_checkpoints"

    connection_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("external_connections.id", ondelete="CASCADE"), nullable=False, index=True
    )
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False)
    cursor_value: Mapped[str] = mapped_column(String(255), nullable=False)
    last_success_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    # Relationships
    connection: Mapped["ExternalConnection"] = relationship("ExternalConnection", back_populates="checkpoints")

    __table_args__ = (
        UniqueConstraint("connection_id", "entity_type", name="uq_sync_checkpoint"),
    )


class BusinessCustomer(TenantScopedModel):
    """Canonical business customer ingested from CRM/ERP."""
    __tablename__ = "business_customers"

    deal_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("deals.id", ondelete="CASCADE"), nullable=False, index=True
    )
    source_provider: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    external_id: Mapped[str] = mapped_column(String(255), nullable=False)
    account_name: Mapped[str] = mapped_column(String(255), nullable=False)
    segment: Mapped[str] = mapped_column(String(100), default="MID_MARKET", nullable=False)
    arr_usd: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    mrr_usd: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    churn_risk_score: Mapped[float] = mapped_column(Float, default=0.15, nullable=False)
    health_status: Mapped[str] = mapped_column(String(50), default="HEALTHY", nullable=False)
    renewal_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    is_churned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    industry: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    expansion_potential_usd: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    provenance_metadata: Mapped[Optional[dict]] = mapped_column(CompatibleJSON, default=dict, nullable=True)
    synced_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint("deal_id", "source_provider", "external_id", name="uq_business_cust_deal_ext"),
        Index("ix_biz_cust_deal_health", "deal_id", "health_status"),
        Index("ix_biz_cust_deal_arr", "deal_id", "arr_usd"),
    )


class BusinessOpportunity(TenantScopedModel):
    """Canonical commercial sales opportunity / deal pipeline event."""
    __tablename__ = "business_opportunities"

    deal_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("deals.id", ondelete="CASCADE"), nullable=False, index=True
    )
    source_provider: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    external_id: Mapped[str] = mapped_column(String(255), nullable=False)
    opportunity_name: Mapped[str] = mapped_column(String(255), nullable=False)
    customer_external_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    amount_usd: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    stage: Mapped[str] = mapped_column(String(100), nullable=False)
    probability_pct: Mapped[float] = mapped_column(Float, default=50.0, nullable=False)
    expected_revenue_usd: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    close_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    is_closed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_won: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    provenance_metadata: Mapped[Optional[dict]] = mapped_column(CompatibleJSON, default=dict, nullable=True)
    synced_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint("deal_id", "source_provider", "external_id", name="uq_biz_opp_deal_ext"),
        Index("ix_biz_opp_deal_stage", "deal_id", "stage"),
        Index("ix_biz_opp_deal_close", "deal_id", "close_date"),
    )


class BusinessRevenueEvent(TenantScopedModel):
    """Canonical realized income / invoice transaction."""
    __tablename__ = "business_revenue_events"

    deal_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("deals.id", ondelete="CASCADE"), nullable=False, index=True
    )
    source_provider: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    external_id: Mapped[str] = mapped_column(String(255), nullable=False)
    customer_external_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    invoice_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    event_date: Mapped[date] = mapped_column(Date, nullable=False)
    fiscal_period: Mapped[str] = mapped_column(String(50), nullable=False)
    amount_usd: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="PAID", nullable=False)
    provenance_metadata: Mapped[Optional[dict]] = mapped_column(CompatibleJSON, default=dict, nullable=True)
    synced_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint("deal_id", "source_provider", "external_id", name="uq_biz_rev_deal_ext"),
        Index("ix_biz_rev_deal_period", "deal_id", "fiscal_period"),
    )


class BusinessExpense(TenantScopedModel):
    """Canonical operational or capital expenditure."""
    __tablename__ = "business_expenses"

    deal_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("deals.id", ondelete="CASCADE"), nullable=False, index=True
    )
    source_provider: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    external_id: Mapped[str] = mapped_column(String(255), nullable=False)
    expense_date: Mapped[date] = mapped_column(Date, nullable=False)
    fiscal_period: Mapped[str] = mapped_column(String(50), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    vendor_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    amount_usd: Mapped[float] = mapped_column(Float, nullable=False)
    provenance_metadata: Mapped[Optional[dict]] = mapped_column(CompatibleJSON, default=dict, nullable=True)
    synced_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint("deal_id", "source_provider", "external_id", name="uq_biz_exp_deal_ext"),
        Index("ix_biz_exp_deal_category", "deal_id", "category"),
    )


class BusinessTelemetryChange(TenantScopedModel):
    """Change detection record logging significant drift in operational/financial telemetry."""
    __tablename__ = "business_telemetry_changes"

    deal_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("deals.id", ondelete="CASCADE"), nullable=False, index=True
    )
    metric_name: Mapped[str] = mapped_column(String(100), nullable=False)
    previous_value: Mapped[float] = mapped_column(Float, nullable=False)
    new_value: Mapped[float] = mapped_column(Float, nullable=False)
    delta_value: Mapped[float] = mapped_column(Float, nullable=False)
    delta_percentage: Mapped[float] = mapped_column(Float, nullable=False)
    severity: Mapped[str] = mapped_column(String(50), default="MEDIUM", nullable=False)
    affected_kpi: Mapped[str] = mapped_column(String(100), nullable=False)
    affected_thesis_pillar: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    affected_initiatives: Mapped[Optional[list]] = mapped_column(CompatibleJSON, default=list, nullable=True)
    suggested_agent_id: Mapped[str] = mapped_column(String(100), nullable=False)
    evidence_source: Mapped[str] = mapped_column(String(255), nullable=False)
    is_resolved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("ix_telemetry_change_deal_res", "deal_id", "is_resolved"),
        Index("ix_telemetry_change_metric", "deal_id", "metric_name"),
    )
