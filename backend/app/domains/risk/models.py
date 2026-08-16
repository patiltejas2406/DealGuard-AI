"""17-Pillar Deal Risk Intelligence & Grounded Evidence Models."""

import uuid
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.domains.common.models import TenantScopedModel

if TYPE_CHECKING:
    from app.domains.deals.models import Deal
    from app.domains.documents.models import Citation


class Risk(TenantScopedModel):
    """Institutional Deal Risk Item across 17 Diligence Pillars."""
    __tablename__ = "risks"

    deal_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("deals.id", ondelete="CASCADE"), nullable=False, index=True
    )
    category: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Quantitative Risk Assessment (1 - 5 scale)
    severity: Mapped[int] = mapped_column(Integer, nullable=False)  # 1 (Negligible) to 5 (Catastrophic)
    likelihood: Mapped[int] = mapped_column(Integer, nullable=False)  # 1 (Rare) to 5 (Almost Certain)
    score: Mapped[int] = mapped_column(Integer, nullable=False)  # severity * likelihood (1 to 25)
    
    status: Mapped[str] = mapped_column(String(50), default="IDENTIFIED", nullable=False, index=True)
    mitigation_strategy: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    owner_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    # Relationships
    deal: Mapped["Deal"] = relationship("Deal", back_populates="risks")
    evidence_items: Mapped[List["RiskEvidence"]] = relationship(
        "RiskEvidence", back_populates="risk", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_risks_org_deal_cat", "organization_id", "deal_id", "category"),
    )


class RiskEvidence(TenantScopedModel):
    """Bridge linking a specific risk finding to its verifiable citation."""
    __tablename__ = "risk_evidence"

    deal_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("deals.id", ondelete="CASCADE"), nullable=False, index=True
    )
    risk_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("risks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    citation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("citations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    relevance_explanation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    weight: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)

    # Relationships
    risk: Mapped["Risk"] = relationship("Risk", back_populates="evidence_items")
    citation: Mapped["Citation"] = relationship("Citation", back_populates="risk_evidence")

    __table_args__ = (
        Index("ix_risk_evidence_lookup", "risk_id", "citation_id"),
    )
