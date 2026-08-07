from typing import List, Tuple
from uuid import UUID

from src.application.services.exporters import get_exporter_registry
from src.core.exceptions import CrawlJobNotFoundException, ExportException
from src.db.repositories.batch_repository import BatchRepository
from src.db.repositories.crawl_repository import CrawlRepository
from src.db.models.crawl_job import CrawlJob, CrawlMode
from src.db.models.page import ExtractedPage
from src.db.models.statistic import CrawlStatistic
from src.schemas.export import ExportFormat


class ExportService:
    """Service layer orchestrating dataset export generation."""

    def __init__(
        self,
        crawl_repo: CrawlRepository,
        page_repo: PageRepository,
    ) -> None:
        self.crawl_repo = crawl_repo
        self.page_repo = page_repo
        self.registry = get_exporter_registry()

    async def generate_export(
        self,
        job_id: UUID,
        export_format: ExportFormat,
    ) -> Tuple[bytes, str, str]:
        """
        Orchestrates loading job, page records, and statistics, delegating
        formatting to the registered Exporter strategy.
        """
        job = await self.crawl_repo.get_job_by_id(job_id)
        if not job:
            raise CrawlJobNotFoundException(f"Crawl job '{job_id}' not found.")

        pages = await self.page_repo.get_all_pages_for_job(job_id)
        if not pages:
            raise ExportException(f"No pages extracted for job '{job_id}' to export.")

        stats = await self.crawl_repo.get_statistics_by_job_id(job_id)

        exporter = self.registry.get(export_format)
        return await exporter.export(pages, job, stats)

    async def generate_batch_export(
        self,
        batch_id: UUID,
        export_format: ExportFormat,
    ) -> Tuple[bytes, str, str]:
        """
        Orchestrates loading all child jobs & pages across a batch, delegating
        multi-website dataset formatting to the registered Exporter strategy.
        """
        batch_repo = BatchRepository(self.crawl_repo.session)
        batch = await batch_repo.get_batch_by_id(batch_id)
        if not batch or not batch.jobs:
            raise CrawlJobNotFoundException(f"BatchJob '{batch_id}' not found or empty.")

        all_pages: List[ExtractedPage] = []
        for child_job in batch.jobs:
            child_pages = await self.page_repo.get_all_pages_for_job(child_job.id)
            all_pages.extend(child_pages)

        if not all_pages:
            raise ExportException(f"No pages extracted across batch '{batch_id}' to export.")

        # Create synthetic CrawlJob and CrawlStatistic representing the batch
        urls_str = ", ".join([j.seed_url for j in batch.jobs])
        batch_virtual_job = CrawlJob(
            id=batch.id,
            seed_url=urls_str,
            status=batch.status,
            crawl_mode=CrawlMode.BATCH,
            max_depth=batch.jobs[0].max_depth if batch.jobs else 2,
            max_pages=batch.jobs[0].max_pages if batch.jobs else 50,
            render_js=batch.jobs[0].render_js if batch.jobs else False,
            created_at=batch.created_at,
            finished_at=batch.finished_at,
        )

        stats_dict = await batch_repo.get_batch_statistics(batch_id)
        stats_obj = CrawlStatistic(
            job_id=batch.id,
            pages_crawled=stats_dict.get("total_pages", 0),
            failed_pages=stats_dict.get("failed_websites", 0),
            total_images=stats_dict.get("total_images", 0),
            total_links=stats_dict.get("total_links", 0),
            total_duration_sec=stats_dict.get("total_duration_sec", 0.0),
        )

        exporter = self.registry.get(export_format)
        file_bytes, filename, media_type = await exporter.export(all_pages, batch_virtual_job, stats_obj)
        
        # Override filename for batch
        batch_filename = f"batch_export_{str(batch_id)[:8]}.{export_format.value}"
        if export_format == ExportFormat.MARKDOWN:
            batch_filename = f"batch_export_{str(batch_id)[:8]}.md"

        return file_bytes, batch_filename, media_type
