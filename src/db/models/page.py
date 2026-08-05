"""ExtractedPage ORM Model.

Stores scraped web page metadata, structural elements (headings, paragraphs, lists, tables),
HTTP status code, and performance metrics.
"""

import uuid
from typing import TYPE_CHECKING, Any, Dict, List, Optional
from sqlalchemy import ForeignKey, Integer, String, Text, Float, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.db.base import Base

if TYPE_CHECKING:
    from src.db.models.crawl_job import CrawlJob
    from src.db.models.link import PageLink
    from src.db.models.image import PageImage


class ExtractedPage(Base):
    """ExtractedPage database entity storing page-level extracted data."""

    __tablename__ = "extracted_pages"

    job_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("crawl_jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    url: Mapped[str] = mapped_column(String(2048), nullable=False)
    normalized_url: Mapped[str] = mapped_column(String(2048), nullable=False, index=True)
    status_code: Mapped[int] = mapped_column(Integer, nullable=False, default=200)
    depth: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    title: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    meta_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    headings: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    paragraphs: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    lists: Mapped[List[Any]] = mapped_column(JSON, default=list, nullable=False)
    tables: Mapped[List[Any]] = mapped_column(JSON, default=list, nullable=False)

    response_time_ms: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    # Relationships
    job: Mapped["CrawlJob"] = relationship("CrawlJob", back_populates="pages")
    links: Mapped[List["PageLink"]] = relationship(
        "PageLink",
        back_populates="page",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    images: Mapped[List["PageImage"]] = relationship(
        "PageImage",
        back_populates="page",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
