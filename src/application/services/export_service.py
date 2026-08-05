"""ExportService Result Generator.

Formats extracted page datasets into JSON, CSV, and Markdown downloadable formats.
"""

import csv
import io
import json
import uuid
from typing import List, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import ExportException
from src.db.models.page import ExtractedPage
from src.db.repositories.page_repository import PageRepository
from src.schemas.export import ExportFormatEnum


class ExportService:
    """Service handling multi-format dataset exports (JSON, CSV, Markdown)."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.page_repo = PageRepository(session)

    async def generate_export(
        self, job_id: uuid.UUID, export_format: ExportFormatEnum
    ) -> Tuple[bytes, str, str]:
        """Generates formatted file payload for a crawl job's extracted dataset.

        Args:
            job_id (uuid.UUID): Job UUID.
            export_format (ExportFormatEnum): Target format enum (json, csv, markdown).

        Returns:
            Tuple[bytes, str, str]: (Raw file bytes, Filename, HTTP Content-Type header).

        Raises:
            ExportException: If format generation fails.
        """
        pages = await self.page_repo.get_all_pages_for_job(job_id)
        if not pages:
            raise ExportException(
                f"No extracted pages found for job '{job_id}' to export."
            )

        if export_format == ExportFormatEnum.JSON:
            return self._export_json(job_id, pages)
        elif export_format == ExportFormatEnum.CSV:
            return self._export_csv(job_id, pages)
        elif export_format == ExportFormatEnum.MARKDOWN:
            return self._export_markdown(job_id, pages)

        raise ExportException(f"Unsupported export format '{export_format}'.")

    def _export_json(
        self, job_id: uuid.UUID, pages: List[ExtractedPage]
    ) -> Tuple[bytes, str, str]:
        """Generates JSON formatted export."""
        data = []
        for p in pages:
            data.append({
                "id": str(p.id),
                "job_id": str(p.job_id),
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
                "links_count": len(p.links),
                "images_count": len(p.images),
                "links": [
                    {
                        "source": link.source_url,
                        "target": link.target_url,
                        "anchor": link.anchor_text,
                        "external": link.is_external,
                    }
                    for link in p.links
                ],
                "images": [
                    {"url": img.image_url, "alt": img.alt_text}
                    for img in p.images
                ],
                "response_time_ms": p.response_time_ms,
                "fetched_at": p.created_at.isoformat(),
            })

        json_bytes = json.dumps(data, indent=2, ensure_ascii=False).encode("utf-8")
        filename = f"crawl_export_{job_id}.json"
        return json_bytes, filename, "application/json"

    def _export_csv(
        self, job_id: uuid.UUID, pages: List[ExtractedPage]
    ) -> Tuple[bytes, str, str]:
        """Generates CSV formatted export."""
        output = io.StringIO()
        writer = csv.writer(output)

        # Write CSV Header
        writer.writerow([
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
        ])

        for p in pages:
            writer.writerow([
                p.url,
                p.normalized_url,
                p.status_code,
                p.depth,
                p.title or "",
                p.meta_description or "",
                len(p.links),
                len(p.images),
                p.response_time_ms,
                p.created_at.isoformat(),
            ])

        csv_bytes = output.getvalue().encode("utf-8")
        filename = f"crawl_export_{job_id}.csv"
        return csv_bytes, filename, "text/csv"

    def _export_markdown(
        self, job_id: uuid.UUID, pages: List[ExtractedPage]
    ) -> Tuple[bytes, str, str]:
        """Generates Markdown formatted documentation export."""
        md_lines = [
            f"# Web Crawl Dataset Export",
            f"**Job ID**: `{job_id}`",
            f"**Total Pages**: `{len(pages)}`",
            "",
            "---",
            "",
        ]

        for idx, p in enumerate(pages, 1):
            md_lines.append(f"## Page {idx}: {p.title or p.url}")
            md_lines.append(f"- **URL**: {p.url}")
            md_lines.append(f"- **Status Code**: `{p.status_code}` | **Depth**: `{p.depth}` | **Latency**: `{p.response_time_ms}ms`")
            if p.meta_description:
                md_lines.append(f"- **Meta Description**: {p.meta_description}")

            if p.headings:
                md_lines.append("\n### Headings")
                for tag, text_list in p.headings.items():
                    for txt in text_list:
                        md_lines.append(f"  - **{tag.upper()}**: {txt}")

            if p.paragraphs:
                md_lines.append("\n### Content Sample")
                for para in p.paragraphs[:5]:  # Include top 5 paragraphs
                    md_lines.append(f"> {para}\n")

            if p.images:
                md_lines.append("\n### Images")
                for img in p.images[:10]:
                    alt = f" (Alt: {img.alt_text})" if img.alt_text else ""
                    md_lines.append(f"- ![{img.alt_text or 'Image'}]({img.image_url}){alt}")

            md_lines.append("\n---\n")

        md_bytes = "\n".join(md_lines).encode("utf-8")
        filename = f"crawl_export_{job_id}.md"
        return md_bytes, filename, "text/markdown"
