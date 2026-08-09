"""Pydantic schemas package for API request and response data contracts."""

from src.schemas.crawl import CrawlCreateRequest, CrawlJobResponse, CrawlStatisticResponse
from src.schemas.page import (
    PageLinkSchema,
    PageImageSchema,
    ExtractedPageResponse,
    PaginatedPageResultsResponse,
)
from src.schemas.export import ExportFormatEnum, ExportRequest
from src.schemas.dataset import (
    StandardCrawlDataset,
    BatchDataset,
    BatchWebsiteItem,
    BatchMetadata,
    BatchStatistics,
    BatchSummary,
)

from src.schemas.ai import (
    AISourceReference,
    AIAnalysisResponse,
    AIQueryRequest,
    AIQueryResponse,
    AIBatchAnalysisResponse,
)

__all__ = [
    "CrawlCreateRequest",
    "CrawlJobResponse",
    "CrawlStatisticResponse",
    "PageLinkSchema",
    "PageImageSchema",
    "ExtractedPageResponse",
    "PaginatedPageResultsResponse",
    "ExportFormatEnum",
    "ExportRequest",
    "StandardCrawlDataset",
    "BatchDataset",
    "BatchWebsiteItem",
    "BatchMetadata",
    "BatchStatistics",
    "BatchSummary",
    "AISourceReference",
    "AIAnalysisResponse",
    "AIQueryRequest",
    "AIQueryResponse",
    "AIBatchAnalysisResponse",
]
