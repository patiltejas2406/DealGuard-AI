"""Document Ingestion, Versioning, Chunks & Evidence Citation Models."""

import uuid
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import BigInteger, Boolean, Float, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.domains.common.models import TenantScopedModel
from app.domains.common.types import CompatibleJSON, CompatibleVector

if TYPE_CHECKING:
    from app.domains.deals.models import Deal
    from app.domains.risk.models import RiskEvidence
    from app.domains.financials.models import FinancialStatement


class Document(TenantScopedModel):
    """Catalog record for a file uploaded to the Diligence Data Room."""
    __tablename__ = "documents"

    deal_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("deals.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)  # PDF, XLSX, DOCX, CSV
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    storage_path: Mapped[str] = mapped_column(String(500), nullable=False)
    sha256_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(50), default="UPLOADED", nullable=False, index=True)
    doc_category: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # FINANCIAL, LEGAL, OPERATIONAL
    
    uploaded_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    # Relationships
    deal: Mapped["Deal"] = relationship("Deal", back_populates="documents")
    versions: Mapped[List["DocumentVersion"]] = relationship(
        "DocumentVersion", back_populates="document", cascade="all, delete-orphan"
    )
    chunks: Mapped[List["DocumentChunk"]] = relationship(
        "DocumentChunk", back_populates="document", cascade="all, delete-orphan"
    )
    citations: Mapped[List["Citation"]] = relationship(
        "Citation", back_populates="document", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_documents_org_deal", "organization_id", "deal_id"),
        Index("ix_documents_deal_hash", "deal_id", "sha256_hash"),
    )


class DocumentVersion(TenantScopedModel):
    """Immutable document version record for reproducibility."""
    __tablename__ = "document_versions"

    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    version_number: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    storage_path: Mapped[str] = mapped_column(String(500), nullable=False)
    sha256_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    parsing_status: Mapped[str] = mapped_column(String(50), default="PENDING", nullable=False)
    page_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    table_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Relationships
    document: Mapped["Document"] = relationship("Document", back_populates="versions")

    __table_args__ = (
        UniqueConstraint("document_id", "version_number", name="uq_doc_version"),
    )


class DocumentChunk(TenantScopedModel):
    """Searchable chunk with metadata breadcrumbs and 1536-dimensional vector embedding."""
    __tablename__ = "document_chunks"

    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    deal_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("deals.id", ondelete="CASCADE"), nullable=False, index=True
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    page_number: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    section_title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    token_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # 1536-dimensional embedding vector (pgvector compatible)
    embedding = mapped_column(CompatibleVector(1536), nullable=True)
    embedding_model: Mapped[str] = mapped_column(String(100), default="gemini-embedding-2", nullable=False)
    metadata_json: Mapped[Optional[dict]] = mapped_column(CompatibleJSON, default=dict, nullable=True)

    # Relationships
    document: Mapped["Document"] = relationship("Document", back_populates="chunks")
    citations: Mapped[List["Citation"]] = relationship("Citation", back_populates="chunk")

    __table_args__ = (
        Index("ix_chunks_org_deal_page", "organization_id", "deal_id", "page_number"),
    )


class Citation(TenantScopedModel):
    """First-class evidence citation binding AI findings and financial numbers to raw documents."""
    __tablename__ = "citations"

    deal_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("deals.id", ondelete="CASCADE"), nullable=False, index=True
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    chunk_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("document_chunks.id", ondelete="SET NULL"), nullable=True, index=True
    )
    page_number: Mapped[int] = mapped_column(Integer, nullable=False)
    section: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    exact_quote: Mapped[str] = mapped_column(Text, nullable=False)
    char_offset_start: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    char_offset_end: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    extraction_method: Mapped[str] = mapped_column(String(50), default="PARSER_TABLE", nullable=False)
    source_entity_type: Mapped[str] = mapped_column(String(50), default="DOCUMENT", nullable=False)  # DOCUMENT, FINANCIAL_RECORD, CONTRACT_CLAUSE, INTEGRATION_DATA, EXTERNAL_SOURCE
    confidence_score: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)

    # Relationships
    document: Mapped["Document"] = relationship("Document", back_populates="citations")
    chunk: Mapped[Optional["DocumentChunk"]] = relationship("DocumentChunk", back_populates="citations")
    risk_evidence: Mapped[List["RiskEvidence"]] = relationship("RiskEvidence", back_populates="citation")

    __table_args__ = (
        Index("ix_citations_deal_doc", "deal_id", "document_id"),
    )
