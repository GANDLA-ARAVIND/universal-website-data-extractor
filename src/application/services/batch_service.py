"""Batch Crawling Service.

Orchestrates multi-website batch crawling with concurrency control, URL validation,
deduplication, failure isolation, progress tracking, and failed job retries.
"""

import asyncio
import logging
import uuid
from typing import List, Optional, Tuple

from fastapi import BackgroundTasks

from src.application.services.crawl_service import CrawlService
from src.core.config import settings
from src.core.exceptions import CrawlJobNotFoundException, InvalidURLException
from src.crawler.engine import CrawlEngine
from src.db.models.crawl_job import CrawlJob, CrawlStatus
from src.db.models.user import User
from src.db.repositories.batch_repository import BatchRepository
from src.db.repositories.crawl_repository import CrawlRepository
from src.schemas.batch import (
    BatchCreateRequest,
    BatchJobResponse,
    BatchStatisticResponse,
)
from src.schemas.crawl import CrawlJobResponse
from src.utils.url_utils import normalize_url, validate_public_url

logger = logging.getLogger(__name__)


class BatchService:
    """Service handling multi-website batch crawling lifecycle."""

    def __init__(
        self,
        batch_repo: BatchRepository,
        crawl_repo: CrawlRepository,
        crawl_service: CrawlService,
    ) -> None:
        self.batch_repo = batch_repo
        self.crawl_repo = crawl_repo
        self.crawl_service = crawl_service

    def validate_and_normalize_urls(self, raw_urls: List[str]) -> List[str]:
        """Validates and deduplicates input target URLs before job creation."""
        normalized: List[str] = []
        seen = set()

        for url_str in raw_urls:
            cleaned = url_str.strip()
            if not cleaned:
                continue

            # validate_public_url raises InvalidURLException if invalid
            norm = validate_public_url(cleaned)
            if norm not in seen:
                seen.add(norm)
                normalized.append(cleaned)

        if not normalized:
            raise InvalidURLException("At least one valid target URL must be provided.")

        return normalized

    async def initiate_batch_crawl(
        self,
        request: BatchCreateRequest,
        background_tasks: BackgroundTasks,
    ) -> BatchJobResponse:
        """Initiates a batch crawl for validated and deduplicated target URLs."""
        valid_urls = self.validate_and_normalize_urls(request.urls)

        batch = await self.batch_repo.create_batch_job(
            urls=valid_urls,
            max_depth=request.max_depth,
            max_pages=request.max_pages,
            render_js=request.render_js,
            project_id=request.project_id,
        )

        background_tasks.add_task(
            self._process_batch_crawl,
            batch_id=batch.id,
            max_depth=request.max_depth,
            max_pages=request.max_pages,
            render_js=request.render_js,
        )

        return await self.get_batch_status(batch.id)

    async def _process_batch_crawl(
        self,
        batch_id: uuid.UUID,
        max_depth: int,
        max_pages: int,
        render_js: bool,
        job_ids_to_run: Optional[List[uuid.UUID]] = None,
    ) -> None:
        """Background worker executing batch crawl jobs under bounded concurrency with isolated session contexts."""
        from src.db.session import AsyncSessionFactory

        async with AsyncSessionFactory() as session:
            batch_repo = BatchRepository(session)
            batch = await batch_repo.get_batch_by_id(batch_id)
            if not batch:
                return

            await batch_repo.update_batch_status(batch_id, CrawlStatus.RUNNING)

            target_jobs_data = [(j.id, j.seed_url) for j in batch.jobs]
            if job_ids_to_run:
                target_jobs_data = [
                    t for t in target_jobs_data if t[0] in job_ids_to_run
                ]

        semaphore = asyncio.Semaphore(settings.MAX_CONCURRENT_BATCH_JOBS)

        async def run_single_job(job_id: uuid.UUID, seed_url: str) -> None:
            async with semaphore:
                async with AsyncSessionFactory() as job_session:
                    crawl_repo = CrawlRepository(job_session)
                    try:
                        engine = CrawlEngine(
                            session=job_session,
                            job_id=job_id,
                            seed_url=seed_url,
                            max_depth=max_depth,
                            max_pages=max_pages,
                            render_js=render_js,
                        )
                        await engine.execute()
                    except Exception as exc:
                        logger.error(
                            f"Child crawl job {job_id} for website {seed_url} failed: {exc}",
                            exc_info=True,
                        )
                        await crawl_repo.update_job_status(job_id, CrawlStatus.FAILED)

        await asyncio.gather(
            *(run_single_job(jid, url) for jid, url in target_jobs_data),
            return_exceptions=True,
        )

        # Re-evaluate overall batch status in a fresh session
        async with AsyncSessionFactory() as session:
            batch_repo = BatchRepository(session)
            refreshed_batch = await batch_repo.get_batch_by_id(batch_id)
            if refreshed_batch:
                completed_cnt = sum(
                    1 for j in refreshed_batch.jobs if j.status == CrawlStatus.COMPLETED
                )
                failed_cnt = sum(
                    1 for j in refreshed_batch.jobs if j.status == CrawlStatus.FAILED
                )
                total_cnt = len(refreshed_batch.jobs)

                if completed_cnt == total_cnt:
                    final_status = CrawlStatus.COMPLETED
                elif failed_cnt == total_cnt:
                    final_status = CrawlStatus.FAILED
                elif completed_cnt > 0 and failed_cnt > 0:
                    final_status = CrawlStatus.PARTIALLY_COMPLETED
                else:
                    final_status = CrawlStatus.COMPLETED

                await batch_repo.update_batch_status(batch_id, final_status)

    async def retry_failed_websites(
        self,
        batch_id: uuid.UUID,
        background_tasks: BackgroundTasks,
        current_user: Optional[User] = None,
    ) -> BatchJobResponse:
        """Re-triggers crawl execution ONLY for child jobs in a batch that failed."""
        await self.get_batch_status(batch_id, current_user=current_user)

        failed_jobs = await self.batch_repo.get_failed_jobs(batch_id)
        if not failed_jobs:
            return await self.get_batch_status(batch_id, current_user=current_user)

        failed_ids = [j.id for j in failed_jobs]
        for fj in failed_jobs:
            await self.crawl_repo.update_job_status(fj.id, CrawlStatus.PENDING)

        await self.batch_repo.update_batch_status(batch_id, CrawlStatus.RUNNING)

        first_job = failed_jobs[0]
        background_tasks.add_task(
            self._process_batch_crawl,
            batch_id=batch_id,
            max_depth=first_job.max_depth,
            max_pages=first_job.max_pages,
            render_js=first_job.render_js,
            job_ids_to_run=failed_ids,
        )

        return await self.get_batch_status(batch_id, current_user=current_user)

    async def get_batch_status(
        self, batch_id: uuid.UUID, current_user: Optional[User] = None
    ) -> BatchJobResponse:
        """Fetches progress summary, child jobs, and progress percentage for a batch."""
        batch = await self.batch_repo.get_batch_by_id(batch_id)
        if not batch:
            raise CrawlJobNotFoundException(f"BatchJob '{batch_id}' not found.")

        if batch.project_id:
            from src.db.repositories.project_repository import ProjectRepository
            proj_repo = ProjectRepository(self.batch_repo.session)
            project = await proj_repo.get_by_id(batch.project_id)
            if not project or not current_user or project.user_id != current_user.id:
                raise CrawlJobNotFoundException(f"BatchJob '{batch_id}' not found.")

        total = len(batch.jobs)
        completed = sum(1 for j in batch.jobs if j.status == CrawlStatus.COMPLETED)
        running = sum(1 for j in batch.jobs if j.status == CrawlStatus.RUNNING)
        failed = sum(1 for j in batch.jobs if j.status == CrawlStatus.FAILED)

        progress_percentage = (
            round(((completed + failed) / total) * 100, 1) if total > 0 else 0.0
        )

        child_job_responses = [CrawlJobResponse.model_validate(j) for j in batch.jobs]

        return BatchJobResponse(
            id=batch.id,
            status=batch.status,
            project_id=batch.project_id,
            total_urls=total,
            completed_urls=completed,
            running_urls=running,
            failed_urls=failed,
            progress_percentage=progress_percentage,
            created_at=batch.created_at,
            finished_at=batch.finished_at,
            jobs=child_job_responses,
        )

    async def list_batches(
        self,
        page: int = 1,
        page_size: int = 20,
        status: Optional[CrawlStatus] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> Tuple[List[BatchJobResponse], int]:
        """Retrieves paginated, filtered, and sorted batch jobs history list."""
        batches, total_count = await self.batch_repo.list_batches(
            page=page,
            page_size=page_size,
            status=status,
            sort_by=sort_by,
            sort_order=sort_order,
        )
        batch_responses = []
        for b in batches:
            total = len(b.jobs)
            completed = sum(1 for j in b.jobs if j.status == CrawlStatus.COMPLETED)
            running = sum(1 for j in b.jobs if j.status == CrawlStatus.RUNNING)
            failed = sum(1 for j in b.jobs if j.status == CrawlStatus.FAILED)
            pct = round(((completed + failed) / total) * 100, 1) if total > 0 else 0.0
            child_job_responses = [CrawlJobResponse.model_validate(j) for j in b.jobs]

            res = BatchJobResponse(
                id=b.id,
                status=b.status,
                total_urls=total,
                completed_urls=completed,
                running_urls=running,
                failed_urls=failed,
                progress_percentage=pct,
                created_at=b.created_at,
                finished_at=b.finished_at,
                jobs=child_job_responses,
            )
            batch_responses.append(res)

        return batch_responses, total_count

    async def get_batch_statistics(
        self, batch_id: uuid.UUID, current_user: Optional[User] = None
    ) -> BatchStatisticResponse:
        """Retrieves aggregated metrics across all websites in a batch."""
        await self.get_batch_status(batch_id, current_user=current_user)
        stats = await self.batch_repo.get_batch_statistics(batch_id)
        if not stats:
            raise CrawlJobNotFoundException(f"BatchJob '{batch_id}' not found.")
        return BatchStatisticResponse.model_validate(stats)
