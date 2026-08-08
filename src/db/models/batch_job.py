import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import DateTime, Enum, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base
from src.db.models.crawl_job import CrawlStatus

if TYPE_CHECKING:
    from src.db.models.crawl_job import CrawlJob
    from src.db.models.project import Project


class BatchJob(Base):
    """BatchJob entity managing parallel/sequential website crawl jobs."""

    __tablename__ = "batch_jobs"

    project_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
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
    project: Mapped[Optional["Project"]] = relationship(
        "Project", back_populates="batch_jobs"
    )
    jobs: Mapped[List["CrawlJob"]] = relationship(
        "CrawlJob",
        back_populates="batch",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
