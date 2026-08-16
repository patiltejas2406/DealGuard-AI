"""Initial Schema: Tenancy, Deals, Documents, Financials, Risks, Auditing & pgvector.

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-08-16 16:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    is_postgres = bind.dialect.name == "postgresql"

    # 1. Enable pgvector extension on PostgreSQL
    if is_postgres:
        op.execute("CREATE EXTENSION IF NOT EXISTS vector;")

    # 2. Organizations
    op.create_table(
        "organizations",
        sa.Column("id", postgresql.UUID(as_uuid=True) if is_postgres else sa.String(36), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(100), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true" if is_postgres else "1"), nullable=False),
        sa.Column("tier", sa.String(50), server_default="ENTERPRISE", nullable=False),
        sa.Column("settings", postgresql.JSONB() if is_postgres else sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("slug", name="uq_organizations_slug"),
    )
    op.create_index("ix_organizations_id", "organizations", ["id"])
    op.create_index("ix_organizations_slug", "organizations", ["slug"])

    # 3. Users
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True) if is_postgres else sa.String(36), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true" if is_postgres else "1"), nullable=False),
        sa.Column("is_superuser", sa.Boolean(), server_default=sa.text("false" if is_postgres else "0"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    op.create_index("ix_users_id", "users", ["id"])
    op.create_index("ix_users_email", "users", ["email"])

    # 4. Roles
    op.create_table(
        "roles",
        sa.Column("id", postgresql.UUID(as_uuid=True) if is_postgres else sa.String(36), primary_key=True),
        sa.Column("name", sa.String(50), nullable=False),
        sa.Column("description", sa.String(255), nullable=True),
        sa.Column("permissions", postgresql.JSONB() if is_postgres else sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("name", name="uq_roles_name"),
    )
    op.create_index("ix_roles_id", "roles", ["id"])
    op.create_index("ix_roles_name", "roles", ["name"])

    # 5. Organization Memberships
    op.create_table(
        "organization_memberships",
        sa.Column("id", postgresql.UUID(as_uuid=True) if is_postgres else sa.String(36), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True) if is_postgres else sa.String(36), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True) if is_postgres else sa.String(36), nullable=False),
        sa.Column("role_id", postgresql.UUID(as_uuid=True) if is_postgres else sa.String(36), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true" if is_postgres else "1"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("organization_id", "user_id", name="uq_org_user_membership"),
    )
    op.create_index("ix_org_membership_lookup", "organization_memberships", ["organization_id", "user_id"])

    # 6. Target Companies
    op.create_table(
        "target_companies",
        sa.Column("id", postgresql.UUID(as_uuid=True) if is_postgres else sa.String(36), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True) if is_postgres else sa.String(36), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("legal_name", sa.String(255), nullable=True),
        sa.Column("industry", sa.String(100), nullable=False),
        sa.Column("sector", sa.String(100), nullable=True),
        sa.Column("headquarters", sa.String(255), nullable=True),
        sa.Column("website", sa.String(255), nullable=True),
        sa.Column("founding_year", sa.Integer(), nullable=True),
        sa.Column("employee_count", sa.Integer(), nullable=True),
        sa.Column("description", sa.String(2000), nullable=True),
        sa.Column("metadata_json", postgresql.JSONB() if is_postgres else sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_target_company_org_name", "target_companies", ["organization_id", "name"])

    # 7. Deals
    op.create_table(
        "deals",
        sa.Column("id", postgresql.UUID(as_uuid=True) if is_postgres else sa.String(36), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True) if is_postgres else sa.String(36), nullable=False),
        sa.Column("target_company_id", postgresql.UUID(as_uuid=True) if is_postgres else sa.String(36), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("code_name", sa.String(100), nullable=True),
        sa.Column("deal_type", sa.String(50), server_default="M_AND_A_BUY_SIDE", nullable=False),
        sa.Column("stage", sa.String(50), server_default="PRE_DILIGENCE", nullable=False),
        sa.Column("status", sa.String(50), server_default="ACTIVE", nullable=False),
        sa.Column("target_ev", sa.Float(), nullable=True),
        sa.Column("currency", sa.String(3), server_default="USD", nullable=False),
        sa.Column("decision_score", sa.Float(), nullable=True),
        sa.Column("created_by_id", postgresql.UUID(as_uuid=True) if is_postgres else sa.String(36), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["target_company_id"], ["target_companies.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_deals_org_stage", "deals", ["organization_id", "stage"])
    op.create_index("ix_deals_org_status", "deals", ["organization_id", "status"])

    # 8. Deal Members
    op.create_table(
        "deal_members",
        sa.Column("id", postgresql.UUID(as_uuid=True) if is_postgres else sa.String(36), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True) if is_postgres else sa.String(36), nullable=False),
        sa.Column("deal_id", postgresql.UUID(as_uuid=True) if is_postgres else sa.String(36), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True) if is_postgres else sa.String(36), nullable=False),
        sa.Column("deal_role", sa.String(50), server_default="ANALYST", nullable=False),
        sa.Column("can_edit", sa.Boolean(), server_default=sa.text("true" if is_postgres else "1"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["deal_id"], ["deals.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("deal_id", "user_id", name="uq_deal_user_membership"),
    )
    op.create_index("ix_deal_members_lookup", "deal_members", ["organization_id", "deal_id", "user_id"])

    # 9. Documents
    op.create_table(
        "documents",
        sa.Column("id", postgresql.UUID(as_uuid=True) if is_postgres else sa.String(36), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True) if is_postgres else sa.String(36), nullable=False),
        sa.Column("deal_id", postgresql.UUID(as_uuid=True) if is_postgres else sa.String(36), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("file_type", sa.String(20), nullable=False),
        sa.Column("mime_type", sa.String(100), nullable=False),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("storage_path", sa.String(500), nullable=False),
        sa.Column("sha256_hash", sa.String(64), nullable=False),
        sa.Column("status", sa.String(50), server_default="UPLOADED", nullable=False),
        sa.Column("doc_category", sa.String(50), nullable=True),
        sa.Column("uploaded_by_id", postgresql.UUID(as_uuid=True) if is_postgres else sa.String(36), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["deal_id"], ["deals.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["uploaded_by_id"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_documents_org_deal", "documents", ["organization_id", "deal_id"])
    op.create_index("ix_documents_deal_hash", "documents", ["deal_id", "sha256_hash"])

    # 10. Document Versions
    op.create_table(
        "document_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True) if is_postgres else sa.String(36), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True) if is_postgres else sa.String(36), nullable=False),
        sa.Column("document_id", postgresql.UUID(as_uuid=True) if is_postgres else sa.String(36), nullable=False),
        sa.Column("version_number", sa.Integer(), server_default="1", nullable=False),
        sa.Column("storage_path", sa.String(500), nullable=False),
        sa.Column("sha256_hash", sa.String(64), nullable=False),
        sa.Column("parsing_status", sa.String(50), server_default="PENDING", nullable=False),
        sa.Column("page_count", sa.Integer(), nullable=True),
        sa.Column("table_count", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("document_id", "version_number", name="uq_doc_version"),
    )

    # 11. Document Chunks (with 1536-dim vector)
    chunk_columns = [
        sa.Column("id", postgresql.UUID(as_uuid=True) if is_postgres else sa.String(36), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True) if is_postgres else sa.String(36), nullable=False),
        sa.Column("document_id", postgresql.UUID(as_uuid=True) if is_postgres else sa.String(36), nullable=False),
        sa.Column("deal_id", postgresql.UUID(as_uuid=True) if is_postgres else sa.String(36), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("page_number", sa.Integer(), server_default="1", nullable=False),
        sa.Column("section_title", sa.String(255), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("token_count", sa.Integer(), nullable=True),
        sa.Column("embedding_model", sa.String(100), server_default="gemini-embedding-2", nullable=False),
        sa.Column("metadata_json", postgresql.JSONB() if is_postgres else sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["deal_id"], ["deals.id"], ondelete="CASCADE"),
    ]
    if is_postgres:
        from pgvector.sqlalchemy import Vector
        chunk_columns.append(sa.Column("embedding", Vector(1536), nullable=True))
    else:
        chunk_columns.append(sa.Column("embedding", sa.Text(), nullable=True))

    op.create_table("document_chunks", *chunk_columns)
    op.create_index("ix_chunks_org_deal_page", "document_chunks", ["organization_id", "deal_id", "page_number"])

    # 12. Citations
    op.create_table(
        "citations",
        sa.Column("id", postgresql.UUID(as_uuid=True) if is_postgres else sa.String(36), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True) if is_postgres else sa.String(36), nullable=False),
        sa.Column("deal_id", postgresql.UUID(as_uuid=True) if is_postgres else sa.String(36), nullable=False),
        sa.Column("document_id", postgresql.UUID(as_uuid=True) if is_postgres else sa.String(36), nullable=False),
        sa.Column("chunk_id", postgresql.UUID(as_uuid=True) if is_postgres else sa.String(36), nullable=True),
        sa.Column("page_number", sa.Integer(), nullable=False),
        sa.Column("section", sa.String(255), nullable=True),
        sa.Column("exact_quote", sa.Text(), nullable=False),
        sa.Column("char_offset_start", sa.Integer(), nullable=True),
        sa.Column("char_offset_end", sa.Integer(), nullable=True),
        sa.Column("extraction_method", sa.String(50), server_default="PARSER_TABLE", nullable=False),
        sa.Column("confidence_score", sa.Float(), server_default="1.0", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["deal_id"], ["deals.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["chunk_id"], ["document_chunks.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_citations_deal_doc", "citations", ["deal_id", "document_id"])

    # 13. Financial Statements
    op.create_table(
        "financial_statements",
        sa.Column("id", postgresql.UUID(as_uuid=True) if is_postgres else sa.String(36), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True) if is_postgres else sa.String(36), nullable=False),
        sa.Column("deal_id", postgresql.UUID(as_uuid=True) if is_postgres else sa.String(36), nullable=False),
        sa.Column("statement_type", sa.String(50), nullable=False),
        sa.Column("period_type", sa.String(20), server_default="ANNUAL", nullable=False),
        sa.Column("fiscal_year", sa.Integer(), nullable=False),
        sa.Column("fiscal_period", sa.String(20), nullable=False),
        sa.Column("period_end_date", sa.Date(), nullable=True),
        sa.Column("source_currency", sa.String(3), server_default="USD", nullable=False),
        sa.Column("is_audited", sa.Boolean(), server_default=sa.text("false" if is_postgres else "0"), nullable=False),
        sa.Column("is_normalized", sa.Boolean(), server_default=sa.text("false" if is_postgres else "0"), nullable=False),
        sa.Column("source_document_id", postgresql.UUID(as_uuid=True) if is_postgres else sa.String(36), nullable=True),
        sa.Column("line_items", postgresql.JSONB() if is_postgres else sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["deal_id"], ["deals.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["source_document_id"], ["documents.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("deal_id", "statement_type", "fiscal_period", name="uq_deal_stmt_period"),
    )
    op.create_index("ix_fin_stmt_lookup", "financial_statements", ["organization_id", "deal_id", "statement_type"])

    # 14. Financial Metrics
    op.create_table(
        "financial_metrics",
        sa.Column("id", postgresql.UUID(as_uuid=True) if is_postgres else sa.String(36), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True) if is_postgres else sa.String(36), nullable=False),
        sa.Column("deal_id", postgresql.UUID(as_uuid=True) if is_postgres else sa.String(36), nullable=False),
        sa.Column("statement_id", postgresql.UUID(as_uuid=True) if is_postgres else sa.String(36), nullable=True),
        sa.Column("citation_id", postgresql.UUID(as_uuid=True) if is_postgres else sa.String(36), nullable=True),
        sa.Column("metric_name", sa.String(100), nullable=False),
        sa.Column("period", sa.String(20), nullable=False),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column("unit", sa.String(20), server_default="CURRENCY", nullable=False),
        sa.Column("source_currency", sa.String(3), server_default="USD", nullable=False),
        sa.Column("is_normalized", sa.Boolean(), server_default=sa.text("false" if is_postgres else "0"), nullable=False),
        sa.Column("calculation_formula", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["deal_id"], ["deals.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["statement_id"], ["financial_statements.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["citation_id"], ["citations.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_fin_metrics_deal_metric", "financial_metrics", ["deal_id", "metric_name", "period"])

    # 15. Risks
    op.create_table(
        "risks",
        sa.Column("id", postgresql.UUID(as_uuid=True) if is_postgres else sa.String(36), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True) if is_postgres else sa.String(36), nullable=False),
        sa.Column("deal_id", postgresql.UUID(as_uuid=True) if is_postgres else sa.String(36), nullable=False),
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("severity", sa.Integer(), nullable=False),
        sa.Column("likelihood", sa.Integer(), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(50), server_default="IDENTIFIED", nullable=False),
        sa.Column("mitigation_strategy", sa.Text(), nullable=True),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True) if is_postgres else sa.String(36), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["deal_id"], ["deals.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_risks_org_deal_cat", "risks", ["organization_id", "deal_id", "category"])

    # 16. Risk Evidence
    op.create_table(
        "risk_evidence",
        sa.Column("id", postgresql.UUID(as_uuid=True) if is_postgres else sa.String(36), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True) if is_postgres else sa.String(36), nullable=False),
        sa.Column("deal_id", postgresql.UUID(as_uuid=True) if is_postgres else sa.String(36), nullable=False),
        sa.Column("risk_id", postgresql.UUID(as_uuid=True) if is_postgres else sa.String(36), nullable=False),
        sa.Column("citation_id", postgresql.UUID(as_uuid=True) if is_postgres else sa.String(36), nullable=False),
        sa.Column("relevance_explanation", sa.Text(), nullable=True),
        sa.Column("weight", sa.Float(), server_default="1.0", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["deal_id"], ["deals.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["risk_id"], ["risks.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["citation_id"], ["citations.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_risk_evidence_lookup", "risk_evidence", ["risk_id", "citation_id"])

    # 17. Audit Events
    op.create_table(
        "audit_events",
        sa.Column("id", postgresql.UUID(as_uuid=True) if is_postgres else sa.String(36), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True) if is_postgres else sa.String(36), nullable=False),
        sa.Column("deal_id", postgresql.UUID(as_uuid=True) if is_postgres else sa.String(36), nullable=True),
        sa.Column("actor_user_id", postgresql.UUID(as_uuid=True) if is_postgres else sa.String(36), nullable=True),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("entity_type", sa.String(100), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True) if is_postgres else sa.String(36), nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("details", postgresql.JSONB() if is_postgres else sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["deal_id"], ["deals.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_audit_org_action_created", "audit_events", ["organization_id", "action", "created_at"])

    # 18. Human Reviews
    op.create_table(
        "human_reviews",
        sa.Column("id", postgresql.UUID(as_uuid=True) if is_postgres else sa.String(36), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True) if is_postgres else sa.String(36), nullable=False),
        sa.Column("deal_id", postgresql.UUID(as_uuid=True) if is_postgres else sa.String(36), nullable=False),
        sa.Column("reviewer_user_id", postgresql.UUID(as_uuid=True) if is_postgres else sa.String(36), nullable=False),
        sa.Column("target_entity_type", sa.String(100), nullable=False),
        sa.Column("target_entity_id", postgresql.UUID(as_uuid=True) if is_postgres else sa.String(36), nullable=False),
        sa.Column("review_action", sa.String(50), nullable=False),
        sa.Column("original_value", postgresql.JSONB() if is_postgres else sa.Text(), nullable=True),
        sa.Column("reviewed_value", postgresql.JSONB() if is_postgres else sa.Text(), nullable=True),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["deal_id"], ["deals.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["reviewer_user_id"], ["users.id"], ondelete="RESTRICT"),
    )
    op.create_index("ix_human_reviews_target", "human_reviews", ["deal_id", "target_entity_type", "target_entity_id"])

    # 19. Job Executions
    op.create_table(
        "job_executions",
        sa.Column("id", postgresql.UUID(as_uuid=True) if is_postgres else sa.String(36), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True) if is_postgres else sa.String(36), nullable=False),
        sa.Column("deal_id", postgresql.UUID(as_uuid=True) if is_postgres else sa.String(36), nullable=True),
        sa.Column("celery_task_id", sa.String(255), nullable=True),
        sa.Column("job_type", sa.String(100), nullable=False),
        sa.Column("status", sa.String(50), server_default="QUEUED", nullable=False),
        sa.Column("progress_pct", sa.Integer(), server_default="0", nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("result_metadata", postgresql.JSONB() if is_postgres else sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["deal_id"], ["deals.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_job_executions_org_status", "job_executions", ["organization_id", "status"])


def downgrade() -> None:
    op.drop_table("job_executions")
    op.drop_table("human_reviews")
    op.drop_table("audit_events")
    op.drop_table("risk_evidence")
    op.drop_table("risks")
    op.drop_table("financial_metrics")
    op.drop_table("financial_statements")
    op.drop_table("citations")
    op.drop_table("document_chunks")
    op.drop_table("document_versions")
    op.drop_table("documents")
    op.drop_table("deal_members")
    op.drop_table("deals")
    op.drop_table("target_companies")
    op.drop_table("organization_memberships")
    op.drop_table("roles")
    op.drop_table("users")
    op.drop_table("organizations")
