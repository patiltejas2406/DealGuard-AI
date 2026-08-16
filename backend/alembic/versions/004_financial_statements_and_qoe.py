"""Quality of Earnings (QoE) Adjustments and Financial Statement Tables.

Revision ID: 004_financial_statements_and_qoe
Revises: 003_document_pipeline_and_jobs
Create Date: 2026-08-16 17:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "004_financial_statements_and_qoe"
down_revision: Union[str, None] = "003_document_pipeline_and_jobs"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    is_postgres = bind.dialect.name == "postgresql"

    op.create_table(
        "qoe_adjustments",
        sa.Column("id", postgresql.UUID(as_uuid=True) if is_postgres else sa.String(36), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True) if is_postgres else sa.String(36), nullable=False),
        sa.Column("deal_id", postgresql.UUID(as_uuid=True) if is_postgres else sa.String(36), nullable=False),
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("description", sa.String(255), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("currency", sa.String(3), server_default="USD", nullable=False),
        sa.Column("period", sa.String(20), server_default="FY2023", nullable=False),
        sa.Column("treatment", sa.String(20), server_default="ADD_BACK", nullable=False),
        sa.Column("status", sa.String(20), server_default="PROPOSED", nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("citation_id", postgresql.UUID(as_uuid=True) if is_postgres else sa.String(36), nullable=True),
        sa.Column("created_by_id", postgresql.UUID(as_uuid=True) if is_postgres else sa.String(36), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["deal_id"], ["deals.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["citation_id"], ["citations.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_qoe_deal_period", "qoe_adjustments", ["deal_id", "period"])
    op.create_index("ix_qoe_org_status", "qoe_adjustments", ["organization_id", "status"])


def downgrade() -> None:
    op.drop_index("ix_qoe_org_status", table_name="qoe_adjustments")
    op.drop_index("ix_qoe_deal_period", table_name="qoe_adjustments")
    op.drop_table("qoe_adjustments")
