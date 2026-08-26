"""Async Database Repository for Copilot Conversations and Messages."""

import uuid
from typing import Any, Dict, List, Optional
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.domains.copilot.models import CopilotConversation, CopilotMessage


class CopilotRepository:
    """Repository handling persistence of multi-turn copilot threads and messages."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_conversation(
        self,
        organization_id: uuid.UUID,
        deal_id: uuid.UUID,
        user_id: Optional[uuid.UUID],
        title: str = "New Diligence Chat",
    ) -> CopilotConversation:
        conv = CopilotConversation(
            organization_id=organization_id,
            deal_id=deal_id,
            user_id=user_id,
            title=title,
        )
        self.session.add(conv)
        await self.session.flush()
        return conv

    async def list_conversations(
        self, organization_id: uuid.UUID, deal_id: uuid.UUID
    ) -> List[CopilotConversation]:
        query = (
            select(CopilotConversation)
            .options(selectinload(CopilotConversation.messages))
            .where(
                CopilotConversation.organization_id == organization_id,
                CopilotConversation.deal_id == deal_id,
            )
            .order_by(CopilotConversation.created_at.desc())
        )
        res = await self.session.execute(query)
        return list(res.scalars().all())

    async def get_conversation(
        self, organization_id: uuid.UUID, conversation_id: uuid.UUID
    ) -> Optional[CopilotConversation]:
        query = (
            select(CopilotConversation)
            .options(selectinload(CopilotConversation.messages))
            .where(
                CopilotConversation.organization_id == organization_id,
                CopilotConversation.id == conversation_id,
            )
        )
        res = await self.session.execute(query)
        return res.scalar_one_or_none()

    async def delete_conversation(
        self, organization_id: uuid.UUID, conversation_id: uuid.UUID
    ) -> bool:
        conv = await self.get_conversation(organization_id, conversation_id)
        if not conv:
            return False
        await self.session.delete(conv)
        await self.session.flush()
        return True

    async def create_message(
        self,
        organization_id: uuid.UUID,
        deal_id: uuid.UUID,
        conversation_id: uuid.UUID,
        role: str,
        content: str,
        citations: Optional[List[Dict[str, Any]]] = None,
        confidence: str = "HIGH",
        retrieved_domains: Optional[List[str]] = None,
        metadata_payload: Optional[Dict[str, Any]] = None,
    ) -> CopilotMessage:
        msg = CopilotMessage(
            organization_id=organization_id,
            deal_id=deal_id,
            conversation_id=conversation_id,
            role=role,
            content=content,
            citations=citations or [],
            confidence=confidence,
            retrieved_domains=retrieved_domains or [],
            metadata_payload=metadata_payload or {},
        )
        self.session.add(msg)
        await self.session.flush()
        return msg
