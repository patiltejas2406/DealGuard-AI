"""Synergy Realization & Value Creation Intelligence Engine Tables.

Revision ID: 010_synergy_value_creation_engine
Revises: 009_scenario_simulation_engine
Create Date: 2026-08-26 17:25:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "010_synergy_value_creation_engine"
down_revision: Union[str, None] = "009_scenario_simulation_engine"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    is_postgres = bind.dialect.name == "postgresql"

    json_type = postgresql.JSONB(astext_type=sa.Text()) if is_postgres else sa.JSON()
    uuid_type = postgresql.UUID(as_uuid=True) if is_postgres else sa.String(36)

    # 1. Create synergy_opportunities table
    op.create_table(
        "synergy_opportunities",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("organization_id", uuid_type, sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("deal_id", uuid_type, sa.ForeignKey("deals.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("company_id", uuid_type, sa.ForeignKey("target_companies.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("synergy_type", sa.String(50), nullable=False),  # REVENUE, COST, OPERATIONAL
        sa.Column("category", sa.String(100), nullable=False),     # CROSS_SELLING, PROCUREMENT, HEADCOUNT, etc.
        sa.Column("status", sa.String(50), nullable=False, server_default="IDENTIFIED"),  # IDENTIFIED, VALIDATED, PLANNED, IN_PROGRESS, PARTIALLY_REALIZED, REALIZED, AT_RISK, ABANDONED
        sa.Column("confidence", sa.String(20), nullable=False, server_default="MEDIUM"),  # HIGH, MEDIUM, LOW
        sa.Column("baseline_value", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("target_value", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("potential_annual_value", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("realization_rate_pct", sa.Float(), nullable=False, server_default="100.0"),
        sa.Column("probability_pct", sa.Float(), nullable=False, server_default="80.0"),
        sa.Column("expected_annual_value", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("one_time_integration_cost", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("realization_curve", json_type, nullable=True),  # {"year_1": 20, "year_2": 50, "year_3": 80, "year_4": 100, "year_5": 100}
        sa.Column("evidence_citation_ids", json_type, nullable=True),  # list of citation UUID strings
        sa.Column("owner", sa.String(100), nullable=True),
        sa.Column("realized_annual_value", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_by_id", uuid_type, sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )

    op.create_index(
        "ix_synergies_org_deal",
        "synergy_opportunities",
        ["organization_id", "deal_id"],
    )
    op.create_index(
        "ix_synergies_deal_type",
        "synergy_opportunities",
        ["deal_id", "synergy_type"],
    )
    op.create_index(
        "ix_synergies_status",
        "synergy_opportunities",
        ["deal_id", "status"],
    )

    # 2. Create synergy_realization_logs table
    op.create_table(
        "synergy_realization_logs",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("organization_id", uuid_type, sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("deal_id", uuid_type, sa.ForeignKey("deals.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("synergy_id", uuid_type, sa.ForeignKey("synergy_opportunities.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("fiscal_period", sa.String(50), nullable=False),  # e.g. "Q1-2024", "FY2024"
        sa.Column("planned_value", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("actual_value", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("variance", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("logged_by_id", uuid_type, sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )

    op.create_index(
        "ix_synergy_logs_org_deal",
        "synergy_realization_logs",
        ["organization_id", "deal_id"],
    )
    op.create_index(
        "ix_synergy_logs_synergy",
        "synergy_realization_logs",
        ["synergy_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_synergy_logs_synergy", table_name="synergy_realization_logs")
    op.drop_index("ix_synergy_logs_org_deal", table_name="synergy_realization_logs")
    op.drop_table("synergy_realization_logs")

    op.drop_index("ix_synergies_status", table_name="synergy_opportunities")
    op.drop_index("ix_synergies_deal_type", table_name="synergy_opportunities")
    op.drop_index("ix_synergies_org_deal", table_name="synergy_opportunities")
    op.drop_table("synergy_opportunities")
