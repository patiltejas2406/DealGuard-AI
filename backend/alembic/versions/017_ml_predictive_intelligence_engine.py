"""ML Predictive Intelligence Engine — Datasets and Training Runs Tables.

Revision ID: 017_ml_predictive_intelligence_engine
Revises: 016_agentic_orchestration_foundation
Create Date: 2026-08-28 17:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "017_ml_predictive_intelligence_engine"
down_revision: Union[str, None] = "016_agentic_orchestration_foundation"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    is_postgres = bind.dialect.name == "postgresql"

    json_type = postgresql.JSONB(astext_type=sa.Text()) if is_postgres else sa.JSON()
    uuid_type = postgresql.UUID(as_uuid=True) if is_postgres else sa.String(36)

    # 1. Create ml_datasets table
    op.create_table(
        "ml_datasets",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("organization_id", uuid_type, sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("dataset_key", sa.String(100), nullable=False, unique=True, index=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("version", sa.String(30), nullable=False, server_default="1.0.0"),
        sa.Column("source", sa.String(255), nullable=False),
        sa.Column("task_type", sa.String(50), nullable=False, index=True),
        sa.Column("target_name", sa.String(100), nullable=False),
        sa.Column("row_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("feature_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("data_checksum", sa.String(64), nullable=False),
        sa.Column("is_benchmark", sa.Boolean(), nullable=False, server_default=sa.text("0" if not is_postgres else "false")),
        sa.Column("metadata_json", json_type, nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_ml_datasets_org_task", "ml_datasets", ["organization_id", "task_type"])

    # 2. Create ml_training_runs table
    op.create_table(
        "ml_training_runs",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("organization_id", uuid_type, sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("model_id", sa.String(100), nullable=False, index=True),
        sa.Column("dataset_key", sa.String(100), nullable=False, index=True),
        sa.Column("status", sa.String(30), nullable=False, server_default="COMPLETED"),
        sa.Column("parameters_json", json_type, nullable=False),
        sa.Column("metrics_json", json_type, nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("duration_ms", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_ml_training_runs_model", "ml_training_runs", ["organization_id", "model_id"])


def downgrade() -> None:
    op.drop_index("ix_ml_training_runs_model", table_name="ml_training_runs")
    op.drop_table("ml_training_runs")
    op.drop_index("ix_ml_datasets_org_task", table_name="ml_datasets")
    op.drop_table("ml_datasets")
