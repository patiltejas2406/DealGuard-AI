"""What-If Deal Simulation & Monte Carlo Scenario Intelligence Tables.

Revision ID: 009_scenario_simulation_engine
Revises: 008_decision_score_engine
Create Date: 2026-08-26 17:15:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "009_scenario_simulation_engine"
down_revision: Union[str, None] = "008_decision_score_engine"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    is_postgres = bind.dialect.name == "postgresql"

    json_type = postgresql.JSONB(astext_type=sa.Text()) if is_postgres else sa.JSON()
    uuid_type = postgresql.UUID(as_uuid=True) if is_postgres else sa.String(36)

    # 1. Create scenarios table
    op.create_table(
        "scenarios",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("organization_id", uuid_type, sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("deal_id", uuid_type, sa.ForeignKey("deals.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("scenario_type", sa.String(50), nullable=False, server_default="WHAT_IF"),  # WHAT_IF, SENSITIVITY, MONTE_CARLO, DOWNSIDE, UPSIDE
        sa.Column("status", sa.String(20), nullable=False, server_default="ACTIVE"),  # DRAFT, ACTIVE, COMPLETED, ARCHIVED
        sa.Column("assumptions", json_type, nullable=False),
        sa.Column("results", json_type, nullable=True),
        sa.Column("created_by_id", uuid_type, sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )

    op.create_index(
        "ix_scenarios_org_deal",
        "scenarios",
        ["organization_id", "deal_id"],
    )
    op.create_index(
        "ix_scenarios_deal_type",
        "scenarios",
        ["deal_id", "scenario_type"],
    )

    # 2. Create simulation_runs table
    op.create_table(
        "simulation_runs",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("organization_id", uuid_type, sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("deal_id", uuid_type, sa.ForeignKey("deals.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("scenario_id", uuid_type, sa.ForeignKey("scenarios.id", ondelete="CASCADE"), nullable=True, index=True),
        sa.Column("simulation_type", sa.String(50), nullable=False, server_default="MONTE_CARLO"),  # MONTE_CARLO, SENSITIVITY_2D
        sa.Column("parameters", json_type, nullable=False),
        sa.Column("iterations_count", sa.Integer(), nullable=False, server_default="1000"),
        sa.Column("random_seed", sa.Integer(), nullable=True),
        sa.Column("statistics_output", json_type, nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="COMPLETED"),  # QUEUED, RUNNING, COMPLETED, FAILED
        sa.Column("created_by_id", uuid_type, sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )

    op.create_index(
        "ix_sim_runs_org_deal",
        "simulation_runs",
        ["organization_id", "deal_id"],
    )
    op.create_index(
        "ix_sim_runs_scenario",
        "simulation_runs",
        ["scenario_id", "created_at"],
    )
    op.create_index(
        "ix_sim_runs_status",
        "simulation_runs",
        ["deal_id", "status"],
    )


def downgrade() -> None:
    op.drop_index("ix_sim_runs_status", table_name="simulation_runs")
    op.drop_index("ix_sim_runs_scenario", table_name="simulation_runs")
    op.drop_index("ix_sim_runs_org_deal", table_name="simulation_runs")
    op.drop_table("simulation_runs")

    op.drop_index("ix_scenarios_deal_type", table_name="scenarios")
    op.drop_index("ix_scenarios_org_deal", table_name="scenarios")
    op.drop_table("scenarios")
