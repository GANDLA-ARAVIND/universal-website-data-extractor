from enum import Enum
from pydantic import BaseModel, Field


class ExportFormat(str, Enum):
    JSON = "json"
    CSV = "csv"
    MARKDOWN = "markdown"
    PDF = "pdf"
    DOCX = "docx"
    XLSX = "xlsx"


# Backward compatibility alias
ExportFormatEnum = ExportFormat


class ExportRequest(BaseModel):
    format: ExportFormat = Field(
        default=ExportFormat.JSON,
        description="Desired export file format (json, csv, markdown, pdf, docx, xlsx)",
    )
