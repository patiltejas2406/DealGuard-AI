"""Copilot Conversation and Multi-Turn Message Domain Models."""

import uuid
from typing import TYPE_CHECKING, Any, Dict, List, Optional
from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.domains.common.models import TenantScopedModel
from app.domains.common.types import CompatibleJSON

if TYPE_CHECKING:
    from app.domains.auth.models import User
    from app.domains.deals.models import Deal


class CopilotConversation(TenantScopedModel):
    """Conversation thread tracking multi-turn deal intelligence dialogue."""
    __tablename__ = "copilot_conversations"

    deal_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("deals.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    title: Mapped[str] = mapped_column(String(255), default="New Diligence Chat", nullable=False)

    # Relationships
    deal: Mapped["Deal"] = relationship("Deal", backref="copilot_conversations")
    user: Mapped[Optional["User"]] = relationship("User")
    messages: Mapped[List["CopilotMessage"]] = relationship(
        "CopilotMessage",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="CopilotMessage.created_at.asc()",
    )

    __table_args__ = (
        Index("ix_copilot_conv_org_deal", "organization_id", "deal_id"),
    )


class CopilotMessage(TenantScopedModel):
    """Single message in a conversational diligence thread with grounded citations."""
    __tablename__ = "copilot_messages"

    deal_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("deals.id", ondelete="CASCADE"), nullable=False, index=True
    )
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("copilot_conversations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)  # user, assistant, system
    content: Mapped[str] = mapped_column(Text, nullable=False)
    citations: Mapped[List[Dict[str, Any]]] = mapped_column(CompatibleJSON, default=list, nullable=False)
    confidence: Mapped[str] = mapped_column(String(30), default="HIGH", nullable=False)  # HIGH, MEDIUM, LOW, INSUFFICIENT_EVIDENCE
    retrieved_domains: Mapped[List[str]] = mapped_column(CompatibleJSON, default=list, nullable=False)
    metadata_payload: Mapped[Dict[str, Any]] = mapped_column(CompatibleJSON, default=dict, nullable=False)

    # Relationships
    conversation: Mapped["CopilotConversation"] = relationship("CopilotConversation", back_populates="messages")

    __table_args__ = (
        Index("ix_copilot_msg_conv_created", "conversation_id", "created_at"),
    )
