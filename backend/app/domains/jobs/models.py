"""Asynchronous Background Job and Task Execution Tracking Models."""

import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.domains.common.models import TenantScopedModel
from app.domains.common.types import CompatibleJSON


class JobExecution(TenantScopedModel):
    """Persistent tracking record for Celery background worker executions."""
    __tablename__ = "job_executions"

    deal_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("deals.id", ondelete="CASCADE"), nullable=True, index=True
    )
    celery_task_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    job_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)  # DOCUMENT_INGESTION, EMBEDDING_GEN, etc.
    status: Mapped[str] = mapped_column(String(50), default="QUEUED", nullable=False, index=True)
    progress_pct: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    result_metadata: Mapped[Optional[dict]] = mapped_column(CompatibleJSON, default=dict, nullable=True)
    
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_job_executions_org_status", "organization_id", "status"),
    )
