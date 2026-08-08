"""Project ORM Model."""

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.db.base import Base

if TYPE_CHECKING:
    from src.db.models.batch_job import BatchJob
    from src.db.models.crawl_job import CrawlJob
    from src.db.models.user import User


class Project(Base):
    """Project entity organizing crawls, batch jobs, and datasets per user workspace."""

    __tablename__ = "projects"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="projects")
    crawl_jobs: Mapped[List["CrawlJob"]] = relationship(
        "CrawlJob",
        back_populates="project",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    batch_jobs: Mapped[List["BatchJob"]] = relationship(
        "BatchJob",
        back_populates="project",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
