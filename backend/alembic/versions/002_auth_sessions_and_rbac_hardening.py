"""Add Auth Sessions and RBAC Hardening.

Revision ID: 002_auth_sessions_and_rbac_hardening
Revises: 001_initial_schema
Create Date: 2026-08-16 16:15:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "002_auth_sessions_and_rbac_hardening"
down_revision: Union[str, None] = "001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    is_postgres = bind.dialect.name == "postgresql"

    # Create auth_sessions table
    op.create_table(
        "auth_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True) if is_postgres else sa.String(36), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True) if is_postgres else sa.String(36), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True) if is_postgres else sa.String(36), nullable=False),
        sa.Column("refresh_token_hash", sa.String(64), nullable=False),
        sa.Column("token_family_id", postgresql.UUID(as_uuid=True) if is_postgres else sa.String(36), nullable=False),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.String(500), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("refresh_token_hash", name="uq_auth_sessions_refresh_hash"),
    )
    op.create_index("ix_auth_sessions_family", "auth_sessions", ["token_family_id"])
    op.create_index("ix_auth_sessions_user_org", "auth_sessions", ["user_id", "organization_id"])
    op.create_index("ix_auth_sessions_refresh_hash", "auth_sessions", ["refresh_token_hash"])


def downgrade() -> None:
    op.drop_table("auth_sessions")
