"""Post-Acquisition Intelligence, Value Creation & Growth Domain Models."""

import uuid
from datetime import date
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import Boolean, Date, Float, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.domains.common.models import TenantScopedModel
from app.domains.common.types import CompatibleJSON

if TYPE_CHECKING:
    from app.domains.deals.models import Deal, TargetCompany
    from app.domains.auth.models import User


class CustomerAccount(TenantScopedModel):
    """Acquired company customer account tracking health, ARR, NRR, and churn risk."""
    __tablename__ = "customer_accounts"

    deal_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("deals.id", ondelete="CASCADE"), nullable=False, index=True
    )
    company_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("target_companies.id", ondelete="SET NULL"), nullable=True, index=True
    )
    account_name: Mapped[str] = mapped_column(String(255), nullable=False)
    segment: Mapped[str] = mapped_column(String(100), default="MID_MARKET", nullable=False)  # ENTERPRISE, MID_MARKET, SMB, STRATEGIC
    arr: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    mrr: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    contract_start_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    contract_end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    churn_risk_score: Mapped[float] = mapped_column(Float, default=0.15, nullable=False)  # 0.0 - 1.0
    health_status: Mapped[str] = mapped_column(String(50), default="HEALTHY", nullable=False)  # HEALTHY, EXPANDING, AT_RISK, CRITICAL, CHURNED
    nps: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_churned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    expansion_potential_usd: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    industry: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    products_used: Mapped[Optional[list]] = mapped_column(CompatibleJSON, default=list, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    deal: Mapped["Deal"] = relationship("Deal", backref="customer_accounts")
    company: Mapped[Optional["TargetCompany"]] = relationship("TargetCompany")

    __table_args__ = (
        Index("ix_cust_accounts_org_deal", "organization_id", "deal_id"),
        Index("ix_cust_accounts_deal_health", "deal_id", "health_status"),
        Index("ix_cust_accounts_deal_arr", "deal_id", "arr"),
    )


class PostAcquisitionMetric(TenantScopedModel):
    """Deterministic time-series post-close actuals vs baseline and plan targets."""
    __tablename__ = "post_acquisition_metrics"

    deal_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("deals.id", ondelete="CASCADE"), nullable=False, index=True
    )
    fiscal_period: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g. "Q1_POST_CLOSE", "Q2_POST_CLOSE", "MONTH_6"
    metric_category: Mapped[str] = mapped_column(String(50), nullable=False)  # FINANCIAL, OPERATIONAL, CUSTOMER, EFFICIENCY
    metric_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)  # REVENUE, EBITDA, GROSS_MARGIN, ARR, NRR, CAC, CLOUD_SPEND, HEADCOUNT
    baseline_value: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    target_value: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    actual_value: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    variance_pct: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    unit: Mapped[str] = mapped_column(String(20), default="USD", nullable=False)  # USD, PERCENTAGE, COUNT, RATIO
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    deal: Mapped["Deal"] = relationship("Deal", backref="post_acquisition_metrics")

    __table_args__ = (
        Index("ix_post_metrics_org_deal", "organization_id", "deal_id"),
        Index("ix_post_metrics_deal_period", "deal_id", "fiscal_period", "metric_name"),
    )


class AcquisitionThesis(TenantScopedModel):
    """Acquisition Thesis tracking comparing pre-deal expectations vs actual post-close performance."""
    __tablename__ = "acquisition_theses"

    deal_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("deals.id", ondelete="CASCADE"), nullable=False, index=True
    )
    thesis_pillar: Mapped[str] = mapped_column(String(50), nullable=False)  # REVENUE, EBITDA, SYNERGY, CUSTOMER, INTEGRATION, TECHNOLOGY
    target_metric: Mapped[str] = mapped_column(String(100), nullable=False)
    baseline_value: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    target_value: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    actual_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    variance_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="INSUFFICIENT_DATA", nullable=False)  # ON_TRACK, AT_RISK, OFF_TRACK, INSUFFICIENT_DATA
    rationale: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    citations: Mapped[Optional[list]] = mapped_column(CompatibleJSON, default=list, nullable=True)

    # Relationships
    deal: Mapped["Deal"] = relationship("Deal", backref="acquisition_theses")

    __table_args__ = (
        Index("ix_thesis_org_deal", "organization_id", "deal_id"),
        Index("ix_thesis_pillar", "deal_id", "thesis_pillar"),
    )


class ValueCreationInitiative(TenantScopedModel):
    """Strategic post-acquisition value creation program and EBITDA impact tracking."""
    __tablename__ = "value_creation_initiatives"

    deal_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("deals.id", ondelete="CASCADE"), nullable=False, index=True
    )
    pillar: Mapped[str] = mapped_column(String(50), nullable=False)  # GROWTH, PRICING, COST, OPERATIONS, RETENTION
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    owner: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    target_ebitda_impact: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    realized_ebitda_impact: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="IDENTIFIED", nullable=False)  # IDENTIFIED, IN_PROGRESS, REALIZED, DELAYED
    timeline_quarter: Mapped[str] = mapped_column(String(50), default="Q1_POST_CLOSE", nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    deal: Mapped["Deal"] = relationship("Deal", backref="value_creation_initiatives")

    __table_args__ = (
        Index("ix_vci_org_deal", "organization_id", "deal_id"),
        Index("ix_vci_deal_pillar", "deal_id", "pillar"),
    )
