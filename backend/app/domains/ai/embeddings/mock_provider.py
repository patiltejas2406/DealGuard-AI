"""Deterministic Mock Embedding Provider for Offline Development and Automated Testing."""

import hashlib
import math
from typing import List
from app.domains.ai.embeddings.base import BaseEmbeddingProvider


class MockEmbeddingProvider(BaseEmbeddingProvider):
    """
    Generates deterministic, normalized 1536-dimensional vectors for testing
    without external network calls or API dependencies.
    """

    def __init__(self, model_name: str = "mock-gemini-embedding-2", dimension: int = 1536) -> None:
        self._model_name = model_name
        self._dimension = dimension

    @property
    def dimension(self) -> int:
        return self._dimension

    @property
    def model_name(self) -> str:
        return self._model_name

    def _generate_vector(self, text: str) -> List[float]:
        """Compute deterministic unit-normalized pseudo-vector from text sha256."""
        seed = int(hashlib.sha256(text.encode("utf-8")).hexdigest()[:12], 16)
        vec = []
        for i in range(self._dimension):
            # Deterministic pseudo-random sinusoidal distribution
            val = math.sin(seed + i * 0.73) * math.cos(i * 0.17)
            vec.append(val)

        # L2 normalize
        norm = math.sqrt(sum(x * x for x in vec)) or 1.0
        return [round(x / norm, 6) for x in vec]

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate deterministic embeddings for text list."""
        return [self._generate_vector(t) for t in texts]

    async def embed_query(self, query: str) -> List[float]:
        """Generate deterministic embedding for search query."""
        return self._generate_vector(query)
