"""Document, Evidence Citation & Ingestion Domain Service."""

import os
import uuid
from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import NotFoundException, ValidationException
from app.domains.ai.embeddings.factory import get_embedding_provider
from app.domains.common.context import TenantContext
from app.domains.documents.models import Citation, Document, DocumentChunk
from app.domains.documents.repository import DocumentRepository, JobRepository
from app.domains.documents.storage import DocumentStorageManager
from app.domains.documents.tasks import dispatch_ingestion_pipeline
from app.domains.jobs.models import JobExecution


class DocumentService:
    """High-level business operations for Diligence Data Room & Evidence Grounding."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = DocumentRepository(session)
        self.job_repo = JobRepository(session)
        self.storage = DocumentStorageManager()

    async def list_documents(self, context: TenantContext, deal_id: uuid.UUID) -> List[Document]:
        context.validate_deal_access(deal_id)
        return await self.repo.list_documents_for_deal(context.organization_id, deal_id)

    async def get_document(
        self, context: TenantContext, deal_id: uuid.UUID, document_id: uuid.UUID
    ) -> Document:
        context.validate_deal_access(deal_id)
        doc = await self.repo.get_document_by_id(context.organization_id, deal_id, document_id)
        if not doc:
            raise NotFoundException("Document", document_id)
        return doc

    async def register_document(
        self,
        context: TenantContext,
        deal_id: uuid.UUID,
        name: str,
        file_type: str,
        mime_type: str,
        size_bytes: int,
        storage_path: str,
        sha256_hash: str,
        doc_category: Optional[str] = None,
    ) -> Document:
        """Directly register document catalog record without background ingestion."""
        context.validate_deal_access(deal_id)
        doc = await self.repo.create_document(
            organization_id=context.organization_id,
            deal_id=deal_id,
            name=name,
            file_type=file_type,
            mime_type=mime_type,
            size_bytes=size_bytes,
            storage_path=storage_path,
            sha256_hash=sha256_hash,
            doc_category=doc_category,
            uploaded_by_id=context.user_id,
            status="UPLOADED",
        )
        await self.session.commit()
        return doc

    async def upload_and_ingest_document(

        self,
        context: TenantContext,
        deal_id: uuid.UUID,
        filename: str,
        file_bytes: bytes,
        mime_type: str = "application/octet-stream",
        doc_category: Optional[str] = None,
        run_inline: bool = True,
    ) -> Dict[str, Any]:
        """
        Validate, store, register catalog entry, and launch background ingestion pipeline.
        Returns document metadata and tracking job.
        """
        context.validate_deal_access(deal_id)

        ext = os.path.splitext(filename)[1].lower().lstrip(".")
        if ext not in ["pdf", "docx", "doc", "xlsx", "xls", "txt", "csv", "md", "json", "html"]:
            raise ValidationException(f"Unsupported file extension: .{ext}")

        # Save to tenant-isolated disk storage
        storage_path, sha256_hash, size_bytes = await self.storage.save_document(
            organization_id=context.organization_id,
            deal_id=deal_id,
            filename=filename,
            file_bytes=file_bytes,
        )

        # Create Document catalog record
        doc = await self.repo.create_document(
            organization_id=context.organization_id,
            deal_id=deal_id,
            name=filename,
            file_type=ext.upper(),
            mime_type=mime_type,
            size_bytes=size_bytes,
            storage_path=storage_path,
            sha256_hash=sha256_hash,
            doc_category=doc_category,
            uploaded_by_id=context.user_id,
            status="QUEUED",
        )
        await self.session.commit()

        # Dispatch ingestion job
        job = await dispatch_ingestion_pipeline(
            session=self.session,
            organization_id=context.organization_id,
            deal_id=deal_id,
            document_id=doc.id,
            storage_path=storage_path,
            filename=filename,
            mime_type=mime_type,
            run_inline=run_inline,
        )

        return {
            "document": doc,
            "job": job,
        }

    async def list_document_chunks(
        self, context: TenantContext, deal_id: uuid.UUID, document_id: uuid.UUID
    ) -> List[DocumentChunk]:
        """Fetch all indexed chunks for a document with page and section metadata."""
        context.validate_deal_access(deal_id)
        # Verify doc exists
        await self.get_document(context, deal_id, document_id)
        return await self.repo.list_chunks_for_document(context.organization_id, deal_id, document_id)

    async def search_evidence(
        self,
        context: TenantContext,
        deal_id: uuid.UUID,
        query: str,
        top_k: int = 5,
        min_similarity: float = 0.2,
    ) -> List[Dict[str, Any]]:
        """Perform semantic similarity search over deal documents."""
        context.validate_deal_access(deal_id)

        embedding_provider = get_embedding_provider()
        query_vector = await embedding_provider.embed_query(query)

        results = await self.repo.search_vector_chunks(
            organization_id=context.organization_id,
            deal_id=deal_id,
            query_embedding=query_vector,
            top_k=top_k,
            min_similarity=min_similarity,
        )

        formatted_results = []
        for chunk, similarity in results:
            formatted_results.append(
                {
                    "chunk_id": str(chunk.id),
                    "document_id": str(chunk.document_id),
                    "document_name": chunk.document.name if chunk.document else "Document",
                    "page_number": chunk.page_number,
                    "section_title": chunk.section_title,
                    "content": chunk.content,
                    "similarity_score": similarity,
                    "metadata": chunk.metadata_json or {},
                }
            )

        return formatted_results

    async def get_job_status(self, context: TenantContext, job_id: uuid.UUID) -> JobExecution:
        """Fetch background job progress and status."""
        job = await self.job_repo.get_job_by_id(context.organization_id, job_id)
        if not job:
            raise NotFoundException("JobExecution", job_id)
        return job
