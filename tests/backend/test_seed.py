"""Tests for Database Seeder and Idempotency."""

import os
import pytest
from app.core import database
from backend.scripts.seed import seed_database


@pytest.mark.asyncio
async def test_seed_database_idempotency(tmp_path):
    """Verify that seed_database executes cleanly and is safely idempotent on subsequent runs."""
    test_db = str(tmp_path / "test_seed_suite.db")
    orig_url = os.environ.get("DATABASE_URL")
    
    try:
        os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{test_db}"
        database._async_engine = None
        database._async_session_factory = None
        
        # First execution: seeds database
        await seed_database()
        
        # Second execution: idempotency guard triggers without exception
        await seed_database()
    finally:
        if orig_url:
            os.environ["DATABASE_URL"] = orig_url
        else:
            os.environ.pop("DATABASE_URL", None)
        database._async_engine = None
        database._async_session_factory = None
