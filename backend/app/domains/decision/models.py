"""Decision Intelligence Domain Models: Composite Decision Scores & Component Lineage."""

import uuid
from typing import TYPE_CHECKING, Optional
from sqlalchemy import Float, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.domains.common.models import TenantScopedModel
from app.domains.common.types import CompatibleJSON

if TYPE_CHECKING:
    from app.domains.auth.models import User
    from app.domains.deals.models import Deal, TargetCompany


class DecisionScore(TenantScopedModel):
    """Auditable, versioned composite decision evaluation score for an M&A deal or company entity."""
    __tablename__ = "decision_scores"

    deal_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("deals.id", ondelete="CASCADE"), nullable=False, index=True
    )
    company_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("target_companies.id", ondelete="SET NULL"), nullable=True, index=True
    )
    score_type: Mapped[str] = mapped_column(String(50), default="DEAL", nullable=False)  # DEAL, COMPANY_HEALTH, PORTFOLIO_COMPANY
    overall_score: Mapped[float] = mapped_column(Float, nullable=False)  # 0.0 to 100.0
    decision_band: Mapped[str] = mapped_column(String(30), nullable=False)  # STRONG, FAVORABLE, CAUTION, HIGH_RISK, AVOID
    confidence_score: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)  # 0.0 to 1.0
    scoring_version: Mapped[str] = mapped_column(String(20), default="1.0", nullable=False)

    # Serialized Component Breakdown & Metadata
    weights_used: Mapped[dict] = mapped_column(CompatibleJSON, nullable=False)
    component_scores: Mapped[dict] = mapped_column(CompatibleJSON, nullable=False)
    positive_drivers: Mapped[Optional[list]] = mapped_column(CompatibleJSON, default=list, nullable=True)
    negative_drivers: Mapped[Optional[list]] = mapped_column(CompatibleJSON, default=list, nullable=True)
    missing_information: Mapped[Optional[list]] = mapped_column(CompatibleJSON, default=list, nullable=True)
    recommendations: Mapped[Optional[list]] = mapped_column(CompatibleJSON, default=list, nullable=True)

    calculated_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    # Relationships
    deal: Mapped["Deal"] = relationship("Deal", backref="decision_score_records")
    company: Mapped[Optional["TargetCompany"]] = relationship("TargetCompany")
    calculated_by: Mapped[Optional["User"]] = relationship("User")

    __table_args__ = (
        Index("ix_decision_scores_org_deal", "organization_id", "deal_id"),
        Index("ix_decision_scores_deal_created", "deal_id", "created_at"),
        Index("ix_decision_scores_score_type", "deal_id", "score_type"),
    )
