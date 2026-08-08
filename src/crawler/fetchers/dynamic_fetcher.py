import asyncio
import time
from typing import Any, List, Optional
from src.core.config import settings
from src.core.logging import logger
from src.crawler.fetchers.base import BaseFetcher, FetchResult

try:
    from playwright.async_api import Browser, Playwright, async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    Browser = None  # type: ignore[assignment, misc]
    Playwright = None  # type: ignore[assignment, misc]


class DynamicFetcher(BaseFetcher):
    """Dynamic page fetcher using Playwright headless browser rendering."""

    def __init__(
        self,
        headless: bool = settings.PLAYWRIGHT_HEADLESS,
        timeout: float = settings.FETCH_TIMEOUT_SEC,
        max_retries: int = 2,
        backoff_factor: float = 1.0,
    ) -> None:
        self.headless = headless
        self.timeout_ms = int(timeout * 1000)
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.playwright: Optional[Any] = None
        self.browser: Optional[Any] = None

    async def _ensure_browser(self) -> Any:
        """Lazy initializer for Playwright browser instance."""
        if not PLAYWRIGHT_AVAILABLE:
            raise RuntimeError(
                "Playwright package is not installed. Run 'pip install playwright && playwright install' to enable dynamic JS crawling."
            )
        if not self.playwright:
            self.playwright = await async_playwright().start()
        if not self.browser:
            self.browser = await self.playwright.chromium.launch(
                headless=self.headless,
                args=["--no-sandbox", "--disable-dev-shm-usage"],
            )
        return self.browser

    async def fetch(self, url: str) -> FetchResult:
        """Navigates to URL in headless Chromium, waits for DOM rendering, and retrieves HTML.

        Args:
            url (str): Target web URL.

        Returns:
            FetchResult: Execution result container.
        """
        start_time = time.perf_counter()
        warnings: List[str] = []

        for attempt in range(1, self.max_retries + 1):
            browser = await self._ensure_browser()
            context = await browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/122.0.0.0 Safari/537.36 WebScraper/1.0"
                )
            )

            try:
                page = await context.new_page()
                try:
                    response = await page.goto(
                        url,
                        timeout=self.timeout_ms,
                        wait_until="domcontentloaded",
                    )

                    status_code = response.status if response else 200
                    final_url = page.url
                    html_content = await page.content()
                    elapsed_ms = (time.perf_counter() - start_time) * 1000.0

                    redirect_url = final_url if final_url != url else None

                    return FetchResult(
                        url=final_url,
                        status_code=status_code,
                        html_content=html_content,
                        response_time_ms=round(elapsed_ms, 2),
                        redirect_url=redirect_url,
                        warnings=warnings,
                    )
                finally:
                    await page.close()
            except Exception as exc:
                elapsed_ms = (time.perf_counter() - start_time) * 1000.0
                if attempt < self.max_retries:
                    warn_msg = f"Playwright attempt {attempt}/{self.max_retries} failed for '{url}': {str(exc)}. Retrying..."
                    warnings.append(warn_msg)
                    logger.warning(warn_msg)
                    await asyncio.sleep(self.backoff_factor * attempt)
                else:
                    logger.error(f"Error fetching dynamic page '{url}' via Playwright after {self.max_retries} attempts: {str(exc)}")
                    return FetchResult(
                        url=url,
                        status_code=500,
                        html_content="",
                        response_time_ms=round(elapsed_ms, 2),
                        error_message=f"Dynamic fetch failed: {str(exc)}",
                        warnings=warnings,
                    )
            finally:
                await context.close()

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        return FetchResult(
            url=url,
            status_code=500,
            html_content="",
            response_time_ms=round(elapsed_ms, 2),
            error_message="Exhausted Playwright retries",
            warnings=warnings,
        )

    async def close(self) -> None:
        """Closes browser instances and stops Playwright driver process."""
        if self.browser:
            await self.browser.close()
            self.browser = None
        if self.playwright:
            await self.playwright.stop()
            self.playwright = None

