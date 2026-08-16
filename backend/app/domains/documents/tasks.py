"""Celery Tasks & Async Dispatcher for Document Ingestion Pipeline."""

import asyncio
import uuid
from typing import Optional
from app.core.celery_app import celery_app
from app.core.config import settings
from app.core.database import get_session_factory
from app.core.logging import get_logger
from app.domains.jobs.models import JobExecution
from app.domains.documents.pipeline import DocumentIngestionPipeline
from app.domains.documents.repository import JobRepository


logger = get_logger("document.tasks")


@celery_app.task(bind=True, max_retries=2, default_retry_delay=10, name="documents.ingest_document")
def ingest_document_task(
    self,
    organization_id_str: str,
    deal_id_str: str,
    document_id_str: str,
    job_id_str: str,
    storage_path: str,
    filename: str,
    mime_type: str = "",
) -> dict:
    """Celery background worker task for document ingestion pipeline."""
    org_id = uuid.UUID(organization_id_str)
    deal_id = uuid.UUID(deal_id_str)
    doc_id = uuid.UUID(document_id_str)
    job_id = uuid.UUID(job_id_str)

    async def _runner():
        session_factory = get_session_factory()
        async with session_factory() as session:
            pipeline = DocumentIngestionPipeline(session)
            return await pipeline.execute(
                organization_id=org_id,
                deal_id=deal_id,
                document_id=doc_id,
                job_id=job_id,
                storage_path=storage_path,
                filename=filename,
                mime_type=mime_type,
            )

    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import nest_asyncio
            nest_asyncio.apply()
            return loop.run_until_complete(_runner())
        else:
            return asyncio.run(_runner())
    except Exception as exc:
        logger.error("Celery task exception during document ingestion", extra={"job_id": job_id_str, "error": str(exc)})
        raise self.retry(exc=exc)


async def dispatch_ingestion_pipeline(
    session,
    organization_id: uuid.UUID,
    deal_id: uuid.UUID,
    document_id: uuid.UUID,
    storage_path: str,
    filename: str,
    mime_type: str = "",
    run_inline: bool = True,
) -> JobExecution:
    """
    Create a tracked JobExecution and dispatch document ingestion.
    In testing or single-process mode, runs inline; in production, dispatches to Celery.
    """
    job_repo = JobRepository(session)
    job = await job_repo.create_job(
        organization_id=organization_id,
        deal_id=deal_id,
        job_type="DOCUMENT_INGESTION",
        result_metadata={"document_id": str(document_id), "filename": filename},
    )
    await session.commit()

    if run_inline or settings.ENVIRONMENT in ["test", "development"]:
        pipeline = DocumentIngestionPipeline(session)
        await pipeline.execute(
            organization_id=organization_id,
            deal_id=deal_id,
            document_id=document_id,
            job_id=job.id,
            storage_path=storage_path,
            filename=filename,
            mime_type=mime_type,
        )
    else:
        # Dispatch to Celery background worker
        task = ingest_document_task.delay(
            str(organization_id),
            str(deal_id),
            str(document_id),
            str(job.id),
            storage_path,
            filename,
            mime_type,
        )
        await job_repo.update_job_progress(
            organization_id=organization_id,
            job_id=job.id,
            status="QUEUED",
            progress_pct=0,
            result_metadata={"celery_task_id": task.id},
        )
        await session.commit()

    return job
