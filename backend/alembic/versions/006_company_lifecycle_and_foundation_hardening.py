"""Company Lifecycle & Intelligence Foundation Hardening.

Revision ID: 006_company_lifecycle_and_foundation_hardening
Revises: 005_valuation_engine_tables
Create Date: 2026-08-26 16:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "006_company_lifecycle_and_foundation_hardening"
down_revision: Union[str, None] = "005_valuation_engine_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add company_type and lifecycle_stage to target_companies
    op.add_column(
        "target_companies",
        sa.Column("company_type", sa.String(50), server_default="TARGET_ACQUISITION", nullable=False),
    )
    op.add_column(
        "target_companies",
        sa.Column("lifecycle_stage", sa.String(50), server_default="DILIGENCE", nullable=False),
    )
    op.create_index(
        "ix_target_company_type_stage",
        "target_companies",
        ["organization_id", "company_type", "lifecycle_stage"],
    )

    # 2. Add source_entity_type to citations for cross-domain evidence binding
    op.add_column(
        "citations",
        sa.Column("source_entity_type", sa.String(50), server_default="DOCUMENT", nullable=False),
    )


def downgrade() -> None:
    op.drop_column("citations", "source_entity_type")
    op.drop_index("ix_target_company_type_stage", table_name="target_companies")
    op.drop_column("target_companies", "lifecycle_stage")
    op.drop_column("target_companies", "company_type")
