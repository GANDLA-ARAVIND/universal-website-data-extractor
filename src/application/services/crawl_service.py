"""CrawlService Use-Case Layer.

Orchestrates crawl job submission, background task execution, status retrieval,
paginated results fetching, and metrics aggregation.
"""

import uuid
from typing import Optional, Tuple
from fastapi import BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import CrawlJobNotFoundException
from src.core.logging import logger
from src.crawler.engine import CrawlEngine
from src.db.models.crawl_job import CrawlJob, CrawlMode, CrawlStatus
from src.db.models.statistic import CrawlStatistic
from src.db.repositories.crawl_repository import CrawlRepository
from src.db.repositories.page_repository import PageRepository
from src.db.models.user import User
from src.schemas.crawl import CrawlCreateRequest


class CrawlService:
    """Service layer managing web crawl operations and asynchronous background processing."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.crawl_repo = CrawlRepository(session)
        self.page_repo = PageRepository(session)

    async def list_jobs(
        self,
        page: int = 1,
        page_size: int = 20,
        status: Optional[CrawlStatus] = None,
        crawl_mode: Optional[CrawlMode] = None,
        search: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> Tuple[list, int]:
        """Retrieves paginated, filtered, and sorted crawl jobs list."""
        return await self.crawl_repo.list_jobs(
            page=page,
            page_size=page_size,
            status=status,
            crawl_mode=crawl_mode,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order,
        )

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
            project_id=request.project_id,
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

    async def get_job_status(
        self, job_id: uuid.UUID, current_user: Optional[User] = None
    ) -> CrawlJob:
        """Fetches crawl job entity by ID, enforcing user ownership if job belongs to a project.

        Raises:
            CrawlJobNotFoundException: If job does not exist or user is unauthorized.
        """
        job = await self.crawl_repo.get_job_by_id(job_id)
        if not job:
            raise CrawlJobNotFoundException(f"Crawl job with ID '{job_id}' was not found.")

        if job.project_id:
            from src.db.repositories.project_repository import ProjectRepository
            proj_repo = ProjectRepository(self.session)
            project = await proj_repo.get_by_id(job.project_id)
            if not project or not current_user or project.user_id != current_user.id:
                raise CrawlJobNotFoundException(f"Crawl job with ID '{job_id}' was not found.")

        return job

    async def get_job_results(
        self,
        job_id: uuid.UUID,
        page: int = 1,
        limit: int = 20,
        current_user: Optional[User] = None,
    ) -> Tuple[list, int]:
        """Retrieves paginated extracted pages for a crawl job."""
        await self.get_job_status(job_id, current_user=current_user)

        skip = (page - 1) * limit
        return await self.page_repo.get_pages_by_job_id(job_id=job_id, skip=skip, limit=limit)

    async def get_job_statistics(
        self, job_id: uuid.UUID, current_user: Optional[User] = None
    ) -> CrawlStatistic:
        """Retrieves execution metrics for a crawl job."""
        await self.get_job_status(job_id, current_user=current_user)

        stats = await self.crawl_repo.get_statistics_by_job_id(job_id)
        if not stats:
            stats = CrawlStatistic(
                job_id=job_id,
                pages_crawled=0,
                failed_pages=0,
                total_images=0,
                total_links=0,
                total_duration_sec=0.0,
            )
        return stats
