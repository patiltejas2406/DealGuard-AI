"""100-Day Post-Acquisition Integration Execution Domain Models."""

import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.domains.common.models import TenantScopedModel
from app.domains.common.types import CompatibleJSON

if TYPE_CHECKING:
    from app.domains.auth.models import User
    from app.domains.deals.models import Deal, TargetCompany
    from app.domains.synergy.models import SynergyOpportunity


class IntegrationProgram(TenantScopedModel):
    """100-Day Integration Program orchestrating deal workstreams and execution timelines."""
    __tablename__ = "integration_programs"

    deal_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("deals.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )
    company_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("target_companies.id", ondelete="SET NULL"), nullable=True, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="ACTIVE", nullable=False)  # PLANNING, ACTIVE, COMPLETED, ON_HOLD
    close_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    day_0_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    day_100_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    current_day_offset: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    executive_sponsor: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    objectives: Mapped[Optional[dict]] = mapped_column(CompatibleJSON, default=dict, nullable=True)
    health_score: Mapped[float] = mapped_column(Float, default=100.0, nullable=False)
    health_band: Mapped[str] = mapped_column(String(50), default="HEALTHY", nullable=False)  # HEALTHY, WATCH, AT_RISK, CRITICAL

    created_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    # Relationships
    deal: Mapped["Deal"] = relationship("Deal", backref="integration_program")
    company: Mapped[Optional["TargetCompany"]] = relationship("TargetCompany")
    created_by: Mapped[Optional["User"]] = relationship("User")
    workstreams: Mapped[List["IntegrationWorkstream"]] = relationship(
        "IntegrationWorkstream", back_populates="program", cascade="all, delete-orphan"
    )
    milestones: Mapped[List["IntegrationMilestone"]] = relationship(
        "IntegrationMilestone", back_populates="program", cascade="all, delete-orphan"
    )
    dependencies: Mapped[List["IntegrationDependency"]] = relationship(
        "IntegrationDependency", back_populates="program", cascade="all, delete-orphan"
    )
    blockers: Mapped[List["IntegrationBlocker"]] = relationship(
        "IntegrationBlocker", back_populates="program", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_integration_programs_org_deal", "organization_id", "deal_id"),
    )


class IntegrationWorkstream(TenantScopedModel):
    """Discrete functional integration track (e.g. Finance & Accounting, Technology Consolidation)."""
    __tablename__ = "integration_workstreams"

    deal_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("deals.id", ondelete="CASCADE"), nullable=False, index=True
    )
    program_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("integration_programs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(String(100), nullable=False)  # 17 categories
    owner: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    executive_sponsor: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="NOT_STARTED", nullable=False)  # NOT_STARTED, PLANNED, IN_PROGRESS, AT_RISK, BLOCKED, COMPLETED, CANCELLED
    priority: Mapped[str] = mapped_column(String(20), default="MEDIUM", nullable=False)      # CRITICAL, HIGH, MEDIUM, LOW
    start_day: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    target_day: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    progress_pct: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    risk_level: Mapped[str] = mapped_column(String(20), default="LOW", nullable=False)       # HIGH, MEDIUM, LOW
    linked_synergy_ids: Mapped[Optional[list]] = mapped_column(CompatibleJSON, default=list, nullable=True)
    linked_risk_ids: Mapped[Optional[list]] = mapped_column(CompatibleJSON, default=list, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    # Relationships
    program: Mapped["IntegrationProgram"] = relationship("IntegrationProgram", back_populates="workstreams")
    milestones: Mapped[List["IntegrationMilestone"]] = relationship(
        "IntegrationMilestone", back_populates="workstream", cascade="all, delete-orphan"
    )
    blockers: Mapped[List["IntegrationBlocker"]] = relationship(
        "IntegrationBlocker", back_populates="workstream", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_workstreams_org_deal", "organization_id", "deal_id"),
        Index("ix_workstreams_program_cat", "program_id", "category"),
        Index("ix_workstreams_status", "program_id", "status"),
    )


class IntegrationMilestone(TenantScopedModel):
    """Specific measurable deliverable or event in an integration workstream."""
    __tablename__ = "integration_milestones"

    deal_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("deals.id", ondelete="CASCADE"), nullable=False, index=True
    )
    program_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("integration_programs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    workstream_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("integration_workstreams.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    target_day: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    target_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="NOT_STARTED", nullable=False)  # NOT_STARTED, IN_PROGRESS, AT_RISK, BLOCKED, COMPLETED, OVERDUE
    priority: Mapped[str] = mapped_column(String(20), default="MEDIUM", nullable=False)
    owner: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    completion_pct: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    is_critical_path: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    linked_synergy_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("synergy_opportunities.id", ondelete="SET NULL"), nullable=True, index=True
    )
    deliverable: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    evidence_citation_ids: Mapped[Optional[list]] = mapped_column(CompatibleJSON, default=list, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    created_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    # Relationships
    program: Mapped["IntegrationProgram"] = relationship("IntegrationProgram", back_populates="milestones")
    workstream: Mapped["IntegrationWorkstream"] = relationship("IntegrationWorkstream", back_populates="milestones")
    linked_synergy: Mapped[Optional["SynergyOpportunity"]] = relationship("SynergyOpportunity")

    __table_args__ = (
        Index("ix_milestones_workstream", "workstream_id", "target_day"),
        Index("ix_milestones_status", "program_id", "status"),
    )


class IntegrationDependency(TenantScopedModel):
    """Directed dependency link between two milestones (predecessor -> successor)."""
    __tablename__ = "integration_dependencies"

    deal_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("deals.id", ondelete="CASCADE"), nullable=False, index=True
    )
    program_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("integration_programs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    predecessor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("integration_milestones.id", ondelete="CASCADE"), nullable=False, index=True
    )
    successor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("integration_milestones.id", ondelete="CASCADE"), nullable=False, index=True
    )
    dependency_type: Mapped[str] = mapped_column(String(50), default="FINISH_TO_START", nullable=False)
    is_blocking: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    program: Mapped["IntegrationProgram"] = relationship("IntegrationProgram", back_populates="dependencies")
    predecessor: Mapped["IntegrationMilestone"] = relationship("IntegrationMilestone", foreign_keys=[predecessor_id])
    successor: Mapped["IntegrationMilestone"] = relationship("IntegrationMilestone", foreign_keys=[successor_id])

    __table_args__ = (
        Index("ix_dependencies_pred_succ", "predecessor_id", "successor_id", unique=True),
    )


class IntegrationBlocker(TenantScopedModel):
    """Operational or strategic blocker impeding milestone or workstream execution."""
    __tablename__ = "integration_blockers"

    deal_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("deals.id", ondelete="CASCADE"), nullable=False, index=True
    )
    program_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("integration_programs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    workstream_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("integration_workstreams.id", ondelete="CASCADE"), nullable=False, index=True
    )
    milestone_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("integration_milestones.id", ondelete="SET NULL"), nullable=True, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    severity: Mapped[str] = mapped_column(String(20), default="HIGH", nullable=False)  # CRITICAL, HIGH, MEDIUM
    status: Mapped[str] = mapped_column(String(20), default="OPEN", nullable=False)     # OPEN, RESOLVED
    owner: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    resolution_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    created_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    # Relationships
    program: Mapped["IntegrationProgram"] = relationship("IntegrationProgram", back_populates="blockers")
    workstream: Mapped["IntegrationWorkstream"] = relationship("IntegrationWorkstream", back_populates="blockers")
    milestone: Mapped[Optional["IntegrationMilestone"]] = relationship("IntegrationMilestone")

    __table_args__ = (
        Index("ix_blockers_workstream_status", "workstream_id", "status"),
    )
