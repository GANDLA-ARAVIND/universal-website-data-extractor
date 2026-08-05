"""CrawlJob ORM Model.

Represents a web crawling task lifecycle, configuration parameters, and execution state.
"""

import enum
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import DateTime, Enum, Integer, String, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.db.base import Base

if TYPE_CHECKING:
    from src.db.models.page import ExtractedPage
    from src.db.models.statistic import CrawlStatistic


class CrawlStatus(str, enum.Enum):
    """Lifecycle status of a crawl job."""

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class CrawlJob(Base):
    """CrawlJob database entity tracking seed target and job parameters."""

    __tablename__ = "crawl_jobs"

    seed_url: Mapped[str] = mapped_column(String(2048), nullable=False, index=True)
    status: Mapped[CrawlStatus] = mapped_column(
        Enum(CrawlStatus, native_enum=False),
        default=CrawlStatus.PENDING,
        nullable=False,
        index=True,
    )
    max_depth: Mapped[int] = mapped_column(Integer, default=2, nullable=False)
    max_pages: Mapped[int] = mapped_column(Integer, default=50, nullable=False)
    render_js: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    finished_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    pages: Mapped[List["ExtractedPage"]] = relationship(
        "ExtractedPage",
        back_populates="job",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    statistic: Mapped[Optional["CrawlStatistic"]] = relationship(
        "CrawlStatistic",
        back_populates="job",
        uselist=False,
        cascade="all, delete-orphan",
        lazy="selectin",
    )
