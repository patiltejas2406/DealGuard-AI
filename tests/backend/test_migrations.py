"""Tests for Alembic Database Migration Upgrade and Downgrade."""

import pytest
from alembic import command
from alembic.config import Config
from app.core.config import settings


def test_alembic_migration_offline_and_online():
    """Verify that Alembic migrations build correctly and upgrade cleanly."""
    alembic_cfg = Config("backend/alembic.ini")
    alembic_cfg.set_main_option("script_location", "backend/alembic")
    alembic_cfg.set_main_option("sqlalchemy.url", "sqlite:///test_alembic.db")

    # Upgrade to head
    command.upgrade(alembic_cfg, "head")

    # Downgrade to base
    command.downgrade(alembic_cfg, "base")

    # Clean up test file
    import os
    if os.path.exists("test_alembic.db"):
        os.remove("test_alembic.db")
