"""Synergy Realization & Value Creation Domain Models."""

import uuid
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import Float, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.domains.common.models import TenantScopedModel
from app.domains.common.types import CompatibleJSON

if TYPE_CHECKING:
    from app.domains.auth.models import User
    from app.domains.deals.models import Deal, TargetCompany


class SynergyOpportunity(TenantScopedModel):
    """Structured synergy value creation opportunity with baseline, target, and realization metrics."""
    __tablename__ = "synergy_opportunities"

    deal_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("deals.id", ondelete="CASCADE"), nullable=False, index=True
    )
    company_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("target_companies.id", ondelete="SET NULL"), nullable=True, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    synergy_type: Mapped[str] = mapped_column(String(50), nullable=False)  # REVENUE, COST, OPERATIONAL
    category: Mapped[str] = mapped_column(String(100), nullable=False)     # CROSS_SELLING, PROCUREMENT, etc.
    status: Mapped[str] = mapped_column(String(50), default="IDENTIFIED", nullable=False)  # IDENTIFIED, VALIDATED, PLANNED, IN_PROGRESS, PARTIALLY_REALIZED, REALIZED, AT_RISK, ABANDONED
    confidence: Mapped[str] = mapped_column(String(20), default="MEDIUM", nullable=False)  # HIGH, MEDIUM, LOW

    # Financial Value & Realization Probabilities
    baseline_value: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    target_value: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    potential_annual_value: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    realization_rate_pct: Mapped[float] = mapped_column(Float, default=100.0, nullable=False)
    probability_pct: Mapped[float] = mapped_column(Float, default=80.0, nullable=False)
    expected_annual_value: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    one_time_integration_cost: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    # 5-Year Realization Schedule & Evidence Provenance
    realization_curve: Mapped[Optional[dict]] = mapped_column(CompatibleJSON, default=dict, nullable=True)  # {"year_1": 20, "year_2": 50, ...}
    evidence_citation_ids: Mapped[Optional[list]] = mapped_column(CompatibleJSON, default=list, nullable=True)

    owner: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    realized_annual_value: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    # Relationships
    deal: Mapped["Deal"] = relationship("Deal", backref="synergies")
    company: Mapped[Optional["TargetCompany"]] = relationship("TargetCompany")
    created_by: Mapped[Optional["User"]] = relationship("User")
    realization_logs: Mapped[List["SynergyRealizationLog"]] = relationship(
        "SynergyRealizationLog", back_populates="synergy", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_synergies_org_deal", "organization_id", "deal_id"),
        Index("ix_synergies_deal_type", "deal_id", "synergy_type"),
        Index("ix_synergies_status", "deal_id", "status"),
    )


class SynergyRealizationLog(TenantScopedModel):
    """Auditable log of actual vs planned realized synergy value per fiscal period."""
    __tablename__ = "synergy_realization_logs"

    deal_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("deals.id", ondelete="CASCADE"), nullable=False, index=True
    )
    synergy_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("synergy_opportunities.id", ondelete="CASCADE"), nullable=False, index=True
    )
    fiscal_period: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g. "Q1-2024", "FY2024"
    planned_value: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    actual_value: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    variance: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    logged_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    # Relationships
    deal: Mapped["Deal"] = relationship("Deal")
    synergy: Mapped["SynergyOpportunity"] = relationship("SynergyOpportunity", back_populates="realization_logs")
    logged_by: Mapped[Optional["User"]] = relationship("User")

    __table_args__ = (
        Index("ix_synergy_logs_org_deal", "organization_id", "deal_id"),
        Index("ix_synergy_logs_synergy", "synergy_id", "created_at"),
    )
