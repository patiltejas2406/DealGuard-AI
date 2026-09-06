"""Business Telemetry, External Connectors and Change Detection Engine Tables.

Revision ID: 019_business_telemetry_and_connectors
Revises: 018_post_acquisition_intelligence_engine
Create Date: 2026-09-06 17:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "019_business_telemetry_and_connectors"
down_revision: Union[str, None] = "018_post_acquisition_intelligence_engine"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    is_postgres = bind.dialect.name == "postgresql"

    json_type = postgresql.JSONB(astext_type=sa.Text()) if is_postgres else sa.JSON()
    uuid_type = postgresql.UUID(as_uuid=True) if is_postgres else sa.String(36)
    bool_false = sa.text("false" if is_postgres else "0")
    bool_true = sa.text("true" if is_postgres else "1")

    # 1. Create external_connections table
    op.create_table(
        "external_connections",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("organization_id", uuid_type, sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("deal_id", uuid_type, sa.ForeignKey("deals.id", ondelete="CASCADE"), nullable=True, index=True),
        sa.Column("provider", sa.String(50), nullable=False, index=True),
        sa.Column("connection_name", sa.String(255), nullable=False),
        sa.Column("connection_status", sa.String(50), nullable=False, server_default="DISCONNECTED"),
        sa.Column("auth_status", sa.String(50), nullable=False, server_default="PENDING"),
        sa.Column("encrypted_credentials", sa.Text(), nullable=False),
        sa.Column("capabilities", json_type, nullable=True),
        sa.Column("auto_sync_interval_hours", sa.Integer(), nullable=False, server_default="6"),
        sa.Column("last_successful_sync", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_attempted_sync", sa.DateTime(timezone=True), nullable=True),
        sa.Column("data_freshness_status", sa.String(50), nullable=False, server_default="NOT_SYNCED"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=bool_true),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_ext_conn_org_provider", "external_connections", ["organization_id", "provider"])
    op.create_index("ix_ext_conn_deal_status", "external_connections", ["deal_id", "connection_status"])

    # 2. Create external_object_mappings table
    op.create_table(
        "external_object_mappings",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("organization_id", uuid_type, sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("connection_id", uuid_type, sa.ForeignKey("external_connections.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("deal_id", uuid_type, sa.ForeignKey("deals.id", ondelete="CASCADE"), nullable=True, index=True),
        sa.Column("provider", sa.String(50), nullable=False),
        sa.Column("external_object_type", sa.String(100), nullable=False),
        sa.Column("external_object_id", sa.String(255), nullable=False),
        sa.Column("canonical_entity_type", sa.String(100), nullable=False),
        sa.Column("canonical_entity_id", uuid_type, nullable=False, index=True),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("organization_id", "provider", "external_object_type", "external_object_id", name="uq_ext_obj_mapping"),
    )
    op.create_index("ix_obj_mapping_lookup", "external_object_mappings", ["provider", "external_object_type", "external_object_id"])

    # 3. Create sync_runs table
    op.create_table(
        "sync_runs",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("organization_id", uuid_type, sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("connection_id", uuid_type, sa.ForeignKey("external_connections.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("deal_id", uuid_type, sa.ForeignKey("deals.id", ondelete="CASCADE"), nullable=True, index=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="QUEUED", index=True),
        sa.Column("is_full_sync", sa.Boolean(), nullable=False, server_default=bool_false),
        sa.Column("records_fetched", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("records_normalized", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("records_upserted", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("records_failed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_seconds", sa.Float(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("entity_breakdown", json_type, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_sync_runs_org_conn", "sync_runs", ["organization_id", "connection_id"])
    op.create_index("ix_sync_runs_status_started", "sync_runs", ["status", "started_at"])

    # 4. Create sync_checkpoints table
    op.create_table(
        "sync_checkpoints",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("organization_id", uuid_type, sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("connection_id", uuid_type, sa.ForeignKey("external_connections.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("entity_type", sa.String(100), nullable=False),
        sa.Column("cursor_value", sa.String(255), nullable=False),
        sa.Column("last_success_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("connection_id", "entity_type", name="uq_sync_checkpoint"),
    )

    # 5. Create business_customers table
    op.create_table(
        "business_customers",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("organization_id", uuid_type, sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("deal_id", uuid_type, sa.ForeignKey("deals.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("source_provider", sa.String(50), nullable=False, index=True),
        sa.Column("external_id", sa.String(255), nullable=False),
        sa.Column("account_name", sa.String(255), nullable=False),
        sa.Column("segment", sa.String(100), nullable=False, server_default="MID_MARKET"),
        sa.Column("arr_usd", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("mrr_usd", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("churn_risk_score", sa.Float(), nullable=False, server_default="0.15"),
        sa.Column("health_status", sa.String(50), nullable=False, server_default="HEALTHY"),
        sa.Column("renewal_date", sa.Date(), nullable=True),
        sa.Column("is_churned", sa.Boolean(), nullable=False, server_default=bool_false),
        sa.Column("industry", sa.String(100), nullable=True),
        sa.Column("expansion_potential_usd", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("provenance_metadata", json_type, nullable=True),
        sa.Column("synced_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("deal_id", "source_provider", "external_id", name="uq_business_cust_deal_ext"),
    )
    op.create_index("ix_biz_cust_deal_health", "business_customers", ["deal_id", "health_status"])
    op.create_index("ix_biz_cust_deal_arr", "business_customers", ["deal_id", "arr_usd"])

    # 6. Create business_opportunities table
    op.create_table(
        "business_opportunities",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("organization_id", uuid_type, sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("deal_id", uuid_type, sa.ForeignKey("deals.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("source_provider", sa.String(50), nullable=False, index=True),
        sa.Column("external_id", sa.String(255), nullable=False),
        sa.Column("opportunity_name", sa.String(255), nullable=False),
        sa.Column("customer_external_id", sa.String(255), nullable=True),
        sa.Column("amount_usd", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("stage", sa.String(100), nullable=False),
        sa.Column("probability_pct", sa.Float(), nullable=False, server_default="50.0"),
        sa.Column("expected_revenue_usd", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("close_date", sa.Date(), nullable=True),
        sa.Column("is_closed", sa.Boolean(), nullable=False, server_default=bool_false),
        sa.Column("is_won", sa.Boolean(), nullable=False, server_default=bool_false),
        sa.Column("provenance_metadata", json_type, nullable=True),
        sa.Column("synced_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("deal_id", "source_provider", "external_id", name="uq_biz_opp_deal_ext"),
    )
    op.create_index("ix_biz_opp_deal_stage", "business_opportunities", ["deal_id", "stage"])
    op.create_index("ix_biz_opp_deal_close", "business_opportunities", ["deal_id", "close_date"])

    # 7. Create business_revenue_events table
    op.create_table(
        "business_revenue_events",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("organization_id", uuid_type, sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("deal_id", uuid_type, sa.ForeignKey("deals.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("source_provider", sa.String(50), nullable=False, index=True),
        sa.Column("external_id", sa.String(255), nullable=False),
        sa.Column("customer_external_id", sa.String(255), nullable=True),
        sa.Column("invoice_number", sa.String(100), nullable=True),
        sa.Column("event_date", sa.Date(), nullable=False),
        sa.Column("fiscal_period", sa.String(50), nullable=False),
        sa.Column("amount_usd", sa.Float(), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="PAID"),
        sa.Column("provenance_metadata", json_type, nullable=True),
        sa.Column("synced_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("deal_id", "source_provider", "external_id", name="uq_biz_rev_deal_ext"),
    )
    op.create_index("ix_biz_rev_deal_period", "business_revenue_events", ["deal_id", "fiscal_period"])

    # 8. Create business_expenses table
    op.create_table(
        "business_expenses",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("organization_id", uuid_type, sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("deal_id", uuid_type, sa.ForeignKey("deals.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("source_provider", sa.String(50), nullable=False, index=True),
        sa.Column("external_id", sa.String(255), nullable=False),
        sa.Column("expense_date", sa.Date(), nullable=False),
        sa.Column("fiscal_period", sa.String(50), nullable=False),
        sa.Column("category", sa.String(100), nullable=False),
        sa.Column("vendor_name", sa.String(255), nullable=True),
        sa.Column("amount_usd", sa.Float(), nullable=False),
        sa.Column("provenance_metadata", json_type, nullable=True),
        sa.Column("synced_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("deal_id", "source_provider", "external_id", name="uq_biz_exp_deal_ext"),
    )
    op.create_index("ix_biz_exp_deal_category", "business_expenses", ["deal_id", "category"])

    # 9. Create business_telemetry_changes table
    op.create_table(
        "business_telemetry_changes",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("organization_id", uuid_type, sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("deal_id", uuid_type, sa.ForeignKey("deals.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("metric_name", sa.String(100), nullable=False),
        sa.Column("previous_value", sa.Float(), nullable=False),
        sa.Column("new_value", sa.Float(), nullable=False),
        sa.Column("delta_value", sa.Float(), nullable=False),
        sa.Column("delta_percentage", sa.Float(), nullable=False),
        sa.Column("severity", sa.String(50), nullable=False, server_default="MEDIUM"),
        sa.Column("affected_kpi", sa.String(100), nullable=False),
        sa.Column("affected_thesis_pillar", sa.String(100), nullable=True),
        sa.Column("affected_initiatives", json_type, nullable=True),
        sa.Column("suggested_agent_id", sa.String(100), nullable=False),
        sa.Column("evidence_source", sa.String(255), nullable=False),
        sa.Column("is_resolved", sa.Boolean(), nullable=False, server_default=bool_false),
        sa.Column("detected_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_telemetry_change_deal_res", "business_telemetry_changes", ["deal_id", "is_resolved"])
    op.create_index("ix_telemetry_change_metric", "business_telemetry_changes", ["deal_id", "metric_name"])


def downgrade() -> None:
    op.drop_table("business_telemetry_changes")
    op.drop_table("business_expenses")
    op.drop_table("business_revenue_events")
    op.drop_table("business_opportunities")
    op.drop_table("business_customers")
    op.drop_table("sync_checkpoints")
    op.drop_table("sync_runs")
    op.drop_table("external_object_mappings")
    op.drop_table("external_connections")
