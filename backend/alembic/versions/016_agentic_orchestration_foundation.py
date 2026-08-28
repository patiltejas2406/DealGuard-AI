"""Agentic Orchestration Foundation & ML Architecture Tables.

Revision ID: 016_agentic_orchestration_foundation
Revises: 015_add_copilot_messages_updated_at
Create Date: 2026-08-28 15:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "016_agentic_orchestration_foundation"
down_revision: Union[str, None] = "015_add_copilot_messages_updated_at"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    is_postgres = bind.dialect.name == "postgresql"

    json_type = postgresql.JSONB(astext_type=sa.Text()) if is_postgres else sa.JSON()
    uuid_type = postgresql.UUID(as_uuid=True) if is_postgres else sa.String(36)

    # 1. Create agent_executions table
    op.create_table(
        "agent_executions",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("organization_id", uuid_type, sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("deal_id", uuid_type, sa.ForeignKey("deals.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("user_id", uuid_type, sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("orchestration_mode", sa.String(50), nullable=False, server_default="FULL_DEAL_DECISION"),
        sa.Column("query", sa.Text(), nullable=True),
        sa.Column("status", sa.String(30), nullable=False, server_default="COMPLETED"),
        sa.Column("recommendation", sa.String(50), nullable=True),
        sa.Column("decision_score", sa.Float(), nullable=True),
        sa.Column("confidence", sa.String(30), nullable=False, server_default="HIGH"),
        sa.Column("confidence_score", sa.Float(), nullable=False, server_default="0.90"),
        sa.Column("human_review_required", sa.Boolean(), nullable=False, server_default=sa.text("0" if not is_postgres else "false")),
        sa.Column("duration_ms", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("selected_agents", json_type, nullable=False, server_default=sa.text("'[]'")),
        sa.Column("synthesis_payload", json_type, nullable=False, server_default=sa.text("'{}'")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )

    op.create_index(
        "ix_agent_exec_lookup",
        "agent_executions",
        ["organization_id", "deal_id", "created_at"],
    )

    # 2. Create agent_assessments table
    op.create_table(
        "agent_assessments",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("organization_id", uuid_type, sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("execution_id", uuid_type, sa.ForeignKey("agent_executions.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("deal_id", uuid_type, sa.ForeignKey("deals.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("agent_id", sa.String(100), nullable=False, index=True),
        sa.Column("domain", sa.String(50), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="SUCCESS"),
        sa.Column("confidence", sa.String(30), nullable=False, server_default="HIGH"),
        sa.Column("confidence_score", sa.Float(), nullable=False, server_default="0.90"),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("findings_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("citations_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("tools_invoked", json_type, nullable=False, server_default=sa.text("'[]'")),
        sa.Column("assessment_payload", json_type, nullable=False, server_default=sa.text("'{}'")),
        sa.Column("execution_time_ms", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )

    op.create_index(
        "ix_agent_assess_lookup",
        "agent_assessments",
        ["organization_id", "deal_id", "agent_id"],
    )

    # 3. Create ml_models table
    op.create_table(
        "ml_models",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("organization_id", uuid_type, sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("model_key", sa.String(100), nullable=False, unique=True, index=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("version", sa.String(30), nullable=False, server_default="1.0.0"),
        sa.Column("task_type", sa.String(50), nullable=False, index=True),
        sa.Column("framework", sa.String(50), nullable=False, server_default="scikit-learn"),
        sa.Column("training_dataset_id", sa.String(100), nullable=True),
        sa.Column("metrics_json", json_type, nullable=False, server_default=sa.text("'{}'")),
        sa.Column("hyperparameters_json", json_type, nullable=False, server_default=sa.text("'{}'")),
        sa.Column("status", sa.String(30), nullable=False, server_default="REGISTERED"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )

    op.create_index(
        "ix_ml_models_org_task",
        "ml_models",
        ["organization_id", "task_type"],
    )

    # 4. Create ml_predictions table
    op.create_table(
        "ml_predictions",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("organization_id", uuid_type, sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("model_id", sa.String(100), nullable=False, index=True),
        sa.Column("model_version", sa.String(30), nullable=False, server_default="1.0.0"),
        sa.Column("deal_id", uuid_type, sa.ForeignKey("deals.id", ondelete="CASCADE"), nullable=True, index=True),
        sa.Column("task_type", sa.String(50), nullable=False, index=True),
        sa.Column("predicted_value_json", json_type, nullable=False),
        sa.Column("prediction_confidence", sa.Float(), nullable=False, server_default="0.90"),
        sa.Column("features_json", json_type, nullable=False, server_default=sa.text("'{}'")),
        sa.Column("explanation_json", json_type, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )

    op.create_index(
        "ix_ml_preds_lookup",
        "ml_predictions",
        ["organization_id", "deal_id", "task_type"],
    )


def downgrade() -> None:
    op.drop_table("ml_predictions")
    op.drop_table("ml_models")
    op.drop_table("agent_assessments")
    op.drop_table("agent_executions")
