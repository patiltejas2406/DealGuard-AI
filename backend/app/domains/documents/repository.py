"""Document, Chunk and Citation Repository Layer."""

import uuid
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.domains.documents.models import Citation, Document, DocumentChunk, DocumentVersion


class DocumentRepository:
    """Tenant-scoped persistence operations for Diligence Documents & Citations."""

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
            .options(selectinload(Document.versions))
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
        )
        self.session.add(version)
        await self.session.flush()
        return doc

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
