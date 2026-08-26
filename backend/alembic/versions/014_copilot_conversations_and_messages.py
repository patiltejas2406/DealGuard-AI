"""Copilot Conversations and Grounded Multi-Turn Messages Tables.

Revision ID: 014_copilot_conversations_and_messages
Revises: 013_technology_operational_intelligence_engine
Create Date: 2026-08-26 18:40:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "014_copilot_conversations_and_messages"
down_revision: Union[str, None] = "013_technology_operational_intelligence_engine"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    is_postgres = bind.dialect.name == "postgresql"

    json_type = postgresql.JSONB(astext_type=sa.Text()) if is_postgres else sa.JSON()
    uuid_type = postgresql.UUID(as_uuid=True) if is_postgres else sa.String(36)

    # 1. Create copilot_conversations table
    op.create_table(
        "copilot_conversations",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("organization_id", uuid_type, sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("deal_id", uuid_type, sa.ForeignKey("deals.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("user_id", uuid_type, sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("title", sa.String(255), nullable=False, server_default="New Diligence Chat"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )

    op.create_index(
        "ix_copilot_conv_org_deal",
        "copilot_conversations",
        ["organization_id", "deal_id"],
    )

    # 2. Create copilot_messages table
    op.create_table(
        "copilot_messages",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("organization_id", uuid_type, sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("deal_id", uuid_type, sa.ForeignKey("deals.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("conversation_id", uuid_type, sa.ForeignKey("copilot_conversations.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("role", sa.String(20), nullable=False),  # user, assistant, system
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("citations", json_type, nullable=False, server_default=sa.text("'[]'")),
        sa.Column("confidence", sa.String(30), nullable=False, server_default="HIGH"),  # HIGH, MEDIUM, LOW, INSUFFICIENT_EVIDENCE
        sa.Column("retrieved_domains", json_type, nullable=False, server_default=sa.text("'[]'")),
        sa.Column("metadata_payload", json_type, nullable=False, server_default=sa.text("'{}'")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )

    op.create_index(
        "ix_copilot_msg_conv_created",
        "copilot_messages",
        ["conversation_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_copilot_msg_conv_created", table_name="copilot_messages")
    op.drop_table("copilot_messages")

    op.drop_index("ix_copilot_conv_org_deal", table_name="copilot_conversations")
    op.drop_table("copilot_conversations")
