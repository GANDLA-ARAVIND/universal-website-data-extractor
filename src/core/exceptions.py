"""Custom Exception Hierarchy.

Defines domain-specific exceptions for clean error propagation across
API, crawler engine, fetcher, extractor, and repository layers.
"""

from typing import Any, Optional


class BaseAppException(Exception):
    """Base exception class for all domain-specific application errors."""

    def __init__(self, message: str, details: Optional[Any] = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class InvalidURLException(BaseAppException):
    """Raised when an input URL fails validation or domain scoping rules."""

    pass


class CrawlJobNotFoundException(BaseAppException):
    """Raised when a requested crawl job ID is not found in persistent store."""

    pass


class FetcherException(BaseAppException):
    """Raised when page content retrieval fails (network timeout, HTTP 4xx/5xx)."""

    pass


class ExtractorException(BaseAppException):
    """Raised when HTML structural parsing or metadata extraction fails."""

    pass


class ExportException(BaseAppException):
    """Raised when result dataset formatting or export generation fails."""

    pass
