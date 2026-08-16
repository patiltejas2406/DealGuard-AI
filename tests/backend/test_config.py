"""Tests for Settings & Configuration Management."""

from app.core.config import Settings


def test_settings_defaults():
    """Verify default configuration values."""
    s = Settings()
    assert s.PROJECT_NAME == "DealGuard AI"
    assert s.VERSION == "1.0.0"
    assert s.API_V1_STR == "/api/v1"
    assert s.EMBEDDING_DIMENSION == 1536
    assert s.EMBEDDING_PROVIDER == "gemini"


def test_cors_origins_parsing():
    """Verify CORS origins parser handles string lists and JSON strings."""
    s1 = Settings(ALLOWED_ORIGINS=["http://localhost:3000"])
    assert s1.ALLOWED_ORIGINS == ["http://localhost:3000"]

    s2 = Settings(ALLOWED_ORIGINS='["http://alpha.com", "http://beta.com"]')
    assert "http://alpha.com" in s2.ALLOWED_ORIGINS


def test_connection_url_generators():
    """Verify database and Celery connection string builders."""
    s = Settings(
        DATABASE_URL=None,
        DATABASE_URL_SYNC=None,
        CELERY_BROKER_URL=None,
        CELERY_RESULT_BACKEND=None,
        POSTGRES_USER="testuser",
        POSTGRES_PASSWORD="testpassword",
        POSTGRES_SERVER="db.example.com",
        POSTGRES_PORT=5432,
        POSTGRES_DB="testdb",
        REDIS_HOST="redis.example.com",
        REDIS_PORT=6379,
    )
    assert "postgresql+asyncpg://testuser:testpassword@db.example.com:5432/testdb" in s.get_database_url()
    assert "redis://redis.example.com:6379/0" in s.get_celery_broker_url()

