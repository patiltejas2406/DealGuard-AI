"""Tests for Multi-Stage Document Ingestion Pipeline & Background Jobs."""

import uuid
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.domains.audit.models import AuditEvent
from app.domains.auth.models import Organization, User
from app.domains.deals.models import Deal, TargetCompany
from app.domains.documents.models import Document, DocumentChunk, DocumentVersion
from app.domains.documents.pipeline import DocumentIngestionPipeline
from app.domains.documents.repository import DocumentRepository, JobRepository
from app.domains.documents.storage import DocumentStorageManager
from app.domains.jobs.models import JobExecution


@pytest.mark.asyncio
async def test_document_ingestion_pipeline_success(db_session: AsyncSession):
    """Verify 5-stage ingestion pipeline executes cleanly and indexes chunks."""
    org_id = uuid.uuid4()
    deal_id = uuid.uuid4()

    # Pre-seed DB
    org = Organization(id=org_id, name="Bain Capital", slug="bain-cap", tier="ENTERPRISE")
    target = TargetCompany(organization_id=org_id, name="CloudScale Inc", industry="Software")
    db_session.add(org)
    db_session.add(target)
    await db_session.flush()

    deal = Deal(id=deal_id, organization_id=org_id, target_company_id=target.id, title="Project CloudScale")
    db_session.add(deal)
    await db_session.commit()


    # Save test document to storage
    storage = DocumentStorageManager()
    file_content = (
        "# Executive Overview\n\n"
        "CloudScale Inc provides enterprise database infrastructure.\n\n"
        "# Financial Performance\n\n"
        "FY2023 Revenue reached $52.4M with 82% Gross Margin."
    ).encode("utf-8")

    storage_path, sha256_hash, size_bytes = await storage.save_document(
        organization_id=org_id,
        deal_id=deal_id,
        filename="CloudScale_Overview.txt",
        file_bytes=file_content,
    )

    doc_repo = DocumentRepository(db_session)
    job_repo = JobRepository(db_session)

    doc = await doc_repo.create_document(
        organization_id=org_id,
        deal_id=deal_id,
        name="CloudScale_Overview.txt",
        file_type="TXT",
        mime_type="text/plain",
        size_bytes=size_bytes,
        storage_path=storage_path,
        sha256_hash=sha256_hash,
    )
    job = await job_repo.create_job(
        organization_id=org_id,
        deal_id=deal_id,
        job_type="DOCUMENT_INGESTION",
    )
    await db_session.commit()

    # Run Pipeline
    pipeline = DocumentIngestionPipeline(db_session)
    result = await pipeline.execute(
        organization_id=org_id,
        deal_id=deal_id,
        document_id=doc.id,
        job_id=job.id,
        storage_path=storage_path,
        filename="CloudScale_Overview.txt",
        mime_type="text/plain",
    )

    assert result["chunks_count"] >= 2
    assert result["document_id"] == str(doc.id)

    # Check Document Status is INDEXED
    retrieved_doc = await doc_repo.get_document_by_id(org_id, deal_id, doc.id)
    assert retrieved_doc is not None
    assert retrieved_doc.status == "INDEXED"

    # Check Chunks in DB
    chunks = await doc_repo.list_chunks_for_document(org_id, deal_id, doc.id)
    assert len(chunks) >= 2
    assert chunks[0].embedding is not None

    # Check Job Status is COMPLETED (100%)
    retrieved_job = await job_repo.get_job_by_id(org_id, job.id)
    assert retrieved_job.status == "COMPLETED"
    assert retrieved_job.progress_pct == 100

    # Check Audit Log
    stmt = select(AuditEvent).where(
        AuditEvent.action == "DOCUMENT_INGESTED",
        AuditEvent.entity_id == doc.id,
    )
    audit_res = await db_session.execute(stmt)
    assert audit_res.scalar_one_or_none() is not None
