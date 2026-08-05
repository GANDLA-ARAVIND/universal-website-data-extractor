"""CrawlService Use-Case Layer.

Orchestrates crawl job submission, background task execution, status retrieval,
paginated results fetching, and metrics aggregation.
"""

import uuid
from typing import Tuple
from fastapi import BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import CrawlJobNotFoundException
from src.core.logging import logger
from src.crawler.engine import CrawlEngine
from src.db.models.crawl_job import CrawlJob
from src.db.models.statistic import CrawlStatistic
from src.db.repositories.crawl_repository import CrawlRepository
from src.db.repositories.page_repository import PageRepository
from src.schemas.crawl import CrawlCreateRequest


class CrawlService:
    """Service layer managing web crawl operations and asynchronous background processing."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.crawl_repo = CrawlRepository(session)
        self.page_repo = PageRepository(session)

    async def initiate_crawl(
        self,
        request: CrawlCreateRequest,
        background_tasks: BackgroundTasks,
    ) -> CrawlJob:
        """Submits a crawl job request, saves initial PENDING state in DB, and dispatches background task.

        Args:
            request (CrawlCreateRequest): Input job parameters.
            background_tasks (BackgroundTasks): FastAPI background task manager.

        Returns:
            CrawlJob: Created job ORM entity.
        """
        job = await self.crawl_repo.create_job(
            seed_url=request.url,
            max_depth=request.max_depth,
            max_pages=request.max_pages,
            render_js=request.render_js,
        )

        # Dispatch asynchronous crawl task
        background_tasks.add_task(
            self._run_crawl_in_background,
            job_id=job.id,
            seed_url=request.url,
            max_depth=request.max_depth,
            max_pages=request.max_pages,
            render_js=request.render_js,
        )

        logger.info(f"Crawl job {job.id} dispatched to background worker for {request.url}")
        return job

    async def _run_crawl_in_background(
        self,
        job_id: uuid.UUID,
        seed_url: str,
        max_depth: int,
        max_pages: int,
        render_js: bool,
    ) -> None:
        """Isolated background worker task creating its own database session context."""
        from src.db.session import AsyncSessionFactory

        async with AsyncSessionFactory() as session:
            engine = CrawlEngine(
                session=session,
                job_id=job_id,
                seed_url=seed_url,
                max_depth=max_depth,
                max_pages=max_pages,
                render_js=render_js,
            )
            await engine.execute()

    async def get_job_status(self, job_id: uuid.UUID) -> CrawlJob:
        """Fetches crawl job entity by ID.

        Raises:
            CrawlJobNotFoundException: If job does not exist.
        """
        job = await self.crawl_repo.get_job_by_id(job_id)
        if not job:
            raise CrawlJobNotFoundException(f"Crawl job with ID '{job_id}' was not found.")
        return job

    async def get_job_results(
        self, job_id: uuid.UUID, page: int = 1, limit: int = 20
    ) -> Tuple[list, int]:
        """Retrieves paginated extracted pages for a crawl job."""
        # Ensure job exists
        await self.get_job_status(job_id)

        skip = (page - 1) * limit
        return await self.page_repo.get_pages_by_job_id(job_id=job_id, skip=skip, limit=limit)

    async def get_job_statistics(self, job_id: uuid.UUID) -> CrawlStatistic:
        """Retrieves execution metrics for a crawl job."""
        # Ensure job exists
        await self.get_job_status(job_id)

        stats = await self.crawl_repo.get_statistics_by_job_id(job_id)
        if not stats:
            # Fallback zero stats if stats record not created yet
            stats = CrawlStatistic(
                job_id=job_id,
                pages_crawled=0,
                failed_pages=0,
                total_images=0,
                total_links=0,
                total_duration_sec=0.0,
            )
        return stats
