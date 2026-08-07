from abc import ABC, abstractmethod
from typing import List, Optional, Tuple
from urllib.parse import urlparse

from src.db.models.crawl_job import CrawlJob
from src.db.models.page import ExtractedPage
from src.db.models.statistic import CrawlStatistic
from src.schemas.export import ExportFormat


class BaseExporter(ABC):
    """Abstract Strategy interface for dataset exporters."""

    @property
    @abstractmethod
    def format_type(self) -> ExportFormat:
        """The export format enum handled by this strategy."""
        pass

    @abstractmethod
    async def export(
        self,
        pages: List[ExtractedPage],
        job: CrawlJob,
        stats: Optional[CrawlStatistic] = None,
    ) -> Tuple[bytes, str, str]:
        """
        Generates the export file payload.
        Returns:
            Tuple of (raw_bytes, filename, media_type)
        """
        pass

    def generate_filename(self, seed_url: str, job_id_str: str, ext: str) -> str:
        """Utility helper to generate a domain & date-aware export filename."""
        try:
            domain = urlparse(seed_url).hostname or "export"
            clean_domain = domain.replace(".", "_").replace("-", "_")
        except Exception:
            clean_domain = "export"
        short_id = job_id_str[:8]
        return f"{clean_domain}_export_{short_id}.{ext}"
