"""Agent Execution & Assessment Persistence Models."""

import uuid
from typing import TYPE_CHECKING, Any, Dict, List, Optional
from sqlalchemy import Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domains.common.models import TenantScopedModel
from app.domains.common.types import CompatibleJSON

if TYPE_CHECKING:
    from app.domains.auth.models import User
    from app.domains.deals.models import Deal


class AgentExecution(TenantScopedModel):
    """Immutable audit record of a multi-agent orchestration execution."""
    __tablename__ = "agent_executions"

    deal_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("deals.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    orchestration_mode: Mapped[str] = mapped_column(String(50), default="FULL_DEAL_DECISION", nullable=False)
    query: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="COMPLETED", nullable=False)
    recommendation: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # BUY, BUY_WITH_CONDITIONS, etc.
    decision_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    confidence: Mapped[str] = mapped_column(String(30), default="HIGH", nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.90, nullable=False)
    human_review_required: Mapped[bool] = mapped_column(default=False, nullable=False)
    duration_ms: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    selected_agents: Mapped[List[str]] = mapped_column(CompatibleJSON, default=list, nullable=False)
    synthesis_payload: Mapped[Dict[str, Any]] = mapped_column(CompatibleJSON, default=dict, nullable=False)

    # Relationships
    assessments: Mapped[List["AgentAssessmentRecord"]] = relationship(
        "AgentAssessmentRecord", back_populates="execution", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_agent_exec_lookup", "organization_id", "deal_id", "created_at"),
    )


class AgentAssessmentRecord(TenantScopedModel):
    """Granular output assessment record for an individual specialist agent."""
    __tablename__ = "agent_assessments"

    execution_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agent_executions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    deal_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("deals.id", ondelete="CASCADE"), nullable=False, index=True
    )
    agent_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    domain: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="SUCCESS", nullable=False)
    confidence: Mapped[str] = mapped_column(String(30), default="HIGH", nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.90, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    findings_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    citations_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    tools_invoked: Mapped[List[str]] = mapped_column(CompatibleJSON, default=list, nullable=False)
    assessment_payload: Mapped[Dict[str, Any]] = mapped_column(CompatibleJSON, default=dict, nullable=False)
    execution_time_ms: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    # Relationships
    execution: Mapped["AgentExecution"] = relationship("AgentExecution", back_populates="assessments")

    __table_args__ = (
        Index("ix_agent_assess_lookup", "organization_id", "deal_id", "agent_id"),
    )
