"""BatchRepository Database Access Object.

Encapsulates persistence operations for BatchJob and child CrawlJob entities.
"""

import uuid
from datetime import datetime, timezone
from typing import List, Optional, Tuple
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.db.models.batch_job import BatchJob
from src.db.models.crawl_job import CrawlJob, CrawlMode, CrawlStatus
from src.db.models.image import PageImage
from src.db.models.link import PageLink
from src.db.models.page import ExtractedPage
from src.db.models.statistic import CrawlStatistic


class BatchRepository:
    """Repository handling BatchJob ORM database operations."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_batch_job(
        self,
        urls: List[str],
        max_depth: int = 2,
        max_pages: int = 50,
        render_js: bool = False,
        project_id: Optional[uuid.UUID] = None,
    ) -> BatchJob:
        """Persists a new BatchJob parent and child CrawlJob records."""
        batch = BatchJob(
            status=CrawlStatus.PENDING,
            total_urls=len(urls),
            project_id=project_id,
        )
        self.session.add(batch)
        await self.session.flush()

        for url in urls:
            job = CrawlJob(
                seed_url=url,
                batch_id=batch.id,
                project_id=project_id,
                crawl_mode=CrawlMode.BATCH,
                status=CrawlStatus.PENDING,
                max_depth=max_depth,
                max_pages=max_pages,
                render_js=render_js,
            )
            self.session.add(job)

        await self.session.commit()
        await self.session.refresh(batch)
        return batch

    async def get_batch_by_id(self, batch_id: uuid.UUID) -> Optional[BatchJob]:
        """Retrieves BatchJob entity with child jobs eagerly loaded."""
        stmt = (
            select(BatchJob)
            .options(selectinload(BatchJob.jobs))
            .where(BatchJob.id == batch_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_batch_status(
        self, batch_id: uuid.UUID, status: CrawlStatus
    ) -> Optional[BatchJob]:
        """Updates batch execution status and finished timestamp."""
        batch = await self.get_batch_by_id(batch_id)
        if not batch:
            return None

        batch.status = status
        if status in (CrawlStatus.COMPLETED, CrawlStatus.FAILED):
            batch.finished_at = datetime.now(timezone.utc)

        await self.session.commit()
        await self.session.refresh(batch)
        return batch

    async def get_failed_jobs(self, batch_id: uuid.UUID) -> List[CrawlJob]:
        """Fetches only child jobs within a batch that failed."""
        stmt = (
            select(CrawlJob)
            .where(
                CrawlJob.batch_id == batch_id,
                CrawlJob.status == CrawlStatus.FAILED,
            )
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_batch_statistics(self, batch_id: uuid.UUID) -> dict:
        """Aggregates crawl metrics across all child jobs in a batch."""
        batch = await self.get_batch_by_id(batch_id)
        if not batch:
            return {}

        job_ids = [j.id for j in batch.jobs]
        if not job_ids:
            return {
                "batch_id": str(batch.id),
                "total_websites": 0,
                "completed_websites": 0,
                "failed_websites": 0,
                "total_pages": 0,
                "total_images": 0,
                "total_links": 0,
                "total_duration_sec": 0.0,
            }

        # Aggregate Pages
        pages_stmt = select(func.count(ExtractedPage.id)).where(
            ExtractedPage.job_id.in_(job_ids)
        )
        total_pages = (await self.session.execute(pages_stmt)).scalar_one() or 0

        # Aggregate Links
        links_stmt = select(func.count(PageLink.id)).join(ExtractedPage).where(
            ExtractedPage.job_id.in_(job_ids)
        )
        total_links = (await self.session.execute(links_stmt)).scalar_one() or 0

        # Aggregate Images
        images_stmt = select(func.count(PageImage.id)).join(ExtractedPage).where(
            ExtractedPage.job_id.in_(job_ids)
        )
        total_images = (await self.session.execute(images_stmt)).scalar_one() or 0

        # Aggregate Duration
        dur_stmt = select(func.coalesce(func.sum(CrawlStatistic.total_duration_sec), 0.0)).where(
            CrawlStatistic.job_id.in_(job_ids)
        )
        total_duration = (await self.session.execute(dur_stmt)).scalar_one() or 0.0

        completed_cnt = sum(1 for j in batch.jobs if j.status == CrawlStatus.COMPLETED)
        failed_cnt = sum(1 for j in batch.jobs if j.status == CrawlStatus.FAILED)

        return {
            "batch_id": str(batch.id),
            "total_websites": len(batch.jobs),
            "completed_websites": completed_cnt,
            "failed_websites": failed_cnt,
            "total_pages": total_pages,
            "total_images": total_images,
            "total_links": total_links,
            "total_duration_sec": float(total_duration),
        }

    async def list_batches(
        self,
        page: int = 1,
        page_size: int = 20,
        status: Optional[CrawlStatus] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> Tuple[List[BatchJob], int]:
        """Retrieves paginated, filtered, and sorted batch jobs history.

        Returns:
            Tuple[List[BatchJob], int]: (Batch jobs list, Total matching records count).
        """
        stmt = select(BatchJob).options(selectinload(BatchJob.jobs))
        count_stmt = select(func.count(BatchJob.id))

        if status:
            stmt = stmt.where(BatchJob.status == status)
            count_stmt = count_stmt.where(BatchJob.status == status)

        total_count = (await self.session.execute(count_stmt)).scalar_one() or 0

        sort_col = getattr(BatchJob, sort_by, BatchJob.created_at)
        if str(sort_order).lower() == "asc":
            stmt = stmt.order_by(sort_col.asc())
        else:
            stmt = stmt.order_by(sort_col.desc())

        offset = (page - 1) * page_size
        stmt = stmt.offset(offset).limit(page_size)

        result = await self.session.execute(stmt)
        batches = list(result.scalars().all())
        return batches, total_count
