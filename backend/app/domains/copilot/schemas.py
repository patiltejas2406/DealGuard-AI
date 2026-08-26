"""Pydantic Schemas for Streaming RAG Copilot."""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class CopilotCitation(BaseModel):
    citation_id: Optional[str] = None
    document_id: Optional[str] = None
    document_name: str
    page_number: Optional[int] = None
    section_title: Optional[str] = None
    quote: str
    confidence: str = Field(default="HIGH")


class CopilotMessageResponse(BaseModel):
    id: uuid.UUID
    deal_id: uuid.UUID
    conversation_id: uuid.UUID
    role: str
    content: str
    citations: List[CopilotCitation] = Field(default_factory=list)
    confidence: str
    retrieved_domains: List[str] = Field(default_factory=list)
    metadata_payload: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CopilotConversationResponse(BaseModel):
    id: uuid.UUID
    deal_id: uuid.UUID
    title: str
    messages_count: int = 0
    created_at: datetime
    updated_at: datetime
    messages: Optional[List[CopilotMessageResponse]] = None

    model_config = ConfigDict(from_attributes=True)


class CopilotConversationCreateRequest(BaseModel):
    title: Optional[str] = Field(default="New Diligence Chat", max_length=255)


class CopilotQueryRequest(BaseModel):
    conversation_id: Optional[uuid.UUID] = None
    message: str = Field(..., min_length=1)


class CopilotQueryResponse(BaseModel):
    deal_id: uuid.UUID
    conversation_id: uuid.UUID
    user_message: CopilotMessageResponse
    assistant_message: CopilotMessageResponse


class CopilotStreamChunk(BaseModel):
    event: str  # token, domain, citation, done, error
    data: Any
