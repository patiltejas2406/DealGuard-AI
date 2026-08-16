"""Database Connection, Async Session Factory and Health Check Utilities."""

from typing import AsyncGenerator
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger("dealguard.database")


class Base(DeclarativeBase):
    """SQLAlchemy 2.0 Declarative Base with common table helpers."""
    pass


# Global async engine instance
_async_engine: AsyncEngine | None = None
_async_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_engine() -> AsyncEngine:
    """Initialize or return the cached async database engine."""
    global _async_engine
    if _async_engine is None:
        db_url = settings.get_database_url()
        # Fallback configuration for SQLite in testing if specified
        connect_args = {}
        if "sqlite" in db_url:
            connect_args["check_same_thread"] = False

        _async_engine = create_async_engine(
            db_url,
            echo=settings.DEBUG and settings.ENVIRONMENT == "development",
            future=True,
            pool_pre_ping=True,
            connect_args=connect_args,
        )
    return _async_engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Initialize or return the cached session factory."""
    global _async_session_factory
    if _async_session_factory is None:
        engine = get_engine()
        _async_session_factory = async_sessionmaker(
            bind=engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )
    return _async_session_factory


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency yielding an async database session."""
    session_factory = get_session_factory()
    async with session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def check_database_health() -> bool:
    """Execute a simple SELECT 1 query to verify database connectivity."""
    try:
        engine = get_engine()
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            return result.scalar() == 1
    except Exception as exc:
        logger.warning(f"Database health check failed: {exc}")
        return False
