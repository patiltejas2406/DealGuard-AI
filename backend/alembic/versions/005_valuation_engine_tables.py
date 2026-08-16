"""Valuation Engine: DCF, WACC, Comparables, Precedents, and Outputs.

Revision ID: 005_valuation_engine_tables
Revises: 004_financial_statements_and_qoe
Create Date: 2026-08-16 18:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "005_valuation_engine_tables"
down_revision: Union[str, None] = "004_financial_statements_and_qoe"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    is_postgres = bind.dialect.name == "postgresql"

    # 1. valuations
    op.create_table(
        "valuations",
        sa.Column("id", postgresql.UUID(as_uuid=True) if is_postgres else sa.String(36), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True) if is_postgres else sa.String(36), nullable=False),
        sa.Column("deal_id", postgresql.UUID(as_uuid=True) if is_postgres else sa.String(36), nullable=False),
        sa.Column("title", sa.String(255), server_default="Base Case Valuation", nullable=False),
        sa.Column("status", sa.String(20), server_default="ACTIVE", nullable=False),
        sa.Column("selected_method", sa.String(50), server_default="DCF", nullable=False),
        sa.Column("currency", sa.String(3), server_default="USD", nullable=False),
        sa.Column("proposed_ev", sa.Float(), nullable=True),
        sa.Column("proposed_equity_value", sa.Float(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_by_id", postgresql.UUID(as_uuid=True) if is_postgres else sa.String(36), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["deal_id"], ["deals.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_valuations_org_deal", "valuations", ["organization_id", "deal_id"])
    op.create_index("ix_valuations_status", "valuations", ["deal_id", "status"])

    # 2. valuation_assumptions
    op.create_table(
        "valuation_assumptions",
        sa.Column("id", postgresql.UUID(as_uuid=True) if is_postgres else sa.String(36), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True) if is_postgres else sa.String(36), nullable=False),
        sa.Column("deal_id", postgresql.UUID(as_uuid=True) if is_postgres else sa.String(36), nullable=False),
        sa.Column("valuation_id", postgresql.UUID(as_uuid=True) if is_postgres else sa.String(36), nullable=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("category", sa.String(50), server_default="WACC", nullable=False),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column("unit", sa.String(20), server_default="PERCENTAGE", nullable=False),
        sa.Column("period", sa.String(20), nullable=True),
        sa.Column("source_type", sa.String(30), server_default="ANALYST_INPUT", nullable=False),
        sa.Column("is_analyst_entered", sa.Boolean(), server_default=sa.text("1" if not is_postgres else "true"), nullable=False),
        sa.Column("confidence_score", sa.Float(), nullable=True),
        sa.Column("citation_id", postgresql.UUID(as_uuid=True) if is_postgres else sa.String(36), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["deal_id"], ["deals.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["valuation_id"], ["valuations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["citation_id"], ["citations.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_val_assumptions_deal_name", "valuation_assumptions", ["deal_id", "name"])
    op.create_index("ix_val_assumptions_valuation", "valuation_assumptions", ["valuation_id", "category"])

    # 3. comparable_companies
    op.create_table(
        "comparable_companies",
        sa.Column("id", postgresql.UUID(as_uuid=True) if is_postgres else sa.String(36), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True) if is_postgres else sa.String(36), nullable=False),
        sa.Column("deal_id", postgresql.UUID(as_uuid=True) if is_postgres else sa.String(36), nullable=False),
        sa.Column("valuation_id", postgresql.UUID(as_uuid=True) if is_postgres else sa.String(36), nullable=True),
        sa.Column("company_name", sa.String(255), nullable=False),
        sa.Column("ticker", sa.String(20), nullable=True),
        sa.Column("industry", sa.String(100), nullable=True),
        sa.Column("geography", sa.String(100), nullable=True),
        sa.Column("revenue", sa.Float(), nullable=True),
        sa.Column("ebitda", sa.Float(), nullable=True),
        sa.Column("ebit", sa.Float(), nullable=True),
        sa.Column("net_income", sa.Float(), nullable=True),
        sa.Column("enterprise_value", sa.Float(), nullable=True),
        sa.Column("equity_value", sa.Float(), nullable=True),
        sa.Column("ev_to_revenue", sa.Float(), nullable=True),
        sa.Column("ev_to_ebitda", sa.Float(), nullable=True),
        sa.Column("pe_ratio", sa.Float(), nullable=True),
        sa.Column("revenue_growth", sa.Float(), nullable=True),
        sa.Column("status", sa.String(20), server_default="INCLUDED", nullable=False),
        sa.Column("source", sa.String(100), server_default="ANALYST_INPUT", nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("citation_id", postgresql.UUID(as_uuid=True) if is_postgres else sa.String(36), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["deal_id"], ["deals.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["valuation_id"], ["valuations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["citation_id"], ["citations.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_comps_deal_status", "comparable_companies", ["deal_id", "status"])

    # 4. precedent_transactions
    op.create_table(
        "precedent_transactions",
        sa.Column("id", postgresql.UUID(as_uuid=True) if is_postgres else sa.String(36), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True) if is_postgres else sa.String(36), nullable=False),
        sa.Column("deal_id", postgresql.UUID(as_uuid=True) if is_postgres else sa.String(36), nullable=False),
        sa.Column("valuation_id", postgresql.UUID(as_uuid=True) if is_postgres else sa.String(36), nullable=True),
        sa.Column("target_name", sa.String(255), nullable=False),
        sa.Column("acquirer_name", sa.String(255), nullable=True),
        sa.Column("announcement_date", sa.String(20), nullable=True),
        sa.Column("transaction_value", sa.Float(), nullable=True),
        sa.Column("enterprise_value", sa.Float(), nullable=True),
        sa.Column("revenue", sa.Float(), nullable=True),
        sa.Column("ebitda", sa.Float(), nullable=True),
        sa.Column("ev_to_revenue", sa.Float(), nullable=True),
        sa.Column("ev_to_ebitda", sa.Float(), nullable=True),
        sa.Column("transaction_type", sa.String(50), server_default="100%_ACQUISITION", nullable=False),
        sa.Column("industry", sa.String(100), nullable=True),
        sa.Column("geography", sa.String(100), nullable=True),
        sa.Column("status", sa.String(20), server_default="INCLUDED", nullable=False),
        sa.Column("source", sa.String(100), server_default="ANALYST_INPUT", nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("citation_id", postgresql.UUID(as_uuid=True) if is_postgres else sa.String(36), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["deal_id"], ["deals.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["valuation_id"], ["valuations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["citation_id"], ["citations.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_precedents_deal_status", "precedent_transactions", ["deal_id", "status"])

    # 5. valuation_outputs
    op.create_table(
        "valuation_outputs",
        sa.Column("id", postgresql.UUID(as_uuid=True) if is_postgres else sa.String(36), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True) if is_postgres else sa.String(36), nullable=False),
        sa.Column("deal_id", postgresql.UUID(as_uuid=True) if is_postgres else sa.String(36), nullable=False),
        sa.Column("valuation_id", postgresql.UUID(as_uuid=True) if is_postgres else sa.String(36), nullable=False),
        sa.Column("methodology", sa.String(50), nullable=False),
        sa.Column("enterprise_value_low", sa.Float(), nullable=True),
        sa.Column("enterprise_value_base", sa.Float(), nullable=True),
        sa.Column("enterprise_value_high", sa.Float(), nullable=True),
        sa.Column("equity_value_low", sa.Float(), nullable=True),
        sa.Column("equity_value_base", sa.Float(), nullable=True),
        sa.Column("equity_value_high", sa.Float(), nullable=True),
        sa.Column("implied_ev", sa.Float(), nullable=True),
        sa.Column("implied_equity_value", sa.Float(), nullable=True),
        sa.Column("calculation_details", postgresql.JSONB(astext_type=sa.Text()) if is_postgres else sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["deal_id"], ["deals.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["valuation_id"], ["valuations.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_val_outputs_deal_method", "valuation_outputs", ["deal_id", "methodology"])


def downgrade() -> None:
    op.drop_index("ix_val_outputs_deal_method", table_name="valuation_outputs")
    op.drop_table("valuation_outputs")
    op.drop_index("ix_precedents_deal_status", table_name="precedent_transactions")
    op.drop_table("precedent_transactions")
    op.drop_index("ix_comps_deal_status", table_name="comparable_companies")
    op.drop_table("comparable_companies")
    op.drop_index("ix_val_assumptions_valuation", table_name="valuation_assumptions")
    op.drop_index("ix_val_assumptions_deal_name", table_name="valuation_assumptions")
    op.drop_table("valuation_assumptions")
    op.drop_index("ix_valuations_status", table_name="valuations")
    op.drop_index("ix_valuations_org_deal", table_name="valuations")
    op.drop_table("valuations")
