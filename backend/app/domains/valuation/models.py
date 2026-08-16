"""Valuation Intelligence Domain Models: DCF, WACC, Comparables, Precedents & Outputs."""

import uuid
from typing import List, Optional
from sqlalchemy import Boolean, Float, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.domains.common.models import TenantScopedModel
from app.domains.common.types import CompatibleJSON



class Valuation(TenantScopedModel):
    """Core valuation project record scoped to an organization and deal."""
    __tablename__ = "valuations"

    deal_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("deals.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False, default="Base Case Valuation")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="ACTIVE")  # DRAFT, ACTIVE, FINAL, ARCHIVED
    selected_method: Mapped[str] = mapped_column(String(50), nullable=False, default="DCF")  # DCF, CCA, PRECEDENT, MULTI_METHOD
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    proposed_ev: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    proposed_equity_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    # Relationships
    deal = relationship("Deal", backref="valuations")
    created_by = relationship("User")
    assumptions = relationship("ValuationAssumption", back_populates="valuation", cascade="all, delete-orphan")
    comparables = relationship("ComparableCompany", back_populates="valuation", cascade="all, delete-orphan")
    precedents = relationship("PrecedentTransaction", back_populates="valuation", cascade="all, delete-orphan")
    outputs = relationship("ValuationOutput", back_populates="valuation", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_valuations_org_deal", "organization_id", "deal_id"),
        Index("ix_valuations_status", "deal_id", "status"),
    )


class ValuationAssumption(TenantScopedModel):
    """Granular, traceable valuation assumption with source citation provenance."""
    __tablename__ = "valuation_assumptions"

    deal_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("deals.id", ondelete="CASCADE"), nullable=False, index=True
    )
    valuation_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("valuations.id", ondelete="CASCADE"), nullable=True, index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g., RISK_FREE_RATE, ERP, BETA, WACC, TERMINAL_GROWTH
    category: Mapped[str] = mapped_column(String(50), nullable=False, default="WACC")  # WACC, PROJECTION, TERMINAL_VALUE, BRIDGE, OTHER
    value: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(20), nullable=False, default="PERCENTAGE")  # PERCENTAGE, CURRENCY, MULTIPLE, RATIO
    period: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # e.g., FY2024, TERMINAL
    source_type: Mapped[str] = mapped_column(String(30), nullable=False, default="ANALYST_INPUT")  # DOCUMENT, FINANCIAL_MODEL, MARKET_DATA, ANALYST_INPUT, DERIVED
    is_analyst_entered: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    confidence_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    citation_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("citations.id", ondelete="SET NULL"), nullable=True
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    valuation = relationship("Valuation", back_populates="assumptions")
    citation = relationship("Citation")

    __table_args__ = (
        Index("ix_val_assumptions_deal_name", "deal_id", "name"),
        Index("ix_val_assumptions_valuation", "valuation_id", "category"),
    )


class ComparableCompany(TenantScopedModel):
    """Trading peer comparable company record."""
    __tablename__ = "comparable_companies"

    deal_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("deals.id", ondelete="CASCADE"), nullable=False, index=True
    )
    valuation_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("valuations.id", ondelete="CASCADE"), nullable=True, index=True
    )
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    ticker: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    industry: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    geography: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    revenue: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ebitda: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ebit: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    net_income: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    enterprise_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    equity_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ev_to_revenue: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ev_to_ebitda: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    pe_ratio: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    revenue_growth: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="INCLUDED")  # INCLUDED, EXCLUDED, REVIEW
    source: Mapped[str] = mapped_column(String(100), nullable=False, default="ANALYST_INPUT")
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    citation_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("citations.id", ondelete="SET NULL"), nullable=True
    )

    # Relationships
    valuation = relationship("Valuation", back_populates="comparables")
    citation = relationship("Citation")

    __table_args__ = (
        Index("ix_comps_deal_status", "deal_id", "status"),
    )


class PrecedentTransaction(TenantScopedModel):
    """M&A Precedent Transaction record."""
    __tablename__ = "precedent_transactions"

    deal_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("deals.id", ondelete="CASCADE"), nullable=False, index=True
    )
    valuation_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("valuations.id", ondelete="CASCADE"), nullable=True, index=True
    )
    target_name: Mapped[str] = mapped_column(String(255), nullable=False)
    acquirer_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    announcement_date: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    transaction_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    enterprise_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    revenue: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ebitda: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ev_to_revenue: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ev_to_ebitda: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    transaction_type: Mapped[str] = mapped_column(String(50), nullable=False, default="100%_ACQUISITION")
    industry: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    geography: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="INCLUDED")  # INCLUDED, EXCLUDED, REVIEW
    source: Mapped[str] = mapped_column(String(100), nullable=False, default="ANALYST_INPUT")
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    citation_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("citations.id", ondelete="SET NULL"), nullable=True
    )

    # Relationships
    valuation = relationship("Valuation", back_populates="precedents")
    citation = relationship("Citation")

    __table_args__ = (
        Index("ix_precedents_deal_status", "deal_id", "status"),
    )


class ValuationOutput(TenantScopedModel):
    """Calculated valuation outputs and methodology bridges."""
    __tablename__ = "valuation_outputs"

    deal_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("deals.id", ondelete="CASCADE"), nullable=False, index=True
    )
    valuation_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("valuations.id", ondelete="CASCADE"), nullable=False, index=True
    )

    methodology: Mapped[str] = mapped_column(String(50), nullable=False)  # DCF_PERPETUITY, DCF_EXIT_MULTIPLE, CCA_REVENUE, CCA_EBITDA, PRECEDENT_REVENUE, PRECEDENT_EBITDA, SUMMARY
    enterprise_value_low: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    enterprise_value_base: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    enterprise_value_high: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    equity_value_low: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    equity_value_base: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    equity_value_high: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    implied_ev: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    implied_equity_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    calculation_details: Mapped[Optional[dict]] = mapped_column(CompatibleJSON, nullable=True)

    # Relationships

    valuation = relationship("Valuation", back_populates="outputs")

    __table_args__ = (
        Index("ix_val_outputs_deal_method", "deal_id", "methodology"),
    )
