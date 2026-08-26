"""Operational, Technology & Product Architecture Diligence Intelligence Engine Tables.

Revision ID: 013_technology_operational_intelligence_engine
Revises: 012_legal_contract_intelligence_engine
Create Date: 2026-08-26 18:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "013_technology_operational_intelligence_engine"
down_revision: Union[str, None] = "012_legal_contract_intelligence_engine"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    is_postgres = bind.dialect.name == "postgresql"

    json_type = postgresql.JSONB(astext_type=sa.Text()) if is_postgres else sa.JSON()
    uuid_type = postgresql.UUID(as_uuid=True) if is_postgres else sa.String(36)

    # 1. Create technology_findings table
    op.create_table(
        "technology_findings",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("organization_id", uuid_type, sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("deal_id", uuid_type, sa.ForeignKey("deals.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("company_id", uuid_type, sa.ForeignKey("target_companies.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("document_id", uuid_type, sa.ForeignKey("documents.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("category", sa.String(100), nullable=False),  # 30 categories (TECHNOLOGY_DEBT, CLOUD_INFRASTRUCTURE, etc.)
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("technical_fact", sa.Text(), nullable=False),
        sa.Column("business_impact", sa.Text(), nullable=True),
        sa.Column("recommendation", sa.Text(), nullable=True),
        sa.Column("severity", sa.String(20), nullable=False, server_default="MEDIUM"),  # CRITICAL, HIGH, MEDIUM, LOW
        sa.Column("likelihood", sa.String(20), nullable=False, server_default="MEDIUM"),  # HIGH, MEDIUM, LOW
        sa.Column("confidence", sa.String(20), nullable=False, server_default="HIGH"),   # HIGH, MEDIUM, LOW
        sa.Column("monetary_exposure", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("status", sa.String(50), nullable=False, server_default="IDENTIFIED"),  # IDENTIFIED, REQUIRES_REVIEW, REMEDIATION_PLANNED, MITIGATED, ACCEPTED
        sa.Column("linked_risk_id", uuid_type, sa.ForeignKey("risks.id", ondelete="SET NULL"), nullable=True),
        sa.Column("linked_workstream_id", uuid_type, sa.ForeignKey("integration_workstreams.id", ondelete="SET NULL"), nullable=True),
        sa.Column("linked_milestone_id", uuid_type, sa.ForeignKey("integration_milestones.id", ondelete="SET NULL"), nullable=True),
        sa.Column("citation_id", uuid_type, sa.ForeignKey("citations.id", ondelete="SET NULL"), nullable=True),
        sa.Column("fingerprint", sa.String(64), nullable=False, index=True),
        sa.Column("created_by_id", uuid_type, sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )

    op.create_index(
        "ix_tech_findings_org_deal",
        "technology_findings",
        ["organization_id", "deal_id"],
    )
    op.create_index(
        "ix_tech_findings_deal_cat",
        "technology_findings",
        ["deal_id", "category"],
    )
    op.create_index(
        "ix_tech_findings_fingerprint",
        "technology_findings",
        ["deal_id", "fingerprint"],
        unique=True,
    )

    # 2. Create operational_metrics table
    op.create_table(
        "operational_metrics",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("organization_id", uuid_type, sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("deal_id", uuid_type, sa.ForeignKey("deals.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("company_id", uuid_type, sa.ForeignKey("target_companies.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("metric_category", sa.String(100), nullable=False),  # UPTIME_SLA, INCIDENT_MTTR, CLOUD_SPEND, BACKUP_RECOVERY, etc.
        sa.Column("metric_name", sa.String(255), nullable=False),
        sa.Column("observed_value", sa.Float(), nullable=False),
        sa.Column("target_value", sa.Float(), nullable=True),
        sa.Column("unit", sa.String(50), nullable=False, server_default="%"),
        sa.Column("deviation", sa.Float(), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="ON_TARGET"),  # ON_TARGET, DEVIATION, CRITICAL_BREACH
        sa.Column("evidence_summary", sa.Text(), nullable=True),
        sa.Column("citation_id", uuid_type, sa.ForeignKey("citations.id", ondelete="SET NULL"), nullable=True),
        sa.Column("fingerprint", sa.String(64), nullable=False, index=True),
        sa.Column("created_by_id", uuid_type, sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )

    op.create_index(
        "ix_op_metrics_deal_cat",
        "operational_metrics",
        ["deal_id", "metric_category"],
    )
    op.create_index(
        "ix_op_metrics_fingerprint",
        "operational_metrics",
        ["deal_id", "fingerprint"],
        unique=True,
    )

    # 3. Create technology_dependencies table
    op.create_table(
        "technology_dependencies",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("organization_id", uuid_type, sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("deal_id", uuid_type, sa.ForeignKey("deals.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("dependency_name", sa.String(255), nullable=False),
        sa.Column("dependency_type", sa.String(100), nullable=False),  # CLOUD_PROVIDER, SAAS_API, DATABASE, EXTERNAL_SERVICE
        sa.Column("provider", sa.String(255), nullable=False),
        sa.Column("purpose", sa.Text(), nullable=True),
        sa.Column("criticality", sa.String(20), nullable=False, server_default="HIGH"),  # CRITICAL, HIGH, MEDIUM, LOW
        sa.Column("failure_impact", sa.Text(), nullable=True),
        sa.Column("replacement_difficulty", sa.String(20), nullable=False, server_default="MEDIUM"),  # HIGH, MEDIUM, LOW
        sa.Column("is_single_point_of_failure", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("annual_cost", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("contract_id", uuid_type, sa.ForeignKey("contract_records.id", ondelete="SET NULL"), nullable=True),
        sa.Column("citation_id", uuid_type, sa.ForeignKey("citations.id", ondelete="SET NULL"), nullable=True),
        sa.Column("fingerprint", sa.String(64), nullable=False, index=True),
        sa.Column("created_by_id", uuid_type, sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )

    op.create_index(
        "ix_tech_deps_deal_criticality",
        "technology_dependencies",
        ["deal_id", "criticality"],
    )
    op.create_index(
        "ix_tech_deps_fingerprint",
        "technology_dependencies",
        ["deal_id", "fingerprint"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_tech_deps_fingerprint", table_name="technology_dependencies")
    op.drop_index("ix_tech_deps_deal_criticality", table_name="technology_dependencies")
    op.drop_table("technology_dependencies")

    op.drop_index("ix_op_metrics_fingerprint", table_name="operational_metrics")
    op.drop_index("ix_op_metrics_deal_cat", table_name="operational_metrics")
    op.drop_table("operational_metrics")

    op.drop_index("ix_tech_findings_fingerprint", table_name="technology_findings")
    op.drop_index("ix_tech_findings_deal_cat", table_name="technology_findings")
    op.drop_index("ix_tech_findings_org_deal", table_name="technology_findings")
    op.drop_table("technology_findings")
