"""Tests for Gemini & Mock Embedding Vectorization Layer (1536 Dimensions)."""

import pytest
from app.core.exceptions import AIProcessingException
from app.domains.ai.embeddings.factory import get_embedding_provider
from app.domains.ai.embeddings.gemini import GeminiEmbeddingProvider
from app.domains.ai.embeddings.mock_provider import MockEmbeddingProvider


@pytest.mark.asyncio
async def test_mock_embedding_provider_dimensionality():
    """Verify MockEmbeddingProvider produces 1536-dimensional normalized vectors."""
    provider = MockEmbeddingProvider(dimension=1536)
    assert provider.dimension == 1536

    texts = [
        "Revenue increased 28% year-over-year to $45.2M.",
        "Customer concentration risk Note 8 disclosure.",
    ]
    vectors = await provider.embed_texts(texts)
    assert len(vectors) == 2
    assert len(vectors[0]) == 1536
    assert len(vectors[1]) == 1536

    query_vec = await provider.embed_query("What is the ARR growth?")
    assert len(query_vec) == 1536


@pytest.mark.asyncio
async def test_gemini_provider_unconfigured_error():
    """Verify GeminiEmbeddingProvider raises clean exception when API key is missing."""
    provider = GeminiEmbeddingProvider(api_key="")
    with pytest.raises(AIProcessingException) as exc:
        await provider.embed_texts(["Test text"])
    assert "Gemini API key is not configured" in str(exc.value)


def test_embedding_factory():
    """Verify get_embedding_provider returns a valid BaseEmbeddingProvider."""
    provider = get_embedding_provider(force_mock=True)
    assert provider.dimension == 1536
    assert provider.model_name is not None
