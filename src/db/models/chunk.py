"""DocumentChunk ORM Entity for RAG Vector Search."""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.db.base import Base


class DocumentChunk(Base):
    """Represents a semantic text chunk extracted from a web page for vector similarity search."""

    __tablename__ = "document_chunks"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4
    )

    job_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("crawl_jobs.id", ondelete="CASCADE"), nullable=False, index=True
    )

    batch_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("batch_jobs.id", ondelete="CASCADE"), nullable=True, index=True
    )

    project_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=True, index=True
    )

    page_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("extracted_pages.id", ondelete="CASCADE"), nullable=False, index=True
    )

    url: Mapped[str] = mapped_column(String(2048), nullable=False)
    page_title: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    heading_path: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)

    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    char_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Embedding array stored as JSON array of floats for cross-database portability
    embedding: Mapped[Optional[List[float]]] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
