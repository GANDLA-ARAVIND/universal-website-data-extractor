import csv
import io
from typing import List, Optional, Tuple

from src.application.services.exporters.base import BaseExporter
from src.db.models.crawl_job import CrawlJob
from src.db.models.page import ExtractedPage
from src.db.models.statistic import CrawlStatistic
from src.schemas.export import ExportFormat


class CsvExporter(BaseExporter):
    """Strategy Exporter for CSV tabular output."""

    @property
    def format_type(self) -> ExportFormat:
        return ExportFormat.CSV

    async def export(
        self,
        pages: List[ExtractedPage],
        job: CrawlJob,
        stats: Optional[CrawlStatistic] = None,
    ) -> Tuple[bytes, str, str]:
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(
            [
                "URL",
                "Normalized URL",
                "Status Code",
                "Depth",
                "Title",
                "Meta Description",
                "Links Count",
                "Images Count",
                "Response Time (ms)",
                "Fetched At",
            ]
        )

        for p in pages:
            writer.writerow(
                [
                    p.url,
                    p.normalized_url,
                    p.status_code,
                    p.depth,
                    p.title or "",
                    p.meta_description or "",
                    len(p.links) if p.links else 0,
                    len(p.images) if p.images else 0,
                    p.response_time_ms,
                    p.created_at.isoformat() if p.created_at else "",
                ]
            )

        csv_str = output.getvalue()
        filename = self.generate_filename(job.seed_url, str(job.id), "csv")
        return csv_str.encode("utf-8"), filename, "text/csv"
