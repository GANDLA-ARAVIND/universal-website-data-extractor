from typing import Any, List, Optional, Tuple

from src.application.services.exporters.base import BaseExporter
from src.db.models.crawl_job import CrawlJob
from src.db.models.page import ExtractedPage
from src.db.models.statistic import CrawlStatistic
from src.schemas.export import ExportFormat


from src.schemas.dataset import StandardCrawlDataset


def format_single_dataset_markdown(dataset: StandardCrawlDataset, is_nested: bool = False) -> List[str]:
    """Renders a comprehensive 9-section report for a single website dataset in Markdown."""
    lines = []
    sub_heading = "###" if is_nested else "##"
    sub_sub_heading = "####" if is_nested else "###"

    # 1. Executive Summary
    lines.append(f"{sub_heading} 1. Executive Summary")
    lines.append(f"- **Extraction Outcome Status**: `{dataset.extraction_status}`")
    lines.append(f"- **Total Pages Extracted**: `{dataset.statistics.pages_crawled}`")
    lines.append(f"- **Failed Pages Count**: `{dataset.statistics.failed_pages}`")
    lines.append(f"- **Total Images Discovered**: `{dataset.statistics.total_images}`")
    lines.append(f"- **Total Hyperlinks Discovered**: `{dataset.statistics.total_links}`")
    lines.append(f"- **Total Execution Time**: `{dataset.statistics.total_duration_sec} seconds`")
    lines.append("\n---\n")

    # 2. Website Overview
    lines.append(f"{sub_heading} 2. Website Overview")
    lines.append(f"- **Website Title**: {dataset.summary.title or 'N/A'}")
    lines.append(f"- **Meta Description**: {dataset.summary.meta_description or 'N/A'}")
    lines.append(f"- **Target Domain**: `{dataset.website_info.domain}`")
    lines.append(f"- **Max Crawl Depth**: `{dataset.metadata.max_depth}`")
    lines.append(f"- **Total Headings**: `{dataset.summary.total_headings_found}`")
    lines.append(f"- **Total Tables**: `{dataset.summary.total_tables_found}`")
    if dataset.summary.main_sections:
        lines.append(f"- **Main Sections Discovered**: {', '.join([f'`{s}`' for s in dataset.summary.main_sections])}")
    lines.append("\n---\n")

    # 3. Website Structure
    lines.append(f"{sub_heading} 3. Website Structure Hierarchy")
    lines.append("```text")
    for line in dataset.summary.structure_tree:
        lines.append(line)
    lines.append("```")
    lines.append("\n---\n")

    # 4. Crawl Statistics
    lines.append(f"{sub_heading} 4. Detailed Aggregated Statistics")
    lines.append("| Metric | Value |")
    lines.append("| :--- | :--- |")
    lines.append(f"| Pages Crawled | `{dataset.statistics.pages_crawled}` |")
    lines.append(f"| Failed Pages | `{dataset.statistics.failed_pages}` |")
    lines.append(f"| Total Headings | `{dataset.summary.total_headings_found}` |")
    lines.append(f"| Total Tables | `{dataset.summary.total_tables_found}` |")
    lines.append(f"| Total Discovered Images | `{dataset.statistics.total_images}` |")
    lines.append(f"| Total Discovered Links | `{dataset.statistics.total_links}` |")
    lines.append("\n---\n")

    # 5. Page Index
    lines.append(f"{sub_heading} 5. Discovered Page Index")
    lines.append("| # | Title | URL | Status | Depth | Latency (ms) |")
    lines.append("| :--- | :--- | :--- | :--- | :--- | :--- |")
    for idx, p in enumerate(dataset.pages, 1):
        clean_title = (p.title or "Untitled").replace("|", "\\|")
        lines.append(f"| {idx} | {clean_title} | [{p.url}]({p.url}) | `{p.status_code}` | `{p.depth}` | `{p.response_time_ms}ms` |")
    lines.append("\n---\n")

    # 6. Detailed Page Information
    lines.append(f"{sub_heading} 6. Detailed Page Information")
    for idx, p in enumerate(dataset.pages, 1):
        lines.append(f"{sub_sub_heading} Page {idx}: {p.title or 'Untitled'}")
        lines.append(f"- **URL**: [{p.url}]({p.url})")
        lines.append(f"- **HTTP Status**: `{p.status_code}` | **Depth**: `{p.depth}` | **Latency**: `{p.response_time_ms}ms`")
        if p.meta_description:
            lines.append(f"- **Meta Description**: {p.meta_description}")

        if p.headings:
            lines.append(f"\n##### Headings")
            for level, txts in p.headings.items():
                for t in txts:
                    lines.append(f"- **[{level.upper()}]**: {t}")

        if p.paragraphs:
            lines.append(f"\n##### Paragraph Content")
            for para in p.paragraphs[:5]:
                lines.append(f"> {para}\n")

        if p.tables:
            lines.append(f"\n##### Extracted Tables ({len(p.tables)})")
            for t_idx, tbl in enumerate(p.tables, 1):
                if tbl:
                    lines.append(f"**Table {t_idx}:**")
                    lines.append("| " + " | ".join([str(c) for c in tbl[0]]) + " |")
                    lines.append("| " + " | ".join(["---"] * len(tbl[0])) + " |")
                    for row in tbl[1:5]:
                        lines.append("| " + " | ".join([str(c) for c in row]) + " |")

        if p.images:
            lines.append(f"\n##### Image Assets ({len(p.images)})")
            for img in p.images[:5]:
                alt = img.get("alt_text") if isinstance(img, dict) else getattr(img, "alt_text", None)
                src = img.get("image_url") if isinstance(img, dict) else getattr(img, "image_url", "")
                lines.append(f"- ![Alt: {alt or 'Image'}]({src}) - `{src}`")

        lines.append("\n")

    lines.append("---\n")

    # 7. Errors & Warnings
    lines.append(f"{sub_heading} 7. Execution Errors & Warnings")
    if dataset.errors or dataset.warnings:
        for err in dataset.errors:
            lines.append(f"- 🔴 **Error**: {err}")
        for warn in dataset.warnings:
            lines.append(f"- ⚠️ **Warning**: {warn}")
    else:
        lines.append("No execution errors or warnings recorded.")
    lines.append("\n---\n")

    # 8. Technical Appendix
    lines.append(f"{sub_heading} 8. Technical Appendix")
    lines.append(f"- **Generated At**: `{dataset.download_metadata.get('generated_at', 'N/A')}`")
    lines.append(f"- **Exporter Version**: `{dataset.download_metadata.get('exporter_version', '3.0.0')}`")
    lines.append(f"- **Schema Standard**: `StandardCrawlDataset v3.0`")
    lines.append("\n---\n")
    return lines


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
        dataset = StandardCrawlDataset.from_orm_models(pages, job, stats)
        lines = [
            f"# Website Data Extraction Report: {dataset.website_info.domain}",
            f"- **Target Seed URL**: `{dataset.website_info.seed_url}`",
            f"- **Crawl Status**: `{dataset.website_info.status}`",
            f"- **Job ID**: `{dataset.metadata.job_id}`",
            f"- **Created At**: `{dataset.metadata.created_at or 'N/A'}`",
            f"- **Total Duration**: `{dataset.statistics.total_duration_sec}s`",
            "\n---\n",
        ]
        lines.extend(format_single_dataset_markdown(dataset, is_nested=False))

        md_str = "\n".join(lines)
        filename = self.generate_filename(job.seed_url, str(job.id), "md")
        return md_str.encode("utf-8"), filename, "text/markdown"

    async def export_batch_dataset(
        self,
        batch_dataset: Any,
    ) -> Tuple[bytes, str, str]:
        """Generates Markdown document payload for a BatchDataset."""
        lines = [
            "# Multi-Website Batch Crawl Executive Report",
            f"- **Batch ID**: `{batch_dataset.batch_metadata.batch_id}`",
            f"- **Overall Status**: `{batch_dataset.batch_statistics.overall_status}`",
            f"- **Total Websites**: `{batch_dataset.batch_statistics.total_websites}` | **Successful**: `{batch_dataset.batch_statistics.successful_websites}` | **Failed**: `{batch_dataset.batch_statistics.failed_websites}`",
            f"- **Total Pages Extracted**: `{batch_dataset.batch_statistics.total_pages}` | **Total Duration**: `{batch_dataset.batch_statistics.total_duration_sec}s`",
            "\n---\n",
        ]

        for idx, site in enumerate(batch_dataset.websites, 1):
            lines.append(f"# Website {idx}: [{site.website_url}]({site.website_url})")
            lines.append(f"- **Status**: `{site.status}` | **Extraction Outcome**: `{site.extraction_status}` | **Duration**: `{site.duration_sec}s`")
            if site.errors:
                lines.append(f"- **Errors**: {'; '.join(site.errors)}")
            lines.append("\n")

            if site.dataset:
                site_lines = format_single_dataset_markdown(site.dataset, is_nested=True)
                lines.extend(site_lines)
            else:
                lines.append("Full website dataset unavailable due to crawl failure.")
                lines.append("\n---\n")

        md_str = "\n".join(lines)
        short_id = str(batch_dataset.batch_metadata.batch_id)[:8]
        filename = f"batch_export_{short_id}.md"
        return md_str.encode("utf-8"), filename, "text/markdown"


