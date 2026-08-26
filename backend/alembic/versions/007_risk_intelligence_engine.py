"""17-Pillar Risk Intelligence Engine Tables & Columns.

Revision ID: 007_risk_intelligence_engine
Revises: 006_company_lifecycle_and_foundation_hardening
Create Date: 2026-08-26 16:45:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "007_risk_intelligence_engine"
down_revision: Union[str, None] = "006_company_lifecycle_and_foundation_hardening"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    is_postgres = bind.dialect.name == "postgresql"

    # Add columns to risks table for Phase 7
    op.add_column(
        "risks",
        sa.Column("risk_level", sa.String(20), server_default="MODERATE", nullable=False),
    )
    op.add_column(
        "risks",
        sa.Column("detection_source", sa.String(30), server_default="MANUAL_ENTRY", nullable=False),
    )
    op.add_column(
        "risks",
        sa.Column("confidence_score", sa.Float(), nullable=True),
    )
    op.add_column(
        "risks",
        sa.Column("recommendation", sa.Text(), nullable=True),
    )
    op.add_column(
        "risks",
        sa.Column("fingerprint", sa.String(64), nullable=True),
    )
    op.add_column(
        "risks",
        sa.Column(
            "company_id",
            postgresql.UUID(as_uuid=True) if is_postgres else sa.String(36),
            nullable=True,
        ),
    )

    # Foreign key for company_id if exists
    try:
        op.create_foreign_key(
            "fk_risks_company_id",
            "risks",
            "target_companies",
            ["company_id"],
            ["id"],
            ondelete="SET NULL",
        )
    except Exception:
        pass

    # Create indices
    op.create_index("ix_risks_deal_level", "risks", ["deal_id", "risk_level"])
    op.create_index("ix_risks_deal_fingerprint", "risks", ["deal_id", "fingerprint"])
    op.create_index("ix_risks_company", "risks", ["organization_id", "company_id"])


def downgrade() -> None:
    op.drop_index("ix_risks_company", table_name="risks")
    op.drop_index("ix_risks_deal_fingerprint", table_name="risks")
    op.drop_index("ix_risks_deal_level", table_name="risks")
    try:
        op.drop_constraint("fk_risks_company_id", "risks", type_="foreignkey")
    except Exception:
        pass
    op.drop_column("risks", "company_id")
    op.drop_column("risks", "fingerprint")
    op.drop_column("risks", "recommendation")
    op.drop_column("risks", "confidence_score")
    op.drop_column("risks", "detection_source")
    op.drop_column("risks", "risk_level")
