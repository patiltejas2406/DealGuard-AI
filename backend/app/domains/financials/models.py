"""Financial Statements, Quality of Earnings (QoE) & Normalized Metrics Models."""

import uuid
from datetime import date
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import Boolean, Date, Float, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.domains.common.models import TenantScopedModel
from app.domains.common.types import CompatibleJSON

if TYPE_CHECKING:
    from app.domains.auth.models import User
    from app.domains.deals.models import Deal
    from app.domains.documents.models import Citation, Document


class FinancialStatement(TenantScopedModel):
    """Standardized 3-statement financial table record (P&L, Balance Sheet, Cash Flow)."""
    __tablename__ = "financial_statements"

    deal_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("deals.id", ondelete="CASCADE"), nullable=False, index=True
    )
    statement_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # INCOME_STATEMENT, BALANCE_SHEET, CASH_FLOW
    period_type: Mapped[str] = mapped_column(String(20), default="ANNUAL", nullable=False)  # ANNUAL, QUARTERLY, TTM
    fiscal_year: Mapped[int] = mapped_column(Integer, nullable=False)
    fiscal_period: Mapped[str] = mapped_column(String(20), nullable=False)  # e.g. FY2023, Q3_2023
    period_end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    
    # Currency preservation
    source_currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    is_audited: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_normalized: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Source linkage
    source_document_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("documents.id", ondelete="SET NULL"), nullable=True
    )

    # Structured Line Items (JSON key-value table: e.g. {"revenue": 45200000, "cogs": 22100000})
    line_items: Mapped[dict] = mapped_column(CompatibleJSON, nullable=False)

    # Relationships
    deal: Mapped["Deal"] = relationship("Deal", back_populates="financial_statements")
    metrics: Mapped[List["FinancialMetric"]] = relationship(
        "FinancialMetric", back_populates="statement", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("deal_id", "statement_type", "fiscal_period", name="uq_deal_stmt_period"),
        Index("ix_fin_stmt_lookup", "organization_id", "deal_id", "statement_type"),
    )


class FinancialMetric(TenantScopedModel):
    """Deterministic, time-series financial metric calculated or extracted from statements."""
    __tablename__ = "financial_metrics"

    deal_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("deals.id", ondelete="CASCADE"), nullable=False, index=True
    )
    statement_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("financial_statements.id", ondelete="CASCADE"), nullable=True, index=True
    )
    citation_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("citations.id", ondelete="SET NULL"), nullable=True
    )

    metric_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)  # REVENUE, EBITDA, NET_DEBT, CAGR
    period: Mapped[str] = mapped_column(String(20), nullable=False)  # FY2023, TTM
    value: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(20), default="CURRENCY", nullable=False)  # CURRENCY, PERCENTAGE, RATIO
    source_currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    is_normalized: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    calculation_formula: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Relationships
    statement: Mapped[Optional["FinancialStatement"]] = relationship("FinancialStatement", back_populates="metrics")
    citation: Mapped[Optional["Citation"]] = relationship("Citation")

    __table_args__ = (
        Index("ix_fin_metrics_deal_metric", "deal_id", "metric_name", "period"),
    )


class QoEAdjustment(TenantScopedModel):
    """Quality of Earnings (QoE) adjustment line item for EBITDA normalization bridge."""
    __tablename__ = "qoe_adjustments"

    deal_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("deals.id", ondelete="CASCADE"), nullable=False, index=True
    )
    category: Mapped[str] = mapped_column(String(50), nullable=False)  # ONE_TIME_EXPENSE, ONE_TIME_INCOME, LEGAL_NON_RECURRING, RESTRUCTURING, OWNER_PERSONAL, PRO_FORMA, OTHER
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    period: Mapped[str] = mapped_column(String(20), default="FY2023", nullable=False)
    treatment: Mapped[str] = mapped_column(String(20), default="ADD_BACK", nullable=False)  # ADD_BACK, DEDUCTION
    status: Mapped[str] = mapped_column(String(20), default="PROPOSED", nullable=False)  # PROPOSED, APPROVED, REJECTED
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    citation_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("citations.id", ondelete="SET NULL"), nullable=True
    )
    created_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    # Relationships
    deal: Mapped["Deal"] = relationship("Deal")
    citation: Mapped[Optional["Citation"]] = relationship("Citation")
    created_by: Mapped[Optional["User"]] = relationship("User")

    __table_args__ = (
        Index("ix_qoe_deal_period", "deal_id", "period"),
        Index("ix_qoe_org_status", "organization_id", "status"),
    )
