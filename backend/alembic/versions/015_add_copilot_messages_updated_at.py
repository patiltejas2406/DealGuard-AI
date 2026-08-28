"""Add updated_at column to copilot_messages table.

Revision ID: 015_add_copilot_messages_updated_at
Revises: 014_copilot_conversations_and_messages
Create Date: 2026-08-28 11:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "015_add_copilot_messages_updated_at"
down_revision: Union[str, None] = "014_copilot_conversations_and_messages"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Check if column already exists before adding (defensive for idempotency)
    bind = op.get_bind()
    insp = sa.inspect(bind)
    cols = [col["name"] for col in insp.get_columns("copilot_messages")]
    if "updated_at" not in cols:
        op.add_column(
            "copilot_messages",
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("CURRENT_TIMESTAMP"),
                nullable=False,
            ),
        )


def downgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    cols = [col["name"] for col in insp.get_columns("copilot_messages")]
    if "updated_at" in cols:
        op.drop_column("copilot_messages", "updated_at")
