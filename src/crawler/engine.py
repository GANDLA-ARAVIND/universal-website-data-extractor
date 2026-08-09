"""Asynchronous BFS Crawl Engine.

Orchestrates web traversal, URL frontier queueing, depth management, fetcher strategy
selection, HTML extraction, database persistence, and statistics aggregation.
"""

import asyncio
import time
import uuid
from collections import deque
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.core.logging import logger
from src.crawler.extractors.html_extractor import HTMLExtractor
from src.crawler.fetchers import BaseFetcher, DynamicFetcher, StaticFetcher
from src.db.models.crawl_job import CrawlStatus
from src.db.repositories.crawl_repository import CrawlRepository
from src.db.repositories.page_repository import PageRepository
from src.utils.url_utils import is_crawlable_html_url, is_same_domain, normalize_url


class CrawlEngine:
    """Asynchronous Breadth-First-Search Crawl Orchestrator."""

    def __init__(
        self,
        session: AsyncSession,
        job_id: uuid.UUID,
        seed_url: str,
        max_depth: int = 2,
        max_pages: int = 50,
        render_js: bool = False,
        crawl_delay: float = settings.DEFAULT_CRAWL_DELAY_SEC,
    ) -> None:
        self.session = session
        self.job_id = job_id
        self.seed_url = normalize_url(seed_url)
        self.max_depth = max_depth
        self.max_pages = max_pages
        self.render_js = render_js
        self.crawl_delay = crawl_delay

        self.crawl_repo = CrawlRepository(session)
        self.page_repo = PageRepository(session)
        self.extractor = HTMLExtractor()

    def _create_fetcher(self) -> BaseFetcher:
        """Instantiates fetcher strategy based on render_js flag."""
        if self.render_js:
            logger.info(f"Job {self.job_id}: Initializing Dynamic Playwright Fetcher")
            return DynamicFetcher()
        logger.info(f"Job {self.job_id}: Initializing Static HTTPX Fetcher")
        return StaticFetcher()

    async def execute(self) -> None:
        """Executes the asynchronous web crawl lifecycle."""
        start_time = time.perf_counter()
        logger.info(f"Starting crawl job {self.job_id} for seed URL: {self.seed_url}")

        # Update status to RUNNING
        await self.crawl_repo.update_job_status(self.job_id, CrawlStatus.RUNNING)

        fetcher = self._create_fetcher()

        # Frontier queue holds tuples of (target_url, current_depth)
        queue = deque([(self.seed_url, 0)])
        visited_urls = {self.seed_url}

        pages_crawled = 0
        failed_pages = 0
        total_images_count = 0
        total_links_count = 0
        lock = asyncio.Lock()
        concurrency_limit = 5
        semaphore = asyncio.Semaphore(concurrency_limit)

        async def _crawl_single(url: str, depth: int):
            nonlocal pages_crawled, failed_pages, total_images_count, total_links_count
            async with semaphore:
                logger.info(
                    f"Job {self.job_id} | Crawling Depth {depth}/{self.max_depth}: {url}"
                )
                try:
                    fetch_res = await fetcher.fetch(url)
                    if fetch_res.is_success:
                        extracted_dto = self.extractor.parse(
                            html=fetch_res.html_content,
                            page_url=fetch_res.url,
                        )
                        if fetch_res.warnings:
                            extracted_dto.warnings.extend(fetch_res.warnings)

                        async with lock:
                            await self.page_repo.save_extracted_page(
                                job_id=self.job_id,
                                dto=extracted_dto,
                                depth=depth,
                                status_code=fetch_res.status_code,
                                response_time_ms=fetch_res.response_time_ms,
                            )
                            pages_crawled += 1
                            total_images_count += len(extracted_dto.images)
                            total_links_count += len(extracted_dto.internal_links) + len(extracted_dto.external_links)

                            if depth < self.max_depth:
                                for link_obj in extracted_dto.internal_links:
                                    target = link_obj["target_url"]
                                    target_norm = normalize_url(target)
                                    if (
                                        target_norm not in visited_urls
                                        and is_same_domain(self.seed_url, target)
                                        and is_crawlable_html_url(target)
                                    ):
                                        visited_urls.add(target_norm)
                                        queue.append((target, depth + 1))
                    else:
                        async with lock:
                            failed_pages += 1
                        logger.warning(
                            f"Job {self.job_id} | Fetch failed for '{url}' "
                            f"Status: {fetch_res.status_code} Error: {fetch_res.error_message}"
                        )
                except Exception as page_exc:
                    async with lock:
                        failed_pages += 1
                    logger.error(
                        f"Job {self.job_id} | Unexpected failure processing page '{url}': {page_exc}",
                        exc_info=True,
                    )

        try:
            while queue and pages_crawled < self.max_pages:
                batch_items = []
                while queue and len(batch_items) < concurrency_limit and (pages_crawled + len(batch_items)) < self.max_pages:
                    batch_items.append(queue.popleft())

                if not batch_items:
                    break

                tasks = [_crawl_single(u, d) for u, d in batch_items]
                await asyncio.gather(*tasks)

                if self.crawl_delay > 0 and queue:
                    await asyncio.sleep(self.crawl_delay)

            total_duration = round(time.perf_counter() - start_time, 2)

            # Determine final status
            final_status = (
                CrawlStatus.COMPLETED
                if pages_crawled > 0
                else (CrawlStatus.FAILED if failed_pages > 0 else CrawlStatus.COMPLETED)
            )

            # Persist execution statistics
            await self.crawl_repo.create_or_update_statistics(
                job_id=self.job_id,
                pages_crawled=pages_crawled,
                failed_pages=failed_pages,
                total_images=total_images_count,
                total_links=total_links_count,
                total_duration_sec=total_duration,
            )

            # Mark job final status
            await self.crawl_repo.update_job_status(
                self.job_id,
                final_status,
                finished_at=datetime.now(timezone.utc),
            )
            logger.info(
                f"Job {self.job_id} {final_status.value}. Pages: {pages_crawled}, "
                f"Failed: {failed_pages}, Images: {total_images_count}, Links: {total_links_count}, "
                f"Duration: {total_duration}s"
            )

        except Exception as exc:
            total_duration = round(time.perf_counter() - start_time, 2)
            logger.error(f"Job {self.job_id} FAILED unexpectedly: {str(exc)}", exc_info=True)
            await self.crawl_repo.update_job_status(self.job_id, CrawlStatus.FAILED)
            await self.crawl_repo.create_or_update_statistics(
                job_id=self.job_id,
                pages_crawled=pages_crawled,
                failed_pages=failed_pages + 1,
                total_images=total_images_count,
                total_links=total_links_count,
                total_duration_sec=total_duration,
            )
        finally:
            await fetcher.close()

