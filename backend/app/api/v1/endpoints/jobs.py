"""Background Job Execution Status Endpoints."""

import uuid
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_tenant_context
from app.api.v1.schemas.documents import JobExecutionResponse
from app.core.database import get_db
from app.domains.common.context import TenantContext
from app.domains.documents.service import DocumentService

router = APIRouter(prefix="/jobs", tags=["Background Jobs & Pipeline Progress"])


@router.get(
    "/{job_id}",
    summary="Get Background Job Execution Status and Progress",
    status_code=status.HTTP_200_OK,
    response_model=JobExecutionResponse,
)
async def get_job_status(
    job_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    context: TenantContext = Depends(get_tenant_context),
) -> JobExecutionResponse:
    """Fetch live progress percentage, stage lifecycle state, and error logs for a background job."""
    service = DocumentService(db)
    job = await service.get_job_status(context, job_id)
    return JobExecutionResponse.model_validate(job)
