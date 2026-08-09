"""DocumentChunk Repository Data Access Object.

Provides persistence, retrieval, and vector similarity search over DocumentChunk records.
"""

import math
import uuid
from typing import List, Optional, Tuple
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.models.chunk import DocumentChunk


class ChunkRepository:
    """Repository handling CRUD operations and vector similarity search over DocumentChunk records."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def save_chunks(self, chunks: List[DocumentChunk]) -> List[DocumentChunk]:
        """Saves a batch of DocumentChunk instances."""
        self.session.add_all(chunks)
        await self.session.commit()
        return chunks

    async def get_chunks_by_job_id(self, job_id: uuid.UUID) -> List[DocumentChunk]:
        """Retrieves all document chunks for a crawl job."""
        stmt = select(DocumentChunk).where(DocumentChunk.job_id == job_id).order_by(DocumentChunk.chunk_index)
        res = await self.session.execute(stmt)
        return list(res.scalars().all())

    async def delete_chunks_by_job_id(self, job_id: uuid.UUID) -> int:
        """Deletes existing document chunks for a crawl job."""
        stmt = delete(DocumentChunk).where(DocumentChunk.job_id == job_id)
        res = await self.session.execute(stmt)
        await self.session.commit()
        return res.rowcount

    async def search_similar_chunks(
        self,
        job_id: uuid.UUID,
        query_embedding: List[float],
        top_k: int = 5,
    ) -> List[Tuple[DocumentChunk, float]]:
        """Performs vector similarity search returning top-k matching chunks sorted by cosine similarity score."""
        chunks = await self.get_chunks_by_job_id(job_id)
        if not chunks or not query_embedding:
            return []

        scored_chunks: List[Tuple[DocumentChunk, float]] = []

        for chunk in chunks:
            if not chunk.embedding:
                continue
            sim = self._cosine_similarity(query_embedding, chunk.embedding)
            scored_chunks.append((chunk, sim))

        # Sort by similarity score descending
        scored_chunks.sort(key=lambda x: x[1], reverse=True)
        return scored_chunks[:top_k]

    @staticmethod
    def _cosine_similarity(v1: List[float], v2: List[float]) -> float:
        """Computes cosine similarity score between two float vectors."""
        if len(v1) != len(v2) or not v1:
            return 0.0
        dot_prod = sum(a * b for a, b in zip(v1, v2))
        norm_v1 = math.sqrt(sum(a * a for a in v1))
        norm_v2 = math.sqrt(sum(b * b for b in v2))
        if norm_v1 == 0 or norm_v2 == 0:
            return 0.0
        return dot_prod / (norm_v1 * norm_v2)
