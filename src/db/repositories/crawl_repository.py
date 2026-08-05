"""CrawlRepository Database Access Object.

Encapsulates CRUD operations for CrawlJob state and CrawlStatistic metrics.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.crawl_job import CrawlJob, CrawlStatus
from src.db.models.statistic import CrawlStatistic


class CrawlRepository:
    """Repository handling CrawlJob lifecycle and execution statistics persistence."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_job(
        self,
        seed_url: str,
        max_depth: int,
        max_pages: int,
        render_js: bool = False,
    ) -> CrawlJob:
        """Creates a new CrawlJob database record.

        Args:
            seed_url (str): Seed website URL.
            max_depth (int): Maximum depth.
            max_pages (int): Maximum pages limit.
            render_js (bool): Playwright rendering flag.

        Returns:
            CrawlJob: Created ORM instance.
        """
        job = CrawlJob(
            seed_url=seed_url,
            status=CrawlStatus.PENDING,
            max_depth=max_depth,
            max_pages=max_pages,
            render_js=render_js,
        )
        self.session.add(job)
        await self.session.commit()
        await self.session.refresh(job)
        return job

    async def get_job_by_id(self, job_id: uuid.UUID) -> Optional[CrawlJob]:
        """Retrieves CrawlJob by UUID primary key.

        Args:
            job_id (uuid.UUID): Job primary key.

        Returns:
            Optional[CrawlJob]: ORM instance if found, None otherwise.
        """
        stmt = select(CrawlJob).where(CrawlJob.id == job_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_job_status(
        self,
        job_id: uuid.UUID,
        status: CrawlStatus,
        finished_at: Optional[datetime] = None,
    ) -> Optional[CrawlJob]:
        """Updates job status and optional completion timestamp.

        Args:
            job_id (uuid.UUID): Job UUID.
            status (CrawlStatus): Target status enum value.
            finished_at (Optional[datetime]): Finish timestamp.

        Returns:
            Optional[CrawlJob]: Updated ORM instance.
        """
        job = await self.get_job_by_id(job_id)
        if not job:
            return None

        job.status = status
        if finished_at:
            job.finished_at = finished_at
        elif status in (CrawlStatus.COMPLETED, CrawlStatus.FAILED):
            job.finished_at = datetime.now(timezone.utc)

        await self.session.commit()
        await self.session.refresh(job)
        return job

    async def create_or_update_statistics(
        self,
        job_id: uuid.UUID,
        pages_crawled: int,
        failed_pages: int,
        total_images: int,
        total_links: int,
        total_duration_sec: float,
    ) -> CrawlStatistic:
        """Upserts execution statistics for a crawl job.

        Args:
            job_id (uuid.UUID): Job UUID.
            pages_crawled (int): Success pages count.
            failed_pages (int): Failed pages count.
            total_images (int): Images count.
            total_links (int): Links count.
            total_duration_sec (float): Total runtime seconds.

        Returns:
            CrawlStatistic: Updated statistics ORM instance.
        """
        stmt = select(CrawlStatistic).where(CrawlStatistic.job_id == job_id)
        result = await self.session.execute(stmt)
        stat = result.scalar_one_or_none()

        if not stat:
            stat = CrawlStatistic(
                job_id=job_id,
                pages_crawled=pages_crawled,
                failed_pages=failed_pages,
                total_images=total_images,
                total_links=total_links,
                total_duration_sec=total_duration_sec,
            )
            self.session.add(stat)
        else:
            stat.pages_crawled = pages_crawled
            stat.failed_pages = failed_pages
            stat.total_images = total_images
            stat.total_links = total_links
            stat.total_duration_sec = total_duration_sec

        await self.session.commit()
        await self.session.refresh(stat)
        return stat

    async def get_statistics_by_job_id(
        self, job_id: uuid.UUID
    ) -> Optional[CrawlStatistic]:
        """Fetches execution statistics for a job ID."""
        stmt = select(CrawlStatistic).where(CrawlStatistic.job_id == job_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
