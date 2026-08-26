"""Legal, Contract & Compliance Diligence Intelligence Engine Tables.

Revision ID: 012_legal_contract_intelligence_engine
Revises: 011_integration_execution_engine
Create Date: 2026-08-26 18:05:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "012_legal_contract_intelligence_engine"
down_revision: Union[str, None] = "011_integration_execution_engine"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    is_postgres = bind.dialect.name == "postgresql"

    json_type = postgresql.JSONB(astext_type=sa.Text()) if is_postgres else sa.JSON()
    uuid_type = postgresql.UUID(as_uuid=True) if is_postgres else sa.String(36)

    # 1. Create contract_records table
    op.create_table(
        "contract_records",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("organization_id", uuid_type, sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("deal_id", uuid_type, sa.ForeignKey("deals.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("company_id", uuid_type, sa.ForeignKey("target_companies.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("document_id", uuid_type, sa.ForeignKey("documents.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("contract_type", sa.String(100), nullable=False, server_default="CUSTOMER_MSA"),  # CUSTOMER_MSA, VENDOR_SaaS, EMPLOYMENT, IP_ASSIGNMENT, etc.
        sa.Column("counterparty", sa.String(255), nullable=False),
        sa.Column("effective_date", sa.Date(), nullable=True),
        sa.Column("expiration_date", sa.Date(), nullable=True),
        sa.Column("auto_renewal", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("annual_value", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("currency", sa.String(10), nullable=False, server_default="USD"),
        sa.Column("governing_law", sa.String(100), nullable=True),
        sa.Column("jurisdiction", sa.String(100), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="ACTIVE"),  # ACTIVE, EXPIRING_SOON, EXPIRED, TERMINATED
        sa.Column("citation_id", uuid_type, sa.ForeignKey("citations.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_by_id", uuid_type, sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )

    op.create_index(
        "ix_contracts_org_deal",
        "contract_records",
        ["organization_id", "deal_id"],
    )
    op.create_index(
        "ix_contracts_deal_type",
        "contract_records",
        ["deal_id", "contract_type"],
    )

    # 2. Create contract_clauses table
    op.create_table(
        "contract_clauses",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("organization_id", uuid_type, sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("deal_id", uuid_type, sa.ForeignKey("deals.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("contract_id", uuid_type, sa.ForeignKey("contract_records.id", ondelete="CASCADE"), nullable=True, index=True),
        sa.Column("document_id", uuid_type, sa.ForeignKey("documents.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("category", sa.String(100), nullable=False),  # 32 categories (CHANGE_OF_CONTROL, ASSIGNMENT_RESTRICTION, etc.)
        sa.Column("clause_title", sa.String(255), nullable=False),
        sa.Column("clause_text", sa.Text(), nullable=False),
        sa.Column("normalized_summary", sa.Text(), nullable=True),
        sa.Column("page_number", sa.Integer(), nullable=True),
        sa.Column("section_reference", sa.String(100), nullable=True),
        sa.Column("requires_consent", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("requires_notice", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("notice_period_days", sa.Integer(), nullable=True),
        sa.Column("severity", sa.String(20), nullable=False, server_default="MEDIUM"),  # CRITICAL, HIGH, MEDIUM, LOW
        sa.Column("confidence", sa.String(20), nullable=False, server_default="HIGH"),   # HIGH, MEDIUM, LOW
        sa.Column("citation_id", uuid_type, sa.ForeignKey("citations.id", ondelete="SET NULL"), nullable=True),
        sa.Column("fingerprint", sa.String(64), nullable=False, index=True),  # SHA-256 for idempotency
        sa.Column("created_by_id", uuid_type, sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )

    op.create_index(
        "ix_clauses_deal_category",
        "contract_clauses",
        ["deal_id", "category"],
    )
    op.create_index(
        "ix_clauses_fingerprint",
        "contract_clauses",
        ["deal_id", "fingerprint"],
        unique=True,
    )

    # 3. Create legal_findings table
    op.create_table(
        "legal_findings",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("organization_id", uuid_type, sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("deal_id", uuid_type, sa.ForeignKey("deals.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("contract_id", uuid_type, sa.ForeignKey("contract_records.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("clause_id", uuid_type, sa.ForeignKey("contract_clauses.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("finding_type", sa.String(100), nullable=False),  # CHANGE_OF_CONTROL_CONSENT, EXCLUSIVITY_RESTRICTION, IP_ASSIGNMENT_GAP, etc.
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("legal_fact", sa.Text(), nullable=False),
        sa.Column("business_impact", sa.Text(), nullable=True),
        sa.Column("recommendation", sa.Text(), nullable=True),
        sa.Column("severity", sa.String(20), nullable=False, server_default="MEDIUM"),  # CRITICAL, HIGH, MEDIUM, LOW
        sa.Column("status", sa.String(50), nullable=False, server_default="IDENTIFIED"),  # IDENTIFIED, REQUIRES_REVIEW, ACTION_PLANNED, CONSENT_OBTAINED, MITIGATED, ACCEPTED
        sa.Column("monetary_exposure", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("currency", sa.String(10), nullable=False, server_default="USD"),
        sa.Column("linked_risk_id", uuid_type, sa.ForeignKey("risks.id", ondelete="SET NULL"), nullable=True),
        sa.Column("linked_synergy_id", uuid_type, sa.ForeignKey("synergy_opportunities.id", ondelete="SET NULL"), nullable=True),
        sa.Column("linked_workstream_id", uuid_type, sa.ForeignKey("integration_workstreams.id", ondelete="SET NULL"), nullable=True),
        sa.Column("linked_milestone_id", uuid_type, sa.ForeignKey("integration_milestones.id", ondelete="SET NULL"), nullable=True),
        sa.Column("citation_id", uuid_type, sa.ForeignKey("citations.id", ondelete="SET NULL"), nullable=True),
        sa.Column("fingerprint", sa.String(64), nullable=False, index=True),
        sa.Column("created_by_id", uuid_type, sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )

    op.create_index(
        "ix_findings_deal_type",
        "legal_findings",
        ["deal_id", "finding_type"],
    )
    op.create_index(
        "ix_findings_fingerprint",
        "legal_findings",
        ["deal_id", "fingerprint"],
        unique=True,
    )

    # 4. Create compliance_requirements table
    op.create_table(
        "compliance_requirements",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("organization_id", uuid_type, sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("deal_id", uuid_type, sa.ForeignKey("deals.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("company_id", uuid_type, sa.ForeignKey("target_companies.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("framework", sa.String(100), nullable=False),  # GDPR, SOC2, HIPAA, CCPA, CYBERSECURITY, REGULATORY_LICENSES, etc.
        sa.Column("requirement_name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="REQUIRES_REVIEW"),  # EVIDENCE_PRESENT, EVIDENCE_MISSING, POTENTIAL_GAP, REQUIRES_REVIEW, COMPLIANT
        sa.Column("confidence", sa.String(20), nullable=False, server_default="MEDIUM"),      # HIGH, MEDIUM, LOW
        sa.Column("evidence_summary", sa.Text(), nullable=True),
        sa.Column("citation_ids", json_type, nullable=True),
        sa.Column("remediation_action", sa.Text(), nullable=True),
        sa.Column("remediation_deadline", sa.Date(), nullable=True),
        sa.Column("created_by_id", uuid_type, sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )

    op.create_index(
        "ix_compliance_deal_framework",
        "compliance_requirements",
        ["deal_id", "framework"],
    )


def downgrade() -> None:
    op.drop_index("ix_compliance_deal_framework", table_name="compliance_requirements")
    op.drop_table("compliance_requirements")

    op.drop_index("ix_findings_fingerprint", table_name="legal_findings")
    op.drop_index("ix_findings_deal_type", table_name="legal_findings")
    op.drop_table("legal_findings")

    op.drop_index("ix_clauses_fingerprint", table_name="contract_clauses")
    op.drop_index("ix_clauses_deal_category", table_name="contract_clauses")
    op.drop_table("contract_clauses")

    op.drop_index("ix_contracts_deal_type", table_name="contract_records")
    op.drop_index("ix_contracts_org_deal", table_name="contract_records")
    op.drop_table("contract_records")
