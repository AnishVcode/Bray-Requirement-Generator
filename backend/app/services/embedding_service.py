"""
Azure OpenAI embedding service.
Generates text embeddings using text-embedding-3-large for vector search.
"""

import hashlib
import numpy as np
from typing import Optional

from app.config import get_settings
from app.utils.logger import get_logger
from app.utils.retry import retry_async

logger = get_logger("embeddings")


class EmbeddingService:
    """Generate embeddings using Azure OpenAI."""

    def __init__(self):
        self.settings = get_settings()
        self._client = None
        self._cache: dict[str, list[float]] = {}

    @property
    def client(self):
        if self._client is None:
            from openai import AzureOpenAI
            self._client = AzureOpenAI(
                api_key=self.settings.AZURE_OPENAI_API_KEY,
                api_version=self.settings.AZURE_OPENAI_API_VERSION,
                azure_endpoint=self.settings.AZURE_OPENAI_ENDPOINT,
            )
        return self._client

    def _cache_key(self, text: str) -> str:
        return hashlib.md5(text.encode()).hexdigest()

    async def generate_embedding(self, text: str) -> list[float]:
        cache_key = self._cache_key(text)
        if cache_key in self._cache:
            return self._cache[cache_key]

        async def _embed():
            response = self.client.embeddings.create(
                input=text[:8191],
                model=self.settings.AZURE_OPENAI_EMBEDDING_DEPLOYMENT,
                dimensions=self.settings.EMBEDDING_DIMENSIONS,
            )
            return response.data[0].embedding

        embedding = await retry_async(_embed, max_retries=self.settings.MAX_RETRIES, operation_name="Generate embedding")
        self._cache[cache_key] = embedding
        return embedding

    async def generate_embeddings_batch(self, texts: list[str], batch_size: Optional[int] = None) -> list[list[float]]:
        batch_size = batch_size or self.settings.EMBEDDING_BATCH_SIZE
        all_embeddings = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            cached, uncached_indices, uncached_texts = [], [], []
            for j, text in enumerate(batch):
                ck = self._cache_key(text)
                if ck in self._cache:
                    cached.append((j, self._cache[ck]))
                else:
                    uncached_indices.append(j)
                    uncached_texts.append(text[:8191])

            if uncached_texts:
                async def _embed_batch():
                    response = self.client.embeddings.create(
                        input=uncached_texts,
                        model=self.settings.AZURE_OPENAI_EMBEDDING_DEPLOYMENT,
                        dimensions=self.settings.EMBEDDING_DIMENSIONS,
                    )
                    return [d.embedding for d in response.data]

                new_embeddings = await retry_async(_embed_batch, max_retries=self.settings.MAX_RETRIES, operation_name=f"Batch embedding ({len(uncached_texts)} texts)")
                for text, emb in zip(uncached_texts, new_embeddings):
                    self._cache[self._cache_key(text)] = emb
                result = [None] * len(batch)
                for j, emb in cached:
                    result[j] = emb
                for idx, j in enumerate(uncached_indices):
                    result[j] = new_embeddings[idx]
                all_embeddings.extend(result)
            else:
                all_embeddings.extend([emb for _, emb in sorted(cached)])
        return all_embeddings


class MockEmbeddingService(EmbeddingService):
    """Mock embedding service using random vectors for local development."""

    async def generate_embedding(self, text: str) -> list[float]:
        cache_key = self._cache_key(text)
        if cache_key in self._cache:
            return self._cache[cache_key]
        seed = int(hashlib.md5(text.encode()).hexdigest(), 16) % (2**32)
        rng = np.random.RandomState(seed)
        embedding = rng.randn(self.settings.EMBEDDING_DIMENSIONS).tolist()
        norm = sum(x**2 for x in embedding) ** 0.5
        embedding = [x / norm for x in embedding]
        self._cache[cache_key] = embedding
        return embedding

    async def generate_embeddings_batch(self, texts: list[str], batch_size: Optional[int] = None) -> list[list[float]]:
        return [await self.generate_embedding(t) for t in texts]


def get_embedding_service() -> EmbeddingService:
    settings = get_settings()
    if settings.MOCK_MODE:
        return MockEmbeddingService()
    return EmbeddingService()
