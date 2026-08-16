"""Diligence Data Room Document Ingestion, Parsing & Semantic Search Endpoints."""

import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import (
    get_tenant_context,
    require_permission,
    validate_deal_membership,
)
from app.api.v1.schemas.common import DocumentResponse
from app.api.v1.schemas.documents import (
    DocumentChunkResponse,
    DocumentUploadResponse,
    JobExecutionResponse,
    SemanticSearchRequest,
    SemanticSearchResultItem,
)
from app.core.database import get_db
from app.domains.auth.permissions import (
    PERM_DOCS_READ,
    PERM_DOCS_UPLOAD,
)
from app.domains.common.context import TenantContext
from app.domains.documents.service import DocumentService

router = APIRouter(prefix="/deals/{deal_id}/documents", tags=["Diligence Documents & Search"])


@router.post(
    "/upload",
    summary="Upload Document & Launch Ingestion Pipeline",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=DocumentUploadResponse,
)
async def upload_document(
    deal_id: uuid.UUID,
    file: UploadFile = File(...),
    category: Optional[str] = Form(None, description="Document Category: FINANCIAL, LEGAL, OPERATIONAL, etc."),
    db: AsyncSession = Depends(get_db),
    context: TenantContext = Depends(validate_deal_membership),
) -> DocumentUploadResponse:
    """
    Ingest a diligence document (PDF, DOCX, XLSX, TXT, SEC filing).
    Stores file, validates SHA-256, extracts structure, chunks text, generates 1536d embeddings,
    and returns document catalog record with background tracking job.
    """
    context.require_permission(PERM_DOCS_UPLOAD)
    file_bytes = await file.read()
    service = DocumentService(db)

    result = await service.upload_and_ingest_document(
        context=context,
        deal_id=deal_id,
        filename=file.filename or "uploaded_document.bin",
        file_bytes=file_bytes,
        mime_type=file.content_type or "application/octet-stream",
        doc_category=category,
        run_inline=True,  # In-process pipeline completion for fast response & tests
    )

    return DocumentUploadResponse(
        document=DocumentResponse.model_validate(result["document"]),
        job=JobExecutionResponse.model_validate(result["job"]),
    )


@router.get(
    "/{document_id}",
    summary="Get Document Metadata & Ingestion Status",
    status_code=status.HTTP_200_OK,
    response_model=DocumentResponse,
)
async def get_document_details(
    deal_id: uuid.UUID,
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    context: TenantContext = Depends(validate_deal_membership),
) -> DocumentResponse:
    context.require_permission(PERM_DOCS_READ)
    service = DocumentService(db)
    doc = await service.get_document(context, deal_id, document_id)
    return DocumentResponse.model_validate(doc)


@router.get(
    "/{document_id}/chunks",
    summary="List Document Chunks with Layout Hierarchy & Breadcrumbs",
    status_code=status.HTTP_200_OK,
    response_model=List[DocumentChunkResponse],
)
async def list_document_chunks(
    deal_id: uuid.UUID,
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    context: TenantContext = Depends(validate_deal_membership),
) -> List[DocumentChunkResponse]:
    context.require_permission(PERM_DOCS_READ)
    service = DocumentService(db)
    chunks = await service.list_document_chunks(context, deal_id, document_id)
    return [DocumentChunkResponse.model_validate(c) for c in chunks]


@router.post(
    "/search",
    summary="Semantic Vector Search across Deal Documents",
    status_code=status.HTTP_200_OK,
    response_model=List[SemanticSearchResultItem],
)
async def search_deal_documents(
    deal_id: uuid.UUID,
    payload: SemanticSearchRequest,
    db: AsyncSession = Depends(get_db),
    context: TenantContext = Depends(validate_deal_membership),
) -> List[SemanticSearchResultItem]:
    """
    Perform 1536-dimensional cosine similarity search across all indexed chunks in this deal room.
    Strictly isolated to authenticated organization and authorized deal members.
    """
    context.require_permission(PERM_DOCS_READ)
    service = DocumentService(db)
    results = await service.search_evidence(
        context=context,
        deal_id=deal_id,
        query=payload.query,
        top_k=payload.top_k,
        min_similarity=payload.min_similarity,
    )
    return [SemanticSearchResultItem(**r) for r in results]
