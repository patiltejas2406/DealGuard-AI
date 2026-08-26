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


def test_alembic_percent_encoded_url_handling():
    """Verify that Alembic config properly handles database URLs with URL-encoded special characters (e.g., %40)."""
    alembic_cfg = Config("backend/alembic.ini")
    test_raw_url = "postgresql://postgres:%40Tejasdealg@db.example.com:5432/postgres"
    alembic_cfg.set_main_option(
        "sqlalchemy.url",
        test_raw_url.replace("%", "%%"),
    )
    # Ensure ConfigParser successfully unescapes %% to %
    assert alembic_cfg.get_main_option("sqlalchemy.url") == test_raw_url
    section = alembic_cfg.get_section(alembic_cfg.config_ini_section, {})
    assert section.get("sqlalchemy.url") == test_raw_url
