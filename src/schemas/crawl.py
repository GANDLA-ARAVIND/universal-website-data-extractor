"""Pydantic schemas for Crawl Jobs and Execution Statistics."""

import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator
from src.db.models.crawl_job import CrawlStatus
from src.utils.url_utils import validate_public_url


class CrawlCreateRequest(BaseModel):
    """Payload to request initiating a new asynchronous web crawl."""

    url: str = Field(
        ...,
        description="Target seed website URL (must be valid HTTP/HTTPS).",
        examples=["https://news.ycombinator.com"],
    )
    max_depth: int = Field(
        default=2,
        ge=0,
        le=10,
        description="Maximum link traversal depth from seed URL.",
    )
    max_pages: int = Field(
        default=50,
        ge=1,
        le=1000,
        description="Maximum total number of unique pages to crawl.",
    )
    render_js: bool = Field(
        default=False,
        description="Whether to use Playwright headless browser for JavaScript rendering.",
    )

    @field_validator("url")
    @classmethod
    def validate_target_url(cls, value: str) -> str:
        """Enforces HTTP/HTTPS public scheme and canonical normalization."""
        return validate_public_url(value)


class CrawlJobResponse(BaseModel):
    """API Response contract for Crawl Job state."""

    id: uuid.UUID
    seed_url: str
    status: CrawlStatus
    max_depth: int
    max_pages: int
    render_js: bool
    created_at: datetime
    finished_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class CrawlStatisticResponse(BaseModel):
    """API Response contract for Crawl Job execution metrics."""

    job_id: uuid.UUID
    pages_crawled: int
    failed_pages: int
    total_images: int
    total_links: int
    total_duration_sec: float

    model_config = {"from_attributes": True}
