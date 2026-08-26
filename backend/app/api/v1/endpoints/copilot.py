"""REST API Endpoints for Streaming RAG Copilot Deal Intelligence."""

import uuid
from typing import List
from fastapi import APIRouter, Depends, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import validate_deal_membership
from app.core.database import get_db
from app.domains.auth.permissions import PERM_ANALYSIS_RUN, PERM_DEALS_READ
from app.domains.common.context import TenantContext
from app.domains.copilot.schemas import (
    CopilotConversationCreateRequest,
    CopilotConversationResponse,
    CopilotQueryRequest,
    CopilotQueryResponse,
)
from app.domains.copilot.service import CopilotService

router = APIRouter(prefix="/deals/{deal_id}/copilot", tags=["copilot"])


@router.get(
    "/conversations",
    summary="List Copilot Conversations",
    status_code=status.HTTP_200_OK,
    response_model=List[CopilotConversationResponse],
)
async def list_conversations(
    deal_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    context: TenantContext = Depends(validate_deal_membership),
) -> List[CopilotConversationResponse]:
    """List all deal diligence conversations for the authenticated tenant."""
    context.require_permission(PERM_DEALS_READ)
    service = CopilotService(db)
    return await service.list_conversations(context, deal_id)


@router.post(
    "/conversations",
    summary="Create Copilot Conversation Thread",
    status_code=status.HTTP_201_CREATED,
    response_model=CopilotConversationResponse,
)
async def create_conversation(
    deal_id: uuid.UUID,
    payload: CopilotConversationCreateRequest,
    db: AsyncSession = Depends(get_db),
    context: TenantContext = Depends(validate_deal_membership),
) -> CopilotConversationResponse:
    """Initialize a new multi-turn diligence conversational thread."""
    context.require_permission(PERM_ANALYSIS_RUN)
    service = CopilotService(db)
    return await service.create_conversation(context, deal_id, payload)


@router.get(
    "/conversations/{conversation_id}",
    summary="Get Copilot Conversation History",
    status_code=status.HTTP_200_OK,
    response_model=CopilotConversationResponse,
)
async def get_conversation(
    deal_id: uuid.UUID,
    conversation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    context: TenantContext = Depends(validate_deal_membership),
) -> CopilotConversationResponse:
    """Retrieve complete message history with grounded citations for a conversation thread."""
    context.require_permission(PERM_DEALS_READ)
    service = CopilotService(db)
    return await service.get_conversation(context, deal_id, conversation_id)


@router.delete(
    "/conversations/{conversation_id}",
    summary="Delete Copilot Conversation",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_conversation(
    deal_id: uuid.UUID,
    conversation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    context: TenantContext = Depends(validate_deal_membership),
) -> None:
    """Delete a conversation thread and its associated message history."""
    context.require_permission(PERM_ANALYSIS_RUN)
    service = CopilotService(db)
    await service.delete_conversation(context, deal_id, conversation_id)


@router.post(
    "/query",
    summary="Ask DealGuard Copilot (Standard Response)",
    status_code=status.HTTP_200_OK,
    response_model=CopilotQueryResponse,
)
async def query_copilot(
    deal_id: uuid.UUID,
    payload: CopilotQueryRequest,
    db: AsyncSession = Depends(get_db),
    context: TenantContext = Depends(validate_deal_membership),
) -> CopilotQueryResponse:
    """Ask an evidence-grounded diligence question across financial, legal, risk, and technical domains."""
    context.require_permission(PERM_ANALYSIS_RUN)
    service = CopilotService(db)
    return await service.process_query(context, deal_id, payload)


@router.post(
    "/stream",
    summary="Ask DealGuard Copilot (SSE Streaming Response)",
    status_code=status.HTTP_200_OK,
)
async def stream_copilot(
    deal_id: uuid.UUID,
    payload: CopilotQueryRequest,
    db: AsyncSession = Depends(get_db),
    context: TenantContext = Depends(validate_deal_membership),
):
    """Stream progressive token synthesis and citations using Server-Sent Events (SSE)."""
    context.require_permission(PERM_ANALYSIS_RUN)
    service = CopilotService(db)
    event_generator = await service.stream_query(context, deal_id, payload)
    return StreamingResponse(event_generator, media_type="text/event-stream")
