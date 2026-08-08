"""Common Pydantic Schemas for API Standardization."""

from typing import Generic, List, Optional, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")


class PageMeta(BaseModel):
    """Standard pagination metadata."""

    page: int = Field(..., ge=1, description="Current page number (1-indexed).")
    page_size: int = Field(..., ge=1, le=100, description="Items limit per page.")
    total: int = Field(..., ge=0, description="Total matching items in collection.")
    total_pages: int = Field(..., ge=0, description="Total computed pages.")
    has_next: bool = Field(..., description="True if subsequent page exists.")
    has_previous: bool = Field(..., description="True if preceding page exists.")


class PaginatedResponse(BaseModel, Generic[T]):
    """Standardized generic API response wrapper for paginated collections."""

    data: List[T] = Field(..., description="Items payload for current page.")
    meta: PageMeta = Field(..., description="Pagination metadata.")
