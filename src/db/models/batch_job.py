"""BatchJob ORM Model.

Represents a multi-website batch crawling request containing individual crawl jobs.
"""

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import DateTime, Enum, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base
from src.db.models.crawl_job import CrawlStatus

if TYPE_CHECKING:
    from src.db.models.crawl_job import CrawlJob


class BatchJob(Base):
    """BatchJob entity managing parallel/sequential website crawl jobs."""

    __tablename__ = "batch_jobs"

    status: Mapped[CrawlStatus] = mapped_column(
        Enum(CrawlStatus, native_enum=False),
        default=CrawlStatus.PENDING,
        nullable=False,
        index=True,
    )
    total_urls: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    finished_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    jobs: Mapped[List["CrawlJob"]] = relationship(
        "CrawlJob",
        back_populates="batch",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
