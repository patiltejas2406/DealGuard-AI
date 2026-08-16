"""Pydantic v2 Schemas for Document Ingestion, Chunks, Search & Jobs."""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field
from app.api.v1.schemas.common import BaseResponse, DocumentResponse


class DocumentChunkResponse(BaseResponse):
    id: uuid.UUID
    document_id: uuid.UUID
    chunk_index: int
    page_number: int
    section_title: Optional[str] = None
    content: str
    token_count: Optional[int] = None
    embedding_model: str
    metadata_json: Optional[Dict[str, Any]] = None


class JobExecutionResponse(BaseResponse):
    id: uuid.UUID
    organization_id: uuid.UUID
    deal_id: Optional[uuid.UUID] = None
    job_type: str
    status: str
    progress_pct: int
    error_message: Optional[str] = None
    result_metadata: Optional[Dict[str, Any]] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class DocumentUploadResponse(BaseModel):
    document: DocumentResponse
    job: JobExecutionResponse


class SemanticSearchRequest(BaseModel):
    query: str = Field(..., min_length=2, max_length=1000)
    top_k: int = Field(default=5, ge=1, le=50)
    min_similarity: float = Field(default=0.2, ge=0.0, le=1.0)


class SemanticSearchResultItem(BaseModel):
    chunk_id: str
    document_id: str
    document_name: str
    page_number: int
    section_title: Optional[str] = None
    content: str
    similarity_score: float
    metadata: Dict[str, Any] = Field(default_factory=dict)
