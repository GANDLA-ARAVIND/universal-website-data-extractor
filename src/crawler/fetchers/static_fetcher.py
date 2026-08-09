import asyncio
import time
from typing import List
import httpx
from src.core.config import settings
from src.core.logging import logger
from src.crawler.fetchers.base import BaseFetcher, FetchResult


TRANSIENT_STATUS_CODES = {408, 429, 502, 503, 504}


class StaticFetcher(BaseFetcher):
    """High-performance static page fetcher using HTTPX async client."""

    def __init__(
        self,
        timeout: float = settings.FETCH_TIMEOUT_SEC,
        max_retries: int = 3,
        backoff_factor: float = 0.5,
    ) -> None:
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
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
        """Fetches page content via HTTP GET request with retry backoff for transient errors.

        Args:
            url (str): Target web URL.

        Returns:
            FetchResult: Execution result container.
        """
        start_time = time.perf_counter()
        warnings: List[str] = []

        for attempt in range(1, self.max_retries + 1):
            try:
                response = await self.client.get(url)
                elapsed_ms = (time.perf_counter() - start_time) * 1000.0

                headers_dict = {k: v for k, v in response.headers.items()}
                redirect_url = str(response.url) if str(response.url) != url else None

                max_size = getattr(settings, "MAX_RESPONSE_SIZE_BYTES", 10485760)
                if len(response.content) > max_size:
                    logger.warning(f"Payload size ({len(response.content)} bytes) for '{url}' exceeded max limit ({max_size} bytes).")
                    return FetchResult(
                        url=str(response.url),
                        status_code=413,
                        html_content="",
                        response_time_ms=round(elapsed_ms, 2),
                        redirect_url=redirect_url,
                        error_message=f"Payload size exceeded maximum allowed limit of {max_size} bytes.",
                        warnings=warnings,
                        headers=headers_dict,
                    )

                if response.status_code in TRANSIENT_STATUS_CODES and attempt < self.max_retries:
                    warn_msg = f"Attempt {attempt}/{self.max_retries} received status {response.status_code} for {url}. Retrying..."
                    warnings.append(warn_msg)
                    logger.warning(warn_msg)
                    await asyncio.sleep(self.backoff_factor * (2 ** (attempt - 1)))
                    continue

                return FetchResult(
                    url=str(response.url),
                    status_code=response.status_code,
                    html_content=response.text,
                    response_time_ms=round(elapsed_ms, 2),
                    redirect_url=redirect_url,
                    warnings=warnings,
                    headers=headers_dict,
                )

            except (httpx.TimeoutException, httpx.NetworkError) as exc:
                elapsed_ms = (time.perf_counter() - start_time) * 1000.0
                err_type = "Timeout" if isinstance(exc, httpx.TimeoutException) else "Network Error"
                if attempt < self.max_retries:
                    warn_msg = f"Attempt {attempt}/{self.max_retries} {err_type} for '{url}': {str(exc)}. Retrying..."
                    warnings.append(warn_msg)
                    logger.warning(warn_msg)
                    await asyncio.sleep(self.backoff_factor * (2 ** (attempt - 1)))
                else:
                    logger.error(f"Static fetch failed after {self.max_retries} attempts for '{url}': {str(exc)}")
                    return FetchResult(
                        url=url,
                        status_code=408 if isinstance(exc, httpx.TimeoutException) else 500,
                        html_content="",
                        response_time_ms=round(elapsed_ms, 2),
                        error_message=f"Static fetch failed ({err_type}): {str(exc)}",
                        warnings=warnings,
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
                    warnings=warnings,
                )

        # Fallback return if loop exhausts
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        return FetchResult(
            url=url,
            status_code=500,
            html_content="",
            response_time_ms=round(elapsed_ms, 2),
            error_message="Exhausted retries",
            warnings=warnings,
        )

    async def close(self) -> None:
        """Closes HTTPX connection pool."""
        await self.client.aclose()

