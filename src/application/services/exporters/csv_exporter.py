import csv
import io
from typing import Any, List, Optional, Tuple

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

    async def export_batch_dataset(
        self,
        batch_dataset: Any,
    ) -> Tuple[bytes, str, str]:
        """Generates CSV tabular output for a BatchDataset."""
        output = io.StringIO()
        writer = csv.writer(output)

        writer.writerow(["Website URL", "Status", "Duration (s)", "Pages Extracted", "Errors"])
        for site in batch_dataset.websites:
            pg_cnt = len(site.dataset.pages) if site.dataset and site.dataset.pages else 0
            err_str = "; ".join(site.errors) if site.errors else ""
            writer.writerow([site.website_url, site.status, site.duration_sec, pg_cnt, err_str])

        writer.writerow([])
        writer.writerow([
            "Website Domain", "URL", "Normalized URL", "Status Code", "Depth",
            "Title", "Meta Description", "Links Count", "Images Count", "Response Time (ms)"
        ])

        for site in batch_dataset.websites:
            if site.dataset and site.dataset.pages:
                for p in site.dataset.pages:
                    writer.writerow([
                        site.dataset.website_info.domain,
                        p.url,
                        p.normalized_url,
                        p.status_code,
                        p.depth,
                        p.title or "",
                        p.meta_description or "",
                        len(p.internal_links) + len(p.external_links),
                        len(p.images),
                        p.response_time_ms,
                    ])

        csv_str = output.getvalue()
        short_id = str(batch_dataset.batch_metadata.batch_id)[:8]
        filename = f"batch_export_{short_id}.csv"
        return csv_str.encode("utf-8"), filename, "text/csv"

