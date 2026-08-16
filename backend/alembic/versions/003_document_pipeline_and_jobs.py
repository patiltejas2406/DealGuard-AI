"""Document Pipeline Indexing and Job Execution Optimization.

Revision ID: 003_document_pipeline_and_jobs
Revises: 002_auth_sessions_and_rbac_hardening
Create Date: 2026-08-16 17:10:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "003_document_pipeline_and_jobs"
down_revision: Union[str, None] = "002_auth_sessions_and_rbac_hardening"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Optimize chunk indexing and job query paths
    op.create_index("ix_chunks_doc_chunk_idx", "document_chunks", ["document_id", "chunk_index"])
    op.create_index("ix_job_executions_deal_type", "job_executions", ["deal_id", "job_type"])


def downgrade() -> None:
    op.drop_index("ix_job_executions_deal_type", table_name="job_executions")
    op.drop_index("ix_chunks_doc_chunk_idx", table_name="document_chunks")
