"""Static HTTP Fetcher Strategy using HTTPX.

Provides fast, high-throughput asynchronous HTTP page retrieval for static web pages.
"""

import time
import httpx
from src.core.config import settings
from src.core.logging import logger
from src.crawler.fetchers.base import BaseFetcher, FetchResult


class StaticFetcher(BaseFetcher):
    """High-performance static page fetcher using HTTPX async client."""

    def __init__(self, timeout: float = settings.FETCH_TIMEOUT_SEC) -> None:
        self.timeout = timeout
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36 WebScraper/1.0"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }
        self.client = httpx.AsyncClient(
            headers=self.headers,
            timeout=httpx.Timeout(self.timeout),
            follow_redirects=True,
            verify=False,  # Bypass broken SSL certificates for resilient crawling
        )

    async def fetch(self, url: str) -> FetchResult:
        """Fetches page content via HTTP GET request.

        Args:
            url (str): Target web URL.

        Returns:
            FetchResult: Execution result container.
        """
        start_time = time.perf_counter()
        try:
            response = await self.client.get(url)
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0

            return FetchResult(
                url=str(response.url),
                status_code=response.status_code,
                html_content=response.text,
                response_time_ms=round(elapsed_ms, 2),
            )
        except httpx.TimeoutException:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            logger.warning(f"Request timeout fetching static page: {url}")
            return FetchResult(
                url=url,
                status_code=408,
                html_content="",
                response_time_ms=round(elapsed_ms, 2),
                error_message="HTTP Request Timeout",
            )
        except Exception as exc:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            logger.error(f"Error fetching static page '{url}': {str(exc)}")
            return FetchResult(
                url=url,
                status_code=500,
                html_content="",
                response_time_ms=round(elapsed_ms, 2),
                error_message=str(exc),
            )

    async def close(self) -> None:
        """Closes HTTPX connection pool."""
        await self.client.aclose()
