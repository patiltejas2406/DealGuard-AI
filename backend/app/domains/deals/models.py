"""Deal Workspace & Target Company Domain Models."""

import uuid
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import Boolean, Float, ForeignKey, Index, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.domains.common.models import TenantScopedModel
from app.domains.common.types import CompatibleJSON

if TYPE_CHECKING:
    from app.domains.auth.models import Organization, User
    from app.domains.documents.models import Document
    from app.domains.financials.models import FinancialStatement
    from app.domains.risk.models import Risk
    from app.domains.audit.models import AuditEvent, HumanReview


class TargetCompany(TenantScopedModel):
    """Target acquisition entity under diligence or monitored portfolio company."""
    __tablename__ = "target_companies"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    legal_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    company_type: Mapped[str] = mapped_column(String(50), default="TARGET_ACQUISITION", nullable=False)  # TARGET_ACQUISITION, PORTFOLIO_COMPANY, INTERNAL_UNIT, SUBSIDIARY
    lifecycle_stage: Mapped[str] = mapped_column(String(50), default="DILIGENCE", nullable=False)  # DILIGENCE, ACQUIRED, INTEGRATING, MONITORED, HISTORICAL
    industry: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    sector: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    headquarters: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    website: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    founding_year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    employee_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(String(2000), nullable=True)
    metadata_json: Mapped[Optional[dict]] = mapped_column(CompatibleJSON, default=dict, nullable=True)

    # Relationships
    deals: Mapped[List["Deal"]] = relationship("Deal", back_populates="target_company")

    __table_args__ = (
        Index("ix_target_company_org_name", "organization_id", "name"),
        Index("ix_target_company_type_stage", "organization_id", "company_type", "lifecycle_stage"),
    )


class Deal(TenantScopedModel):
    """Deal Workspace tracking the M&A transaction lifecycle."""
    __tablename__ = "deals"

    target_company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("target_companies.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    code_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    deal_type: Mapped[str] = mapped_column(String(50), default="M_AND_A_BUY_SIDE", nullable=False)
    stage: Mapped[str] = mapped_column(String(50), default="PRE_DILIGENCE", nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(50), default="ACTIVE", nullable=False, index=True)
    
    # Financial Targets & Presentation Currency
    target_ev: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    
    # Composite Decision Score (0 - 100)
    decision_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Author / Lead
    created_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization", back_populates="deals")
    target_company: Mapped["TargetCompany"] = relationship("TargetCompany", back_populates="deals")
    members: Mapped[List["DealMember"]] = relationship("DealMember", back_populates="deal", cascade="all, delete-orphan")
    documents: Mapped[List["Document"]] = relationship("Document", back_populates="deal", cascade="all, delete-orphan")
    financial_statements: Mapped[List["FinancialStatement"]] = relationship("FinancialStatement", back_populates="deal", cascade="all, delete-orphan")
    risks: Mapped[List["Risk"]] = relationship("Risk", back_populates="deal", cascade="all, delete-orphan")
    audit_events: Mapped[List["AuditEvent"]] = relationship("AuditEvent", back_populates="deal", cascade="all, delete-orphan")
    human_reviews: Mapped[List["HumanReview"]] = relationship("HumanReview", back_populates="deal", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_deals_org_stage", "organization_id", "stage"),
        Index("ix_deals_org_status", "organization_id", "status"),
    )


class DealMember(TenantScopedModel):
    """Assignment of a user to a specific deal workspace with deal-level role."""
    __tablename__ = "deal_members"

    deal_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("deals.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    deal_role: Mapped[str] = mapped_column(String(50), default="ANALYST", nullable=False)
    can_edit: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    deal: Mapped["Deal"] = relationship("Deal", back_populates="members")
    user: Mapped["User"] = relationship("User", back_populates="deal_memberships")

    __table_args__ = (
        UniqueConstraint("deal_id", "user_id", name="uq_deal_user_membership"),
        Index("ix_deal_members_lookup", "organization_id", "deal_id", "user_id"),
    )
