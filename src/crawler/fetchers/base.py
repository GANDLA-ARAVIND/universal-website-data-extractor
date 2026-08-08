"""Fetcher Base Strategy Interface and Data Transfer Contracts.

Defines the abstract interface for all page retrieval strategies (HTTP vs Playwright).
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class FetchResult:
    """Encapsulates raw page fetch response state and metadata."""

    url: str
    status_code: int
    html_content: str
    response_time_ms: float
    error_message: Optional[str] = None
    redirect_url: Optional[str] = None
    warnings: List[str] = field(default_factory=list)
    headers: Dict[str, str] = field(default_factory=dict)

    @property
    def is_success(self) -> bool:
        """Indicates whether HTTP status code represents a successful response."""
        return 200 <= self.status_code < 300 and self.html_content != ""


class BaseFetcher(ABC):
    """Abstract Base Class for web fetching strategy implementations."""

    @abstractmethod
    async def fetch(self, url: str) -> FetchResult:
        """Asynchronously retrieves HTML content for a target URL.

        Args:
            url (str): Target web page URL.

        Returns:
            FetchResult: Data object containing status code, HTML body, and execution metrics.
        """
        pass

    @abstractmethod
    async def close(self) -> None:
        """Releases underlying HTTP client network connections or browser sessions."""
        pass
