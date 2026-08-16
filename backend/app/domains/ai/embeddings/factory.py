"""Embedding Provider Factory with Environment-Aware Selection."""

import os
from typing import Optional
from app.core.config import settings
from app.core.logging import get_logger
from app.domains.ai.embeddings.base import BaseEmbeddingProvider
from app.domains.ai.embeddings.gemini import GeminiEmbeddingProvider
from app.domains.ai.embeddings.mock_provider import MockEmbeddingProvider

logger = get_logger("embeddings.factory")

_global_provider: Optional[BaseEmbeddingProvider] = None


def get_embedding_provider(force_mock: bool = False) -> BaseEmbeddingProvider:
    """
    Get configured embedding provider.
    Uses GeminiEmbeddingProvider when GEMINI_API_KEY is present and not force_mock,
    otherwise falls back to deterministic MockEmbeddingProvider for testing.
    """
    global _global_provider
    if _global_provider is not None and not force_mock:
        return _global_provider

    gemini_key = os.getenv("GEMINI_API_KEY") or getattr(settings, "GEMINI_API_KEY", "")

    if force_mock or not gemini_key or gemini_key.startswith("mock-") or gemini_key == "change-in-production":
        provider = MockEmbeddingProvider()
    else:
        provider = GeminiEmbeddingProvider(api_key=gemini_key)

    if not force_mock:
        _global_provider = provider

    return provider


def set_global_embedding_provider(provider: Optional[BaseEmbeddingProvider]) -> None:
    """Set or reset global embedding provider (useful for test fixtures)."""
    global _global_provider
    _global_provider = provider
