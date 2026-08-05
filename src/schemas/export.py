"""Pydantic schemas for result export formats and requests."""

import enum
from pydantic import BaseModel, Field


class ExportFormatEnum(str, enum.Enum):
    """Supported result export file formats."""

    JSON = "json"
    CSV = "csv"
    MARKDOWN = "markdown"


class ExportRequest(BaseModel):
    """Payload to request export generation for a crawl job."""

    format: ExportFormatEnum = Field(
        default=ExportFormatEnum.JSON,
        description="Target export format (json, csv, markdown).",
    )
