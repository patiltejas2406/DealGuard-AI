"""Document and Evidence Citation Domain Service."""

import uuid
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import NotFoundException
from app.domains.common.context import TenantContext
from app.domains.documents.models import Citation, Document
from app.domains.documents.repository import DocumentRepository


class DocumentService:
    """Business operations for Diligence Data Room & Citations."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = DocumentRepository(session)

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
        )
        await self.session.commit()
        return doc
