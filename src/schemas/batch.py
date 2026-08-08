"""Batch Crawl Pydantic Schemas.

Defines request payloads, progress metadata, and response models for batch crawling.
"""

import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator
from src.utils.url_utils import validate_public_url

from src.db.models.crawl_job import CrawlStatus
from src.schemas.crawl import CrawlJobResponse


class BatchCreateRequest(BaseModel):
    """Payload schema for initiating a multi-website batch crawl."""

    urls: List[str] = Field(
        ...,
        min_length=1,
        max_length=100,
        description="List of target website seed URLs to crawl.",
        json_schema_extra={"example": ["https://example.com", "https://python.org"]},
    )
    project_id: Optional[uuid.UUID] = Field(
        default=None,
        description="Optional project UUID to associate this batch crawl with.",
    )
    max_depth: int = Field(
        default=2,
        ge=1,
        le=5,
        description="Maximum BFS link traversal depth for each website.",
    )
    max_pages: int = Field(
        default=50,
        ge=1,
        le=500,
        description="Maximum pages to extract per website.",
    )
    render_js: bool = Field(
        default=False,
        description="Enable Playwright browser rendering for JavaScript pages.",
    )

    @field_validator("urls")
    @classmethod
    def validate_batch_urls(cls, urls: List[str]) -> List[str]:
        """Validates that all seed URLs in batch request are valid public URLs."""
        return [validate_public_url(u) for u in urls]


class BatchJobResponse(BaseModel):
    """Response model representing batch crawl execution progress and child jobs."""

    id: uuid.UUID
    status: CrawlStatus
    project_id: Optional[uuid.UUID] = None
    total_urls: int
    completed_urls: int
    running_urls: int
    failed_urls: int
    progress_percentage: float
    created_at: datetime
    finished_at: Optional[datetime] = None
    jobs: List[CrawlJobResponse] = []

    model_config = {"from_attributes": True}


class BatchStatisticResponse(BaseModel):
    """Response model for aggregated batch crawling metrics."""

    batch_id: uuid.UUID
    total_websites: int
    completed_websites: int
    failed_websites: int
    total_pages: int
    total_images: int
    total_links: int
    total_duration_sec: float

    model_config = {"from_attributes": True}
