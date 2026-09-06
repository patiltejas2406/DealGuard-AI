"""Post-Acquisition Intelligence, Value Creation & Growth Engine Tables.

Revision ID: 018_post_acquisition_intelligence_engine
Revises: 017_ml_predictive_intelligence_engine
Create Date: 2026-09-06 14:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "018_post_acquisition_intelligence_engine"
down_revision: Union[str, None] = "017_ml_predictive_intelligence_engine"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    is_postgres = bind.dialect.name == "postgresql"

    json_type = postgresql.JSONB(astext_type=sa.Text()) if is_postgres else sa.JSON()
    uuid_type = postgresql.UUID(as_uuid=True) if is_postgres else sa.String(36)

    # 1. Create customer_accounts table
    op.create_table(
        "customer_accounts",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("organization_id", uuid_type, sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("deal_id", uuid_type, sa.ForeignKey("deals.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("company_id", uuid_type, sa.ForeignKey("target_companies.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("account_name", sa.String(255), nullable=False),
        sa.Column("segment", sa.String(100), nullable=False, server_default="MID_MARKET"),
        sa.Column("arr", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("mrr", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("contract_start_date", sa.Date(), nullable=True),
        sa.Column("contract_end_date", sa.Date(), nullable=True),
        sa.Column("churn_risk_score", sa.Float(), nullable=False, server_default="0.15"),
        sa.Column("health_status", sa.String(50), nullable=False, server_default="HEALTHY"),
        sa.Column("nps", sa.Integer(), nullable=True),
        sa.Column("is_churned", sa.Boolean(), nullable=False, server_default=sa.text("0" if not is_postgres else "false")),
        sa.Column("expansion_potential_usd", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("industry", sa.String(100), nullable=True),
        sa.Column("products_used", json_type, nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_cust_accounts_org_deal", "customer_accounts", ["organization_id", "deal_id"])
    op.create_index("ix_cust_accounts_deal_health", "customer_accounts", ["deal_id", "health_status"])
    op.create_index("ix_cust_accounts_deal_arr", "customer_accounts", ["deal_id", "arr"])

    # 2. Create post_acquisition_metrics table
    op.create_table(
        "post_acquisition_metrics",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("organization_id", uuid_type, sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("deal_id", uuid_type, sa.ForeignKey("deals.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("fiscal_period", sa.String(50), nullable=False),
        sa.Column("metric_category", sa.String(50), nullable=False),
        sa.Column("metric_name", sa.String(100), nullable=False, index=True),
        sa.Column("baseline_value", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("target_value", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("actual_value", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("variance_pct", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("unit", sa.String(20), nullable=False, server_default="USD"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_post_metrics_org_deal", "post_acquisition_metrics", ["organization_id", "deal_id"])
    op.create_index("ix_post_metrics_deal_period", "post_acquisition_metrics", ["deal_id", "fiscal_period", "metric_name"])

    # 3. Create acquisition_theses table
    op.create_table(
        "acquisition_theses",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("organization_id", uuid_type, sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("deal_id", uuid_type, sa.ForeignKey("deals.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("thesis_pillar", sa.String(50), nullable=False),
        sa.Column("target_metric", sa.String(100), nullable=False),
        sa.Column("baseline_value", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("target_value", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("actual_value", sa.Float(), nullable=True),
        sa.Column("variance_pct", sa.Float(), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="INSUFFICIENT_DATA"),
        sa.Column("rationale", sa.Text(), nullable=True),
        sa.Column("citations", json_type, nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_thesis_org_deal", "acquisition_theses", ["organization_id", "deal_id"])
    op.create_index("ix_thesis_pillar", "acquisition_theses", ["deal_id", "thesis_pillar"])

    # 4. Create value_creation_initiatives table
    op.create_table(
        "value_creation_initiatives",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("organization_id", uuid_type, sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("deal_id", uuid_type, sa.ForeignKey("deals.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("pillar", sa.String(50), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("owner", sa.String(100), nullable=True),
        sa.Column("target_ebitda_impact", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("realized_ebitda_impact", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("status", sa.String(50), nullable=False, server_default="IDENTIFIED"),
        sa.Column("timeline_quarter", sa.String(50), nullable=False, server_default="Q1_POST_CLOSE"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_vci_org_deal", "value_creation_initiatives", ["organization_id", "deal_id"])
    op.create_index("ix_vci_deal_pillar", "value_creation_initiatives", ["deal_id", "pillar"])


def downgrade() -> None:
    op.drop_index("ix_vci_deal_pillar", table_name="value_creation_initiatives")
    op.drop_index("ix_vci_org_deal", table_name="value_creation_initiatives")
    op.drop_table("value_creation_initiatives")

    op.drop_index("ix_thesis_pillar", table_name="acquisition_theses")
    op.drop_index("ix_thesis_org_deal", table_name="acquisition_theses")
    op.drop_table("acquisition_theses")

    op.drop_index("ix_post_metrics_deal_period", table_name="post_acquisition_metrics")
    op.drop_index("ix_post_metrics_org_deal", table_name="post_acquisition_metrics")
    op.drop_table("post_acquisition_metrics")

    op.drop_index("ix_cust_accounts_deal_arr", table_name="customer_accounts")
    op.drop_index("ix_cust_accounts_deal_health", table_name="customer_accounts")
    op.drop_index("ix_cust_accounts_org_deal", table_name="customer_accounts")
    op.drop_table("customer_accounts")
