"""Celery Tasks & Async Dispatcher for Business Telemetry Synchronization Pipeline."""

import logging
import uuid
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.celery_app import celery_app
from app.core.config import settings
from app.core.database import async_session_factory
from app.domains.jobs.models import JobExecution
from app.domains.documents.repository import JobRepository
from app.domains.telemetry.sync_engine import TelemetrySyncEngine

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=2, default_retry_delay=15, name="telemetry.sync_connection")
def sync_connection_task(
    self,
    organization_id_str: str,
    connection_id_str: str,
    job_id_str: str,
    is_full_sync: bool = False,
) -> dict:
    """Celery background worker task for external business telemetry synchronization."""
    import asyncio

    async def _async_run():
        async with async_session_factory() as session:
            job_repo = JobRepository(session)
            org_id = uuid.UUID(organization_id_str)
            conn_id = uuid.UUID(connection_id_str)
            job_id = uuid.UUID(job_id_str)

            try:
                await job_repo.update_job_progress(
                    organization_id=org_id,
                    job_id=job_id,
                    status="RUNNING",
                    progress_pct=15,
                )
                await session.commit()

                engine = TelemetrySyncEngine(session)
                sync_run = await engine.execute_sync(
                    organization_id=org_id,
                    connection_id=conn_id,
                    is_full_sync=is_full_sync,
                )

                await job_repo.update_job_progress(
                    organization_id=org_id,
                    job_id=job_id,
                    status="COMPLETED" if sync_run.status != "FAILED" else "FAILED",
                    progress_pct=100,
                    error_message=sync_run.error_message,
                    result_metadata={
                        "sync_run_id": str(sync_run.id),
                        "records_fetched": sync_run.records_fetched,
                        "records_upserted": sync_run.records_upserted,
                        "records_failed": sync_run.records_failed,
                    },
                )
                await session.commit()
                return {"status": sync_run.status, "sync_run_id": str(sync_run.id)}
            except Exception as exc:
                logger.error(f"Celery task exception during telemetry sync: {str(exc)}", exc_info=True)
                await job_repo.update_job_progress(
                    organization_id=org_id,
                    job_id=job_id,
                    status="FAILED",
                    progress_pct=100,
                    error_message=str(exc),
                )
                await session.commit()
                raise exc

    return asyncio.run(_async_run())


async def dispatch_telemetry_sync(
    session: AsyncSession,
    organization_id: uuid.UUID,
    deal_id: uuid.UUID,
    connection_id: uuid.UUID,
    is_full_sync: bool = False,
    run_inline: bool = True,
) -> JobExecution:
    """Create a tracked JobExecution and dispatch connection synchronization.
    
    In test/dev environments, executes inline. In production, dispatches to Celery.
    """
    job_repo = JobRepository(session)
    job = await job_repo.create_job(
        organization_id=organization_id,
        deal_id=deal_id,
        job_type="TELEMETRY_SYNC",
        result_metadata={"connection_id": str(connection_id), "is_full_sync": is_full_sync},
    )
    await session.commit()

    if run_inline or settings.ENVIRONMENT in ["test", "development"]:
        engine = TelemetrySyncEngine(session)
        sync_run = await engine.execute_sync(
            organization_id=organization_id,
            connection_id=connection_id,
            is_full_sync=is_full_sync,
        )
        await job_repo.update_job_progress(
            organization_id=organization_id,
            job_id=job.id,
            status="COMPLETED" if sync_run.status != "FAILED" else "FAILED",
            progress_pct=100,
            error_message=sync_run.error_message,
            result_metadata={
                "sync_run_id": str(sync_run.id),
                "records_fetched": sync_run.records_fetched,
                "records_upserted": sync_run.records_upserted,
                "records_failed": sync_run.records_failed,
            },
        )
        await session.commit()
    else:
        task = sync_connection_task.delay(
            str(organization_id),
            str(connection_id),
            str(job.id),
            is_full_sync,
        )
        await job_repo.update_job_progress(
            organization_id=organization_id,
            job_id=job.id,
            status="QUEUED",
            progress_pct=0,
            result_metadata={"celery_task_id": task.id, "connection_id": str(connection_id)},
        )
        await session.commit()

    return job
