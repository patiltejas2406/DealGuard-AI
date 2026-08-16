"""Immutable Audit Ledger & Human-in-the-Loop Override Models."""

import uuid
from typing import TYPE_CHECKING, Optional
from sqlalchemy import ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.domains.common.models import TenantScopedModel
from app.domains.common.types import CompatibleJSON

if TYPE_CHECKING:
    from app.domains.auth.models import Organization, User
    from app.domains.deals.models import Deal


class AuditEvent(TenantScopedModel):
    """Monotonic append-only audit trail logging all high-impact actions."""
    __tablename__ = "audit_events"

    deal_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("deals.id", ondelete="CASCADE"), nullable=True, index=True
    )
    actor_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    details: Mapped[Optional[dict]] = mapped_column(CompatibleJSON, default=dict, nullable=True)

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization", back_populates="audit_events")
    deal: Mapped[Optional["Deal"]] = relationship("Deal", back_populates="audit_events")
    actor_user: Mapped[Optional["User"]] = relationship("User", back_populates="audit_events")

    __table_args__ = (
        Index("ix_audit_org_action_created", "organization_id", "action", "created_at"),
    )


class HumanReview(TenantScopedModel):
    """Auditable ledger of human-in-the-loop decisions and AI overrides."""
    __tablename__ = "human_reviews"

    deal_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("deals.id", ondelete="CASCADE"), nullable=False, index=True
    )
    reviewer_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    target_entity_type: Mapped[str] = mapped_column(String(100), nullable=False)  # Risk, FinancialMetric, Recommendation
    target_entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    review_action: Mapped[str] = mapped_column(String(50), nullable=False)  # APPROVED, REJECTED, OVERRIDDEN, MODIFIED
    original_value: Mapped[Optional[dict]] = mapped_column(CompatibleJSON, nullable=True)
    reviewed_value: Mapped[Optional[dict]] = mapped_column(CompatibleJSON, nullable=True)
    rationale: Mapped[str] = mapped_column(Text, nullable=False)

    # Relationships
    deal: Mapped["Deal"] = relationship("Deal", back_populates="human_reviews")
    reviewer_user: Mapped["User"] = relationship("User", back_populates="human_reviews")

    __table_args__ = (
        Index("ix_human_reviews_target", "deal_id", "target_entity_type", "target_entity_id"),
    )
