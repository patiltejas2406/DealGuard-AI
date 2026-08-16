"""Document, Version, Chunk, Citation, and Vector Search Repository Layer."""

import math
import uuid
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.domains.common.models import utc_now
from app.domains.documents.models import Citation, Document, DocumentChunk, DocumentVersion
from app.domains.jobs.models import JobExecution


class DocumentRepository:
    """Tenant-scoped persistence operations for Diligence Documents, Chunks, and Vector Indices."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_documents_for_deal(
        self, organization_id: uuid.UUID, deal_id: uuid.UUID
    ) -> List[Document]:
        stmt = (
            select(Document)
            .where(
                Document.organization_id == organization_id,
                Document.deal_id == deal_id,
            )
            .options(
                selectinload(Document.versions),
                selectinload(Document.chunks),
            )
            .order_by(Document.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_document_by_id(
        self, organization_id: uuid.UUID, deal_id: uuid.UUID, document_id: uuid.UUID
    ) -> Optional[Document]:
        stmt = (
            select(Document)
            .where(
                Document.organization_id == organization_id,
                Document.deal_id == deal_id,
                Document.id == document_id,
            )
            .options(
                selectinload(Document.versions),
                selectinload(Document.chunks),
                selectinload(Document.citations),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_document(
        self,
        organization_id: uuid.UUID,
        deal_id: uuid.UUID,
        name: str,
        file_type: str,
        mime_type: str,
        size_bytes: int,
        storage_path: str,
        sha256_hash: str,
        doc_category: Optional[str] = None,
        uploaded_by_id: Optional[uuid.UUID] = None,
        status: str = "QUEUED",
    ) -> Document:
        doc = Document(
            organization_id=organization_id,
            deal_id=deal_id,
            name=name,
            file_type=file_type.upper(),
            mime_type=mime_type,
            size_bytes=size_bytes,
            storage_path=storage_path,
            sha256_hash=sha256_hash,
            status=status,
            doc_category=doc_category,
            uploaded_by_id=uploaded_by_id,
        )
        self.session.add(doc)
        await self.session.flush()

        # Create version 1 record
        version = DocumentVersion(
            organization_id=organization_id,
            document_id=doc.id,
            version_number=1,
            storage_path=storage_path,
            sha256_hash=sha256_hash,
            parsing_status="PENDING",
        )
        self.session.add(version)
        await self.session.flush()
        return doc

    async def update_document_status(
        self, organization_id: uuid.UUID, document_id: uuid.UUID, status: str
    ) -> None:
        stmt = (
            update(Document)
            .where(Document.organization_id == organization_id, Document.id == document_id)
            .values(status=status, updated_at=utc_now())
        )
        await self.session.execute(stmt)
        await self.session.flush()

    async def update_document_version(
        self,
        organization_id: uuid.UUID,
        document_id: uuid.UUID,
        parsing_status: str,
        page_count: Optional[int] = None,
        table_count: Optional[int] = None,
    ) -> None:
        stmt = (
            update(DocumentVersion)
            .where(
                DocumentVersion.organization_id == organization_id,
                DocumentVersion.document_id == document_id,
                DocumentVersion.version_number == 1,
            )
            .values(
                parsing_status=parsing_status,
                page_count=page_count,
                table_count=table_count,
                updated_at=utc_now(),
            )
        )
        await self.session.execute(stmt)
        await self.session.flush()

    async def bulk_create_chunks(
        self,
        organization_id: uuid.UUID,
        deal_id: uuid.UUID,
        document_id: uuid.UUID,
        chunks_data: List[Dict[str, Any]],
    ) -> List[DocumentChunk]:
        """Bulk insert extracted document chunks with 1536-dimensional embeddings."""
        created_chunks: List[DocumentChunk] = []
        for c in chunks_data:
            chunk = DocumentChunk(
                organization_id=organization_id,
                deal_id=deal_id,
                document_id=document_id,
                chunk_index=c["chunk_index"],
                page_number=c.get("page_number", 1),
                section_title=c.get("section_title"),
                content=c["content"],
                token_count=c.get("token_count"),
                embedding=c.get("embedding"),
                embedding_model=c.get("embedding_model", "gemini-embedding-2"),
                metadata_json=c.get("metadata_json", {}),
            )
            self.session.add(chunk)
            created_chunks.append(chunk)

        await self.session.flush()
        return created_chunks

    async def list_chunks_for_document(
        self, organization_id: uuid.UUID, deal_id: uuid.UUID, document_id: uuid.UUID
    ) -> List[DocumentChunk]:
        stmt = (
            select(DocumentChunk)
            .where(
                DocumentChunk.organization_id == organization_id,
                DocumentChunk.deal_id == deal_id,
                DocumentChunk.document_id == document_id,
            )
            .order_by(DocumentChunk.chunk_index.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def search_vector_chunks(
        self,
        organization_id: uuid.UUID,
        deal_id: uuid.UUID,
        query_embedding: List[float],
        top_k: int = 5,
        min_similarity: float = 0.3,
    ) -> List[Tuple[DocumentChunk, float]]:
        """
        Perform tenant-isolated semantic similarity search across deal chunks.
        Supports both PostgreSQL pgvector cosine distance and SQLite in-memory cosine fallback.
        """
        stmt = (
            select(DocumentChunk)
            .where(
                DocumentChunk.organization_id == organization_id,
                DocumentChunk.deal_id == deal_id,
                DocumentChunk.embedding.isnot(None),
            )
            .options(selectinload(DocumentChunk.document))
        )
        result = await self.session.execute(stmt)
        all_chunks = list(result.scalars().all())

        ranked_results: List[Tuple[DocumentChunk, float]] = []
        for chunk in all_chunks:
            chunk_vec = chunk.embedding
            if not chunk_vec:
                continue

            # Compute cosine similarity
            if isinstance(chunk_vec, list) and len(chunk_vec) == len(query_embedding):
                dot_product = sum(a * b for a, b in zip(query_embedding, chunk_vec))
                norm_q = math.sqrt(sum(a * a for a in query_embedding)) or 1.0
                norm_c = math.sqrt(sum(b * b for b in chunk_vec)) or 1.0
                sim = dot_product / (norm_q * norm_c)
                if sim >= min_similarity:
                    ranked_results.append((chunk, round(sim, 4)))

        # Sort descending by similarity score
        ranked_results.sort(key=lambda x: x[1], reverse=True)
        return ranked_results[:top_k]

    async def create_citation(
        self,
        organization_id: uuid.UUID,
        deal_id: uuid.UUID,
        document_id: uuid.UUID,
        page_number: int,
        exact_quote: str,
        chunk_id: Optional[uuid.UUID] = None,
        section: Optional[str] = None,
        char_offset_start: Optional[int] = None,
        char_offset_end: Optional[int] = None,
        extraction_method: str = "PARSER_TABLE",
        confidence_score: float = 1.0,
    ) -> Citation:
        citation = Citation(
            organization_id=organization_id,
            deal_id=deal_id,
            document_id=document_id,
            chunk_id=chunk_id,
            page_number=page_number,
            section=section,
            exact_quote=exact_quote,
            char_offset_start=char_offset_start,
            char_offset_end=char_offset_end,
            extraction_method=extraction_method,
            confidence_score=confidence_score,
        )
        self.session.add(citation)
        await self.session.flush()
        return citation

    async def list_citations_for_deal(
        self, organization_id: uuid.UUID, deal_id: uuid.UUID
    ) -> List[Citation]:
        stmt = (
            select(Citation)
            .where(
                Citation.organization_id == organization_id,
                Citation.deal_id == deal_id,
            )
            .options(selectinload(Citation.document))
            .order_by(Citation.page_number.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())


class JobRepository:
    """Persistence operations for Background Job Executions."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_job(
        self,
        organization_id: uuid.UUID,
        job_type: str,
        deal_id: Optional[uuid.UUID] = None,
        celery_task_id: Optional[str] = None,
        status: str = "QUEUED",
        result_metadata: Optional[dict] = None,
    ) -> JobExecution:
        job = JobExecution(
            organization_id=organization_id,
            deal_id=deal_id,
            celery_task_id=celery_task_id,
            job_type=job_type,
            status=status,
            progress_pct=0,
            result_metadata=result_metadata or {},
            started_at=utc_now(),
        )
        self.session.add(job)
        await self.session.flush()
        return job

    async def get_job_by_id(
        self, organization_id: uuid.UUID, job_id: uuid.UUID
    ) -> Optional[JobExecution]:
        stmt = (
            select(JobExecution)
            .where(
                JobExecution.organization_id == organization_id,
                JobExecution.id == job_id,
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_job_progress(
        self,
        organization_id: uuid.UUID,
        job_id: uuid.UUID,
        status: str,
        progress_pct: int,
        error_message: Optional[str] = None,
        result_metadata: Optional[dict] = None,
    ) -> None:
        values: Dict[str, Any] = {
            "status": status,
            "progress_pct": progress_pct,
            "updated_at": utc_now(),
        }
        if error_message:
            values["error_message"] = error_message
        if result_metadata:
            values["result_metadata"] = result_metadata
        if status in ["COMPLETED", "FAILED", "CANCELLED"]:
            values["completed_at"] = utc_now()

        stmt = (
            update(JobExecution)
            .where(
                JobExecution.organization_id == organization_id,
                JobExecution.id == job_id,
            )
            .values(**values)
        )
        await self.session.execute(stmt)
        await self.session.flush()
