"""Typed Application Configuration using Pydantic Settings."""

import json
from typing import Any, List, Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    # General App Settings
    PROJECT_NAME: str = "DealGuard AI"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    # Security & Auth
    APP_SECRET_KEY: str = "dev-secret-key-change-in-production-0123456789abcdef"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    JWT_ALGORITHM: str = "HS256"

    # Database Settings (PostgreSQL 16 + pgvector)
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "dealguard"
    POSTGRES_PASSWORD: str = "dealguard_secret"
    POSTGRES_DB: str = "dealguard_ai"
    DATABASE_URL: Optional[str] = None
    DATABASE_URL_SYNC: Optional[str] = None

    # Redis & Background Jobs
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: Optional[str] = None
    REDIS_URL: Optional[str] = None
    CELERY_BROKER_URL: Optional[str] = None
    CELERY_RESULT_BACKEND: Optional[str] = None

    # Object Storage (MinIO / S3)
    STORAGE_PROVIDER: str = "minio"
    STORAGE_ENDPOINT: str = "http://localhost:9000"
    STORAGE_ACCESS_KEY: str = "minioadmin"
    STORAGE_SECRET_KEY: str = "minioadmin"
    STORAGE_BUCKET_DOCUMENTS: str = "dealguard-documents"
    STORAGE_REGION: str = "us-east-1"
    STORAGE_SECURE: bool = False

    # AI & Embedding Providers
    EMBEDDING_PROVIDER: str = "gemini"
    EMBEDDING_MODEL: str = "models/text-embedding-004"
    EMBEDDING_DIMENSION: int = 1536
    GEMINI_API_KEY: Optional[str] = None

    # CORS Configuration
    FRONTEND_URL: str = "http://localhost:3000"
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Any) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, str) and v.startswith("["):
            try:
                return json.loads(v)
            except Exception:
                return ["http://localhost:3000"]
        elif isinstance(v, list):
            return v
        return ["http://localhost:3000"]

    def get_database_url(self) -> str:
        """Return async database connection URL, normalizing postgres/postgresql schemes to postgresql+asyncpg."""
        if self.DATABASE_URL:
            raw_url = self.DATABASE_URL
            if raw_url.startswith("sqlite"):
                return raw_url
            if raw_url.startswith("postgres://"):
                return raw_url.replace("postgres://", "postgresql+asyncpg://", 1)
            if raw_url.startswith("postgresql://"):
                return raw_url.replace("postgresql://", "postgresql+asyncpg://", 1)
            return raw_url
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    def get_database_url_sync(self) -> str:
        """Return sync database connection URL for Alembic migrations and synchronous drivers."""
        if self.DATABASE_URL_SYNC:
            raw_url = self.DATABASE_URL_SYNC
            if raw_url.startswith("postgres://"):
                return raw_url.replace("postgres://", "postgresql://", 1)
            if raw_url.startswith("postgresql+asyncpg://"):
                return raw_url.replace("postgresql+asyncpg://", "postgresql://", 1)
            return raw_url
        if self.DATABASE_URL:
            raw_url = self.DATABASE_URL
            if raw_url.startswith("sqlite"):
                return raw_url.replace("sqlite+aiosqlite://", "sqlite://", 1)
            if raw_url.startswith("postgres://"):
                return raw_url.replace("postgres://", "postgresql://", 1)
            if raw_url.startswith("postgresql+asyncpg://"):
                return raw_url.replace("postgresql+asyncpg://", "postgresql://", 1)
            return raw_url
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    def get_celery_broker_url(self) -> str:
        """Return Celery broker connection string, prioritizing CELERY_BROKER_URL or REDIS_URL."""
        if self.CELERY_BROKER_URL:
            return self.CELERY_BROKER_URL
        if self.REDIS_URL:
            url = self.REDIS_URL.rstrip("/")
            parts = url.split("://", 1)
            if len(parts) == 2 and "/" not in parts[1]:
                return f"{url}/0"
            return url
        pwd = f":{self.REDIS_PASSWORD}@" if self.REDIS_PASSWORD else ""
        return f"redis://{pwd}{self.REDIS_HOST}:{self.REDIS_PORT}/0"

    def get_celery_result_backend(self) -> str:
        """Return Celery result backend connection string, prioritizing CELERY_RESULT_BACKEND or REDIS_URL."""
        if self.CELERY_RESULT_BACKEND:
            return self.CELERY_RESULT_BACKEND
        if self.REDIS_URL:
            url = self.REDIS_URL.rstrip("/")
            parts = url.split("://", 1)
            if len(parts) == 2 and "/" not in parts[1]:
                return f"{url}/1"
            return url
        pwd = f":{self.REDIS_PASSWORD}@" if self.REDIS_PASSWORD else ""
        return f"redis://{pwd}{self.REDIS_HOST}:{self.REDIS_PORT}/1"


settings = Settings()
