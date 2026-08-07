from typing import List, Optional, Tuple

from src.application.services.exporters.base import BaseExporter
from src.db.models.crawl_job import CrawlJob
from src.db.models.page import ExtractedPage
from src.db.models.statistic import CrawlStatistic
from src.schemas.export import ExportFormat


class MarkdownExporter(BaseExporter):
    """Strategy Exporter for Markdown dataset document output."""

    @property
    def format_type(self) -> ExportFormat:
        return ExportFormat.MARKDOWN

    async def export(
        self,
        pages: List[ExtractedPage],
        job: CrawlJob,
        stats: Optional[CrawlStatistic] = None,
    ) -> Tuple[bytes, str, str]:
        lines = [
            f"# Crawl Data Export: {job.seed_url}",
            f"- **Job ID**: {job.id}",
            f"- **Total Pages**: {len(pages)}",
            f"- **Crawled At**: {job.created_at.isoformat() if job.created_at else 'N/A'}",
            "\n---\n",
        ]

        for p in pages:
            lines.append(f"## Page: {p.title or 'Untitled'}")
            lines.append(f"- **URL**: [{p.url}]({p.url})")
            lines.append(f"- **Status Code**: `{p.status_code}` | **Depth**: `{p.depth}` | **Latency**: `{p.response_time_ms}ms`")
            if p.meta_description:
                lines.append(f"- **Description**: {p.meta_description}")

            if p.headings:
                lines.append("\n### Headings")
                for level, txts in p.headings.items():
                    for t in txts:
                        prefix = "#" * int(level[1]) if len(level) > 1 and level[1].isdigit() else "###"
                        lines.append(f"{prefix} {t}")

            if p.paragraphs:
                lines.append("\n### Paragraphs")
                for para in p.paragraphs:
                    lines.append(f"> {para}\n")

            if p.lists:
                lines.append("\n### Lists")
                for sublist in p.lists:
                    for item in sublist:
                        lines.append(f"- {item}")
                    lines.append("")

            if p.images:
                lines.append("\n### Images")
                for img in p.images:
                    lines.append(f"![{img.alt_text or 'Image'}]({img.image_url})")

            lines.append("\n---\n")

        md_str = "\n".join(lines)
        filename = self.generate_filename(job.seed_url, str(job.id), "md")
        return md_str.encode("utf-8"), filename, "text/markdown"
