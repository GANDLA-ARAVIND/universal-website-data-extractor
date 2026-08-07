from typing import Dict, Optional

from src.application.services.exporters.base import BaseExporter
from src.application.services.exporters.csv_exporter import CsvExporter
from src.application.services.exporters.docx_exporter import DocxExporter
from src.application.services.exporters.json_exporter import JsonExporter
from src.application.services.exporters.markdown_exporter import MarkdownExporter
from src.application.services.exporters.pdf_exporter import PdfExporter
from src.application.services.exporters.xlsx_exporter import XlsxExporter
from src.core.exceptions import ExportException
from src.schemas.export import ExportFormat


class ExporterRegistry:
    """Registry pattern holding format-to-strategy mappings."""

    def __init__(self) -> None:
        self._exporters: Dict[ExportFormat, BaseExporter] = {}
        # Register default strategies
        self.register(JsonExporter())
        self.register(CsvExporter())
        self.register(MarkdownExporter())
        self.register(PdfExporter())
        self.register(DocxExporter())
        self.register(XlsxExporter())

    def register(self, exporter: BaseExporter) -> None:
        """Register a new exporter strategy."""
        self._exporters[exporter.format_type] = exporter

    def get(self, format_type: ExportFormat) -> BaseExporter:
        """Retrieve an exporter strategy by format type."""
        exporter = self._exporters.get(format_type)
        if not exporter:
            raise ExportException(f"Unsupported export format strategy: '{format_type.value}'")
        return exporter


_registry_instance: Optional[ExporterRegistry] = None


def get_exporter_registry() -> ExporterRegistry:
    """Singleton getter for ExporterRegistry."""
    global _registry_instance
    if _registry_instance is None:
        _registry_instance = ExporterRegistry()
    return _registry_instance
