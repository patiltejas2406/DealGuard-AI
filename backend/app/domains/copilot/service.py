"""Copilot Business Service: Multi-Domain Evidence Grounding and Streaming."""

import uuid
from typing import Any, AsyncGenerator, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import NotFoundException
from app.domains.audit.models import AuditEvent
from app.domains.common.context import TenantContext
from app.domains.copilot.engine import CopilotEngine
from app.domains.copilot.models import CopilotConversation, CopilotMessage
from app.domains.copilot.repository import CopilotRepository
from app.domains.copilot.retriever import MultiDomainRetriever
from app.domains.copilot.schemas import (
    CopilotConversationCreateRequest,
    CopilotConversationResponse,
    CopilotMessageResponse,
    CopilotQueryRequest,
    CopilotQueryResponse,
)
from app.domains.copilot.streaming import generate_sse_copilot_stream


class CopilotService:
    """Service layer managing copilot conversations, grounded retrieval, and streaming responses."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = CopilotRepository(session)
        self.retriever = MultiDomainRetriever(session)
        self.engine = CopilotEngine()

    async def list_conversations(
        self, context: TenantContext, deal_id: uuid.UUID
    ) -> List[CopilotConversationResponse]:
        context.validate_deal_access(deal_id)
        convs = await self.repo.list_conversations(context.organization_id, deal_id)
        return [
            CopilotConversationResponse(
                id=c.id,
                deal_id=c.deal_id,
                title=c.title,
                messages_count=len(c.messages) if hasattr(c, "messages") and c.messages else 0,
                created_at=c.created_at,
                updated_at=c.updated_at,
            )
            for c in convs
        ]

    async def create_conversation(
        self,
        context: TenantContext,
        deal_id: uuid.UUID,
        payload: CopilotConversationCreateRequest,
    ) -> CopilotConversationResponse:
        context.validate_deal_access(deal_id)
        conv = await self.repo.create_conversation(
            organization_id=context.organization_id,
            deal_id=deal_id,
            user_id=context.user_id,
            title=payload.title or "New Diligence Chat",
        )
        await self.session.commit()
        return CopilotConversationResponse(
            id=conv.id,
            deal_id=conv.deal_id,
            title=conv.title,
            messages_count=0,
            created_at=conv.created_at,
            updated_at=conv.updated_at,
            messages=[],
        )

    async def get_conversation(
        self, context: TenantContext, deal_id: uuid.UUID, conversation_id: uuid.UUID
    ) -> CopilotConversationResponse:
        context.validate_deal_access(deal_id)
        conv = await self.repo.get_conversation(context.organization_id, conversation_id)
        if not conv or conv.deal_id != deal_id:
            raise NotFoundException("CopilotConversation", conversation_id)

        msg_responses = [
            CopilotMessageResponse(
                id=m.id,
                deal_id=m.deal_id,
                conversation_id=m.conversation_id,
                role=m.role,
                content=m.content,
                citations=m.citations or [],
                confidence=m.confidence,
                retrieved_domains=m.retrieved_domains or [],
                metadata_payload=m.metadata_payload or {},
                created_at=m.created_at,
            )
            for m in conv.messages
        ]

        return CopilotConversationResponse(
            id=conv.id,
            deal_id=conv.deal_id,
            title=conv.title,
            messages_count=len(msg_responses),
            created_at=conv.created_at,
            updated_at=conv.updated_at,
            messages=msg_responses,
        )

    async def delete_conversation(
        self, context: TenantContext, deal_id: uuid.UUID, conversation_id: uuid.UUID
    ) -> bool:
        context.validate_deal_access(deal_id)
        deleted = await self.repo.delete_conversation(context.organization_id, conversation_id)
        if not deleted:
            raise NotFoundException("CopilotConversation", conversation_id)
        await self.session.commit()
        return True

    async def process_query(
        self, context: TenantContext, deal_id: uuid.UUID, payload: CopilotQueryRequest
    ) -> CopilotQueryResponse:
        """Process conversational query, retrieve multi-domain evidence, and persist message history."""
        context.validate_deal_access(deal_id)

        # 1. Resolve conversation and past history
        conversation_id = payload.conversation_id
        conversation_history: List[Dict[str, str]] = []

        if not conversation_id:
            title = payload.message[:40] + ("..." if len(payload.message) > 40 else "")
            conv = await self.repo.create_conversation(
                context.organization_id, deal_id, context.user_id, title=title
            )
            conversation_id = conv.id
        else:
            conv = await self.repo.get_conversation(context.organization_id, conversation_id)
            if not conv or conv.deal_id != deal_id:
                raise NotFoundException("CopilotConversation", conversation_id)
            if conv.messages:
                conversation_history = [
                    {"role": m.role, "content": m.content} for m in conv.messages
                ]

        # 2. Record User Message
        user_msg = await self.repo.create_message(
            organization_id=context.organization_id,
            deal_id=deal_id,
            conversation_id=conversation_id,
            role="user",
            content=payload.message,
        )

        # 3. Retrieve Multi-Domain Evidence Context
        retrieved_context = await self.retriever.retrieve_context_for_query(
            organization_id=context.organization_id,
            deal_id=deal_id,
            query=payload.message,
            conversation_history=conversation_history,
        )

        # 4. Generate Grounded Synthesis
        answer_text, confidence, citations = self.engine.generate_grounded_response(
            query=payload.message,
            retrieved_context=retrieved_context,
            conversation_history=conversation_history,
        )

        # 5. Record Assistant Message
        intent_val = getattr(retrieved_context.get("intent"), "value", str(retrieved_context.get("intent")))
        lang_val = getattr(retrieved_context.get("language"), "value", str(retrieved_context.get("language")))

        assistant_msg = await self.repo.create_message(
            organization_id=context.organization_id,
            deal_id=deal_id,
            conversation_id=conversation_id,
            role="assistant",
            content=answer_text,
            citations=citations,
            confidence=confidence,
            retrieved_domains=retrieved_context.get("retrieved_domains", []),
            metadata_payload={
                "deal_id": str(deal_id),
                "intent": intent_val,
                "language": lang_val,
            },
        )

        # 6. Audit Logging
        self.session.add(
            AuditEvent(
                organization_id=context.organization_id,
                actor_user_id=context.user_id,
                deal_id=deal_id,
                action="COPILOT_QUERY_PROCESSED",
                entity_type="CopilotConversation",
                entity_id=conversation_id,
                details={
                    "query": payload.message[:100],
                    "intent": intent_val,
                    "language": lang_val,
                    "confidence": confidence,
                    "citations_count": len(citations),
                    "retrieved_domains": retrieved_context.get("retrieved_domains", []),
                },
            )
        )
        await self.session.commit()

        return CopilotQueryResponse(
            deal_id=deal_id,
            conversation_id=conversation_id,
            user_message=CopilotMessageResponse.model_validate(user_msg),
            assistant_message=CopilotMessageResponse.model_validate(assistant_msg),
        )

    async def stream_query(
        self, context: TenantContext, deal_id: uuid.UUID, payload: CopilotQueryRequest
    ) -> AsyncGenerator[str, None]:
        """Stream conversational query tokens and citations over Server-Sent Events (SSE)."""
        context.validate_deal_access(deal_id)

        # 1. Resolve conversation and past history
        conversation_id = payload.conversation_id
        conversation_history: List[Dict[str, str]] = []

        if not conversation_id:
            title = payload.message[:40] + ("..." if len(payload.message) > 40 else "")
            conv = await self.repo.create_conversation(
                context.organization_id, deal_id, context.user_id, title=title
            )
            conversation_id = conv.id
        else:
            conv = await self.repo.get_conversation(context.organization_id, conversation_id)
            if not conv or conv.deal_id != deal_id:
                raise NotFoundException("CopilotConversation", conversation_id)
            if conv.messages:
                conversation_history = [
                    {"role": m.role, "content": m.content} for m in conv.messages
                ]

        # 2. Record User Message
        user_msg = await self.repo.create_message(
            organization_id=context.organization_id,
            deal_id=deal_id,
            conversation_id=conversation_id,
            role="user",
            content=payload.message,
        )

        # 3. Retrieve Multi-Domain Evidence Context
        retrieved_context = await self.retriever.retrieve_context_for_query(
            organization_id=context.organization_id,
            deal_id=deal_id,
            query=payload.message,
            conversation_history=conversation_history,
        )

        # 4. Generate Grounded Synthesis
        answer_text, confidence, citations = self.engine.generate_grounded_response(
            query=payload.message,
            retrieved_context=retrieved_context,
            conversation_history=conversation_history,
        )

        # 5. Record Assistant Message
        intent_val = getattr(retrieved_context.get("intent"), "value", str(retrieved_context.get("intent")))
        lang_val = getattr(retrieved_context.get("language"), "value", str(retrieved_context.get("language")))

        assistant_msg = await self.repo.create_message(
            organization_id=context.organization_id,
            deal_id=deal_id,
            conversation_id=conversation_id,
            role="assistant",
            content=answer_text,
            citations=citations,
            confidence=confidence,
            retrieved_domains=retrieved_context.get("retrieved_domains", []),
            metadata_payload={
                "deal_id": str(deal_id),
                "intent": intent_val,
                "language": lang_val,
            },
        )

        # 6. Audit Logging
        self.session.add(
            AuditEvent(
                organization_id=context.organization_id,
                actor_user_id=context.user_id,
                deal_id=deal_id,
                action="COPILOT_QUERY_STREAMED",
                entity_type="CopilotConversation",
                entity_id=conversation_id,
                details={
                    "query": payload.message[:100],
                    "intent": intent_val,
                    "language": lang_val,
                    "confidence": confidence,
                    "citations_count": len(citations),
                    "retrieved_domains": retrieved_context.get("retrieved_domains", []),
                },
            )
        )
        await self.session.commit()

        metadata = {
            "conversation_id": str(conversation_id),
            "user_message_id": str(user_msg.id),
            "assistant_message_id": str(assistant_msg.id),
            "intent": intent_val,
            "language": lang_val,
            "created_at": assistant_msg.created_at.isoformat() if hasattr(assistant_msg, "created_at") and assistant_msg.created_at else None,
        }

        return generate_sse_copilot_stream(
            answer_text=answer_text,
            confidence=confidence,
            citations=citations,
            retrieved_domains=retrieved_context.get("retrieved_domains", []),
            metadata=metadata,
        )
