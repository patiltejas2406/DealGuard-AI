"""Google GenAI Gemini Embedding Provider (1536 Dimensions)."""

import os
from typing import List, Optional
import httpx
from app.core.config import settings
from app.core.exceptions import AIProcessingException
from app.domains.ai.embeddings.base import BaseEmbeddingProvider


class GeminiEmbeddingProvider(BaseEmbeddingProvider):
    """Generates 1536-dimensional semantic vector embeddings via Google GenAI API."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "text-embedding-004",
        dimension: int = 1536,
    ) -> None:
        self._api_key = api_key or os.getenv("GEMINI_API_KEY") or getattr(settings, "GEMINI_API_KEY", "")
        self._model_name = model_name
        self._dimension = dimension

    @property
    def dimension(self) -> int:
        return self._dimension

    @property
    def model_name(self) -> str:
        return self._model_name

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of document chunks using Gemini API."""
        if not self._api_key or self._api_key.startswith("mock-") or self._api_key == "change-in-production":
            raise AIProcessingException(
                "Gemini API key is not configured. Please set GEMINI_API_KEY in environment variables."
            )

        if not texts:
            return []

        endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{self._model_name}:batchEmbedContents?key={self._api_key}"

        requests_payload = [
            {
                "model": f"models/{self._model_name}",
                "content": {"parts": [{"text": text}]},
                "outputDimensionality": self._dimension,
            }
            for text in texts
        ]

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(endpoint, json={"requests": requests_payload})
                if response.status_code != 200:
                    raise AIProcessingException(
                        f"Gemini embedding API error ({response.status_code}): {response.text}"
                    )
                data = response.json()
                embeddings = [item["values"] for item in data.get("embeddings", [])]
                return embeddings
            except httpx.RequestError as exc:
                raise AIProcessingException(f"Network error connecting to Gemini API: {str(exc)}")

    async def embed_query(self, query: str) -> List[float]:
        """Generate embedding vector for a single search query."""
        results = await self.embed_texts([query])
        if not results:
            raise AIProcessingException("Failed to generate embedding for query.")
        return results[0]
