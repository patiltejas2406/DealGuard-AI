"""Pytest Fixtures and Test Harness for DealGuard AI Backend."""

import os
import pytest
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Set testing environment variables before importing app
os.environ["ENVIRONMENT"] = "test"
os.environ["DEBUG"] = "false"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["DATABASE_URL_SYNC"] = "sqlite:///:memory:"

from app.core.config import settings
from app.core.database import Base, get_db
from app.main import app

import pytest_asyncio

# Test In-Memory SQLite Async Engine
test_async_engine = create_async_engine(
    "sqlite+aiosqlite:///:memory:",
    connect_args={"check_same_thread": False},
    future=True,
)

TestSessionLocal = async_sessionmaker(
    bind=test_async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    """Test dependency override for database session."""
    async with TestSessionLocal() as session:
        yield session


app.dependency_overrides[get_db] = override_get_db


@pytest_asyncio.fixture
async def prepare_database():
    """Create all test tables before each test and drop after."""
    async with test_async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session(prepare_database) -> AsyncGenerator[AsyncSession, None]:
    """Yield an active test database session."""
    async with TestSessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def async_client(prepare_database) -> AsyncGenerator[AsyncClient, None]:
    """Asynchronous HTTP test client fixture with initialized database."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client


