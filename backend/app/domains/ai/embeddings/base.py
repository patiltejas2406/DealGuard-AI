"""Abstract Base Embedding Provider Interface for Vector Embeddings."""

from abc import ABC, abstractmethod
from typing import List


class BaseEmbeddingProvider(ABC):
    """Abstract interface for text vectorization and semantic embeddings."""

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Return the vector dimensionality (e.g. 1536)."""
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Return the model identifier string."""
        pass

    @abstractmethod
    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate embedding vectors for a batch of text passages."""
        pass

    @abstractmethod
    async def embed_query(self, query: str) -> List[float]:
        """Generate an embedding vector for a search query."""
        pass
