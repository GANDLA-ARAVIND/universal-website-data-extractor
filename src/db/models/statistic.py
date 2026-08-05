"""CrawlStatistic ORM Model.

Stores aggregated execution metrics and performance statistics for a finished or running crawl job.
"""

import uuid
from typing import TYPE_CHECKING
from sqlalchemy import Float, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.db.base import Base

if TYPE_CHECKING:
    from src.db.models.crawl_job import CrawlJob


class CrawlStatistic(Base):
    """CrawlStatistic entity holding aggregated job metrics."""

    __tablename__ = "crawl_statistics"

    job_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("crawl_jobs.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    pages_crawled: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failed_pages: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_images: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_links: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_duration_sec: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    job: Mapped["CrawlJob"] = relationship("CrawlJob", back_populates="statistic")
