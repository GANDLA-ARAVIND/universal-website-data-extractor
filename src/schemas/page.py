"""Pydantic schemas for Extracted Page data, links, images, and paginated API responses."""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class PageLinkSchema(BaseModel):
    """Schema representing an extracted hyperlink."""

    source_url: str
    target_url: str
    anchor_text: Optional[str] = None
    is_external: bool

    model_config = {"from_attributes": True}


class PageImageSchema(BaseModel):
    """Schema representing an extracted image asset."""

    image_url: str
    alt_text: Optional[str] = None

    model_config = {"from_attributes": True}


class ExtractedPageResponse(BaseModel):
    """API Response model for a single extracted web page."""

    id: uuid.UUID
    job_id: uuid.UUID
    url: str
    normalized_url: str
    status_code: int
    depth: int
    title: Optional[str] = None
    meta_description: Optional[str] = None
    headings: Dict[str, Any] = Field(default_factory=dict)
    paragraphs: List[str] = Field(default_factory=list)
    lists: List[Any] = Field(default_factory=list)
    tables: List[Any] = Field(default_factory=list)
    response_time_ms: float
    fetched_at: datetime = Field(alias="created_at")
    links_count: int = 0
    images_count: int = 0

    model_config = {"from_attributes": True, "populate_by_name": True}


class PaginatedPageResultsResponse(BaseModel):
    """Paginated wrapper for extracted pages list API."""

    total: int
    page: int
    limit: int
    data: List[ExtractedPageResponse]
