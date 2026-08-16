"""Document Ingestion & Multi-Stage Vectorization Pipeline."""

import os
import uuid
from typing import Any, Dict, List
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.logging import get_logger
from app.domains.ai.embeddings.factory import get_embedding_provider
from app.domains.audit.service import AuditService
from app.domains.documents.chunker import LayoutAwareChunker
from app.domains.documents.parsers.extractor import DocumentExtractorRegistry
from app.domains.documents.repository import DocumentRepository, JobRepository
from app.domains.documents.storage import DocumentStorageManager

logger = get_logger("document.pipeline")


class DocumentIngestionPipeline:
    """Executes multi-stage asynchronous extraction, chunking, and embedding generation."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.doc_repo = DocumentRepository(session)
        self.job_repo = JobRepository(session)
        self.audit_service = AuditService(session)
        self.extractor = DocumentExtractorRegistry()
        self.chunker = LayoutAwareChunker()
        self.storage = DocumentStorageManager()

    async def execute(
        self,
        organization_id: uuid.UUID,
        deal_id: uuid.UUID,
        document_id: uuid.UUID,
        job_id: uuid.UUID,
        storage_path: str,
        filename: str,
        mime_type: str = "",
    ) -> Dict[str, Any]:
        """Run the complete 5-stage ingestion pipeline with progress reporting."""
        try:
            # Stage 1: EXTRACTING (20%)
            logger.info("Starting document extraction", extra={"document_id": str(document_id), "stage": "EXTRACTING"})
            await self.job_repo.update_job_progress(
                organization_id=organization_id,
                job_id=job_id,
                status="EXTRACTING",
                progress_pct=20,
            )
            await self.session.commit()

            file_bytes = await self.storage.read_document(storage_path)
            parsed_doc = await self.extractor.extract(file_bytes, filename, mime_type)

            # Stage 2: CHUNKING (45%)
            logger.info("Starting document chunking", extra={"document_id": str(document_id), "stage": "CHUNKING"})
            await self.job_repo.update_job_progress(
                organization_id=organization_id,
                job_id=job_id,
                status="CHUNKING",
                progress_pct=45,
            )
            await self.session.commit()

            raw_chunks = self.chunker.chunk_document(parsed_doc, filename)

            # Stage 3: EMBEDDING (70%)
            logger.info("Starting embedding generation", extra={"document_id": str(document_id), "stage": "EMBEDDING", "chunk_count": len(raw_chunks)})
            await self.job_repo.update_job_progress(
                organization_id=organization_id,
                job_id=job_id,
                status="EMBEDDING",
                progress_pct=70,
            )
            await self.session.commit()

            embedding_provider = get_embedding_provider()
            chunk_texts = [c.content for c in raw_chunks]
            embeddings = await embedding_provider.embed_texts(chunk_texts)

            # Stage 4: INDEXING (90%)
            logger.info("Starting chunk and vector indexing", extra={"document_id": str(document_id), "stage": "INDEXING"})
            await self.job_repo.update_job_progress(
                organization_id=organization_id,
                job_id=job_id,
                status="INDEXING",
                progress_pct=90,
            )

            chunks_data: List[Dict[str, Any]] = []
            for i, chunk in enumerate(raw_chunks):
                vec = embeddings[i] if i < len(embeddings) else None
                chunks_data.append(
                    {
                        "chunk_index": chunk.chunk_index,
                        "page_number": chunk.page_number,
                        "section_title": chunk.section_title,
                        "content": chunk.content,
                        "token_count": chunk.token_count,
                        "embedding": vec,
                        "embedding_model": embedding_provider.model_name,
                        "metadata_json": {
                            **chunk.metadata,
                            "char_offset_start": chunk.char_offset_start,
                            "char_offset_end": chunk.char_offset_end,
                            "source_type": chunk.source_type,
                        },
                    }
                )

            await self.doc_repo.bulk_create_chunks(
                organization_id=organization_id,
                deal_id=deal_id,
                document_id=document_id,
                chunks_data=chunks_data,
            )

            await self.doc_repo.update_document_version(
                organization_id=organization_id,
                document_id=document_id,
                parsing_status="PARSED",
                page_count=parsed_doc.page_count,
                table_count=parsed_doc.table_count,
            )

            await self.doc_repo.update_document_status(
                organization_id=organization_id,
                document_id=document_id,
                status="INDEXED",
            )

            # Stage 5: COMPLETED (100%)
            result_meta = {
                "document_id": str(document_id),
                "chunks_count": len(raw_chunks),
                "page_count": parsed_doc.page_count,
                "table_count": parsed_doc.table_count,
                "embedding_model": embedding_provider.model_name,
            }

            await self.job_repo.update_job_progress(
                organization_id=organization_id,
                job_id=job_id,
                status="COMPLETED",
                progress_pct=100,
                result_metadata=result_meta,
            )

            await self.audit_service.log_event(
                organization_id=organization_id,
                deal_id=deal_id,
                action="DOCUMENT_INGESTED",
                entity_type="Document",
                entity_id=document_id,
                details=result_meta,
            )

            await self.session.commit()
            logger.info("Document pipeline completed successfully", extra={"document_id": str(document_id)})
            return result_meta

        except Exception as exc:
            logger.error("Document ingestion pipeline failure", extra={"document_id": str(document_id), "error": str(exc)})
            await self.session.rollback()

            # Record failure status
            await self.doc_repo.update_document_status(
                organization_id=organization_id,
                document_id=document_id,
                status="FAILED",
            )
            await self.job_repo.update_job_progress(
                organization_id=organization_id,
                job_id=job_id,
                status="FAILED",
                progress_pct=0,
                error_message=str(exc),
            )
            await self.audit_service.log_event(
                organization_id=organization_id,
                deal_id=deal_id,
                action="DOCUMENT_INGESTION_FAILED",
                entity_type="Document",
                entity_id=document_id,
                details={"error": str(exc)},
            )
            await self.session.commit()
            raise exc
