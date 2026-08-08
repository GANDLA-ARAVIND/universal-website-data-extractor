import json
from typing import Any, List, Optional, Tuple

from src.application.services.exporters.base import BaseExporter
from src.db.models.crawl_job import CrawlJob
from src.db.models.page import ExtractedPage
from src.db.models.statistic import CrawlStatistic
from src.schemas.export import ExportFormat


class JsonExporter(BaseExporter):
    """Strategy Exporter for JSON dataset output."""

    @property
    def format_type(self) -> ExportFormat:
        return ExportFormat.JSON

    async def export(
        self,
        pages: List[ExtractedPage],
        job: CrawlJob,
        stats: Optional[CrawlStatistic] = None,
    ) -> Tuple[bytes, str, str]:
        export_data = {
            "job_id": str(job.id),
            "seed_url": job.seed_url,
            "crawled_at": job.created_at.isoformat() if job.created_at else None,
            "total_pages": len(pages),
            "pages": [
                {
                    "url": p.url,
                    "normalized_url": p.normalized_url,
                    "status_code": p.status_code,
                    "depth": p.depth,
                    "title": p.title,
                    "meta_description": p.meta_description,
                    "headings": p.headings,
                    "paragraphs": p.paragraphs,
                    "lists": p.lists,
                    "tables": p.tables,
                    "links_count": len(p.links) if p.links else 0,
                    "images_count": len(p.images) if p.images else 0,
                    "links": [
                        {
                            "target_url": l.target_url,
                            "anchor_text": l.anchor_text,
                            "is_external": l.is_external,
                        }
                        for l in (p.links or [])
                    ],
                    "images": [
                        {"image_url": i.image_url, "alt_text": i.alt_text}
                        for i in (p.images or [])
                    ],
                    "response_time_ms": p.response_time_ms,
                    "fetched_at": p.created_at.isoformat() if p.created_at else None,
                }
                for p in pages
            ],
        }

        json_str = json.dumps(export_data, indent=2, ensure_ascii=False)
        filename = self.generate_filename(job.seed_url, str(job.id), "json")
        return json_str.encode("utf-8"), filename, "application/json"

    async def export_batch_dataset(
        self,
        batch_dataset: Any,
    ) -> Tuple[bytes, str, str]:
        """Generates JSON payload for a BatchDataset."""
        data = batch_dataset.model_dump(mode="json")
        json_str = json.dumps(data, indent=2, ensure_ascii=False)
        short_id = str(batch_dataset.batch_metadata.batch_id)[:8]
        filename = f"batch_export_{short_id}.json"
        return json_str.encode("utf-8"), filename, "application/json"

