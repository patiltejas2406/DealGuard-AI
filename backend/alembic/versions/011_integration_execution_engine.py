"""100-Day Post-Acquisition Integration Execution & Workstream Planning Engine Tables.

Revision ID: 011_integration_execution_engine
Revises: 010_synergy_value_creation_engine
Create Date: 2026-08-26 17:45:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "011_integration_execution_engine"
down_revision: Union[str, None] = "010_synergy_value_creation_engine"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    is_postgres = bind.dialect.name == "postgresql"

    json_type = postgresql.JSONB(astext_type=sa.Text()) if is_postgres else sa.JSON()
    uuid_type = postgresql.UUID(as_uuid=True) if is_postgres else sa.String(36)

    # 1. Create integration_programs table
    op.create_table(
        "integration_programs",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("organization_id", uuid_type, sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("deal_id", uuid_type, sa.ForeignKey("deals.id", ondelete="CASCADE"), nullable=False, unique=True, index=True),
        sa.Column("company_id", uuid_type, sa.ForeignKey("target_companies.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="ACTIVE"),  # PLANNING, ACTIVE, COMPLETED, ON_HOLD
        sa.Column("close_date", sa.Date(), nullable=True),
        sa.Column("day_0_date", sa.Date(), nullable=True),
        sa.Column("day_100_date", sa.Date(), nullable=True),
        sa.Column("current_day_offset", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("executive_sponsor", sa.String(100), nullable=True),
        sa.Column("objectives", json_type, nullable=True),
        sa.Column("health_score", sa.Float(), nullable=False, server_default="100.0"),
        sa.Column("health_band", sa.String(50), nullable=False, server_default="HEALTHY"),  # HEALTHY, WATCH, AT_RISK, CRITICAL
        sa.Column("created_by_id", uuid_type, sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )

    op.create_index(
        "ix_integration_programs_org_deal",
        "integration_programs",
        ["organization_id", "deal_id"],
    )

    # 2. Create integration_workstreams table
    op.create_table(
        "integration_workstreams",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("organization_id", uuid_type, sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("deal_id", uuid_type, sa.ForeignKey("deals.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("program_id", uuid_type, sa.ForeignKey("integration_programs.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("category", sa.String(100), nullable=False),  # 17 categories: EXECUTIVE_GOVERNANCE, FINANCE_ACCOUNTING, etc.
        sa.Column("owner", sa.String(100), nullable=True),
        sa.Column("executive_sponsor", sa.String(100), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="NOT_STARTED"),  # NOT_STARTED, PLANNED, IN_PROGRESS, AT_RISK, BLOCKED, COMPLETED, CANCELLED
        sa.Column("priority", sa.String(20), nullable=False, server_default="MEDIUM"),      # CRITICAL, HIGH, MEDIUM, LOW
        sa.Column("start_day", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("target_day", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("progress_pct", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("risk_level", sa.String(20), nullable=False, server_default="LOW"),       # HIGH, MEDIUM, LOW
        sa.Column("linked_synergy_ids", json_type, nullable=True),  # List of synergy UUIDs
        sa.Column("linked_risk_ids", json_type, nullable=True),     # List of risk UUIDs
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_by_id", uuid_type, sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )

    op.create_index(
        "ix_workstreams_org_deal",
        "integration_workstreams",
        ["organization_id", "deal_id"],
    )
    op.create_index(
        "ix_workstreams_program_cat",
        "integration_workstreams",
        ["program_id", "category"],
    )
    op.create_index(
        "ix_workstreams_status",
        "integration_workstreams",
        ["program_id", "status"],
    )

    # 3. Create integration_milestones table
    op.create_table(
        "integration_milestones",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("organization_id", uuid_type, sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("deal_id", uuid_type, sa.ForeignKey("deals.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("program_id", uuid_type, sa.ForeignKey("integration_programs.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("workstream_id", uuid_type, sa.ForeignKey("integration_workstreams.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("target_day", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("target_date", sa.Date(), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="NOT_STARTED"),  # NOT_STARTED, IN_PROGRESS, AT_RISK, BLOCKED, COMPLETED, OVERDUE
        sa.Column("priority", sa.String(20), nullable=False, server_default="MEDIUM"),      # CRITICAL, HIGH, MEDIUM, LOW
        sa.Column("owner", sa.String(100), nullable=True),
        sa.Column("completion_pct", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("is_critical_path", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("linked_synergy_id", uuid_type, sa.ForeignKey("synergy_opportunities.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("deliverable", sa.Text(), nullable=True),
        sa.Column("evidence_citation_ids", json_type, nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by_id", uuid_type, sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )

    op.create_index(
        "ix_milestones_workstream",
        "integration_milestones",
        ["workstream_id", "target_day"],
    )
    op.create_index(
        "ix_milestones_status",
        "integration_milestones",
        ["program_id", "status"],
    )

    # 4. Create integration_dependencies table
    op.create_table(
        "integration_dependencies",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("organization_id", uuid_type, sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("deal_id", uuid_type, sa.ForeignKey("deals.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("program_id", uuid_type, sa.ForeignKey("integration_programs.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("predecessor_id", uuid_type, sa.ForeignKey("integration_milestones.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("successor_id", uuid_type, sa.ForeignKey("integration_milestones.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("dependency_type", sa.String(50), nullable=False, server_default="FINISH_TO_START"),  # FINISH_TO_START, START_TO_START, FINISH_TO_FINISH
        sa.Column("is_blocking", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )

    op.create_index(
        "ix_dependencies_pred_succ",
        "integration_dependencies",
        ["predecessor_id", "successor_id"],
        unique=True,
    )

    # 5. Create integration_blockers table
    op.create_table(
        "integration_blockers",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("organization_id", uuid_type, sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("deal_id", uuid_type, sa.ForeignKey("deals.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("program_id", uuid_type, sa.ForeignKey("integration_programs.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("workstream_id", uuid_type, sa.ForeignKey("integration_workstreams.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("milestone_id", uuid_type, sa.ForeignKey("integration_milestones.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("severity", sa.String(20), nullable=False, server_default="HIGH"),  # CRITICAL, HIGH, MEDIUM
        sa.Column("status", sa.String(20), nullable=False, server_default="OPEN"),     # OPEN, RESOLVED
        sa.Column("owner", sa.String(100), nullable=True),
        sa.Column("resolution_notes", sa.Text(), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by_id", uuid_type, sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )

    op.create_index(
        "ix_blockers_workstream_status",
        "integration_blockers",
        ["workstream_id", "status"],
    )


def downgrade() -> None:
    op.drop_index("ix_blockers_workstream_status", table_name="integration_blockers")
    op.drop_table("integration_blockers")

    op.drop_index("ix_dependencies_pred_succ", table_name="integration_dependencies")
    op.drop_table("integration_dependencies")

    op.drop_index("ix_milestones_status", table_name="integration_milestones")
    op.drop_index("ix_milestones_workstream", table_name="integration_milestones")
    op.drop_table("integration_milestones")

    op.drop_index("ix_workstreams_status", table_name="integration_workstreams")
    op.drop_index("ix_workstreams_program_cat", table_name="integration_workstreams")
    op.drop_index("ix_workstreams_org_deal", table_name="integration_workstreams")
    op.drop_table("integration_workstreams")

    op.drop_index("ix_integration_programs_org_deal", table_name="integration_programs")
    op.drop_table("integration_programs")
