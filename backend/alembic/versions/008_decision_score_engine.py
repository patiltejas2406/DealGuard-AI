"""Composite DealGuard Decision Score & Explainable Decision Intelligence Tables.

Revision ID: 008_decision_score_engine
Revises: 007_risk_intelligence_engine
Create Date: 2026-08-26 17:05:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "008_decision_score_engine"
down_revision: Union[str, None] = "007_risk_intelligence_engine"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    is_postgres = bind.dialect.name == "postgresql"

    json_type = postgresql.JSONB(astext_type=sa.Text()) if is_postgres else sa.JSON()
    uuid_type = postgresql.UUID(as_uuid=True) if is_postgres else sa.String(36)

    # Create decision_scores table
    op.create_table(
        "decision_scores",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("organization_id", uuid_type, sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("deal_id", uuid_type, sa.ForeignKey("deals.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("company_id", uuid_type, sa.ForeignKey("target_companies.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("score_type", sa.String(50), nullable=False, server_default="DEAL"),
        sa.Column("overall_score", sa.Float(), nullable=False),
        sa.Column("decision_band", sa.String(30), nullable=False),  # STRONG, FAVORABLE, CAUTION, HIGH_RISK, AVOID
        sa.Column("confidence_score", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("scoring_version", sa.String(20), nullable=False, server_default="1.0"),
        sa.Column("weights_used", json_type, nullable=False),
        sa.Column("component_scores", json_type, nullable=False),
        sa.Column("positive_drivers", json_type, nullable=True),
        sa.Column("negative_drivers", json_type, nullable=True),
        sa.Column("missing_information", json_type, nullable=True),
        sa.Column("recommendations", json_type, nullable=True),
        sa.Column("calculated_by_id", uuid_type, sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )

    op.create_index(
        "ix_decision_scores_org_deal",
        "decision_scores",
        ["organization_id", "deal_id"],
    )
    op.create_index(
        "ix_decision_scores_deal_created",
        "decision_scores",
        ["deal_id", "created_at"],
    )
    op.create_index(
        "ix_decision_scores_score_type",
        "decision_scores",
        ["deal_id", "score_type"],
    )


def downgrade() -> None:
    op.drop_index("ix_decision_scores_score_type", table_name="decision_scores")
    op.drop_index("ix_decision_scores_deal_created", table_name="decision_scores")
    op.drop_index("ix_decision_scores_org_deal", table_name="decision_scores")
    op.drop_table("decision_scores")
