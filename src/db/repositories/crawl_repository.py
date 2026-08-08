"""CrawlRepository Database Access Object.

Encapsulates CRUD operations for CrawlJob state and CrawlStatistic metrics.
"""

import uuid
from datetime import datetime, timezone
from typing import List, Optional, Tuple
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.crawl_job import CrawlJob, CrawlMode, CrawlStatus
from src.db.models.statistic import CrawlStatistic


class CrawlRepository:
    """Repository handling CrawlJob lifecycle and execution statistics persistence."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_jobs(
        self,
        page: int = 1,
        page_size: int = 20,
        status: Optional[CrawlStatus] = None,
        crawl_mode: Optional[CrawlMode] = None,
        search: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> Tuple[List[CrawlJob], int]:
        """Retrieves paginated, filtered, and sorted crawl jobs history.

        Returns:
            Tuple[List[CrawlJob], int]: (Crawl jobs list, Total matching records count).
        """
        stmt = select(CrawlJob)
        count_stmt = select(func.count(CrawlJob.id))

        filters = []
        if status:
            filters.append(CrawlJob.status == status)
        if crawl_mode:
            filters.append(CrawlJob.crawl_mode == crawl_mode)
        if search:
            filters.append(CrawlJob.seed_url.ilike(f"%{search}%"))

        if filters:
            stmt = stmt.where(*filters)
            count_stmt = count_stmt.where(*filters)

        total_count = (await self.session.execute(count_stmt)).scalar_one() or 0

        sort_col = getattr(CrawlJob, sort_by, CrawlJob.created_at)
        if str(sort_order).lower() == "asc":
            stmt = stmt.order_by(sort_col.asc())
        else:
            stmt = stmt.order_by(sort_col.desc())

        offset = (page - 1) * page_size
        stmt = stmt.offset(offset).limit(page_size)

        result = await self.session.execute(stmt)
        jobs = list(result.scalars().all())
        return jobs, total_count

    async def create_job(
        self,
        seed_url: str,
        max_depth: int,
        max_pages: int,
        render_js: bool = False,
        project_id: Optional[uuid.UUID] = None,
    ) -> CrawlJob:
        """Creates a new CrawlJob database record."""
        job = CrawlJob(
            seed_url=seed_url,
            status=CrawlStatus.PENDING,
            max_depth=max_depth,
            max_pages=max_pages,
            render_js=render_js,
            project_id=project_id,
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
