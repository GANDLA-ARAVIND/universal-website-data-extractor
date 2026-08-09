"""AI Context Builder & Sanitizer Module.

Extracts, cleans, formats, and selects high-signal semantic content from
StandardCrawlDataset / BatchDataset / ExtractedPage models.
Omits noise like timing benchmarks, HTTP metadata, raw link arrays, and image dimensions.
"""

from typing import Any, Dict, List, Optional
from src.schemas.dataset import StandardCrawlDataset, BatchDataset, PageDetail
from src.db.models.page import ExtractedPage


class ContextBuilder:
    """Builds clean, purposeful context strings and structured semantic blocks for LLM consumption."""

    @staticmethod
    def build_dataset_context(
        dataset: StandardCrawlDataset,
        max_pages: Optional[int] = None,
        max_paragraphs_per_page: int = 10,
    ) -> str:
        """Serializes a StandardCrawlDataset into a clean Markdown representation for Direct AI analysis."""
        lines: List[str] = []
        seed_url = getattr(dataset.website_info, 'seed_url', None) or getattr(dataset, 'seed_url', 'Unknown Target')
        domain = getattr(dataset.website_info, 'domain', None) or seed_url
        pages_crawled = getattr(dataset.statistics, 'pages_crawled', len(dataset.pages))

        lines.append(f"# Website Crawl Dataset: {domain}")
        lines.append(f"Seed URL: {seed_url}")
        lines.append(f"Total Extracted Pages: {pages_crawled}\n")

        pages = dataset.pages
        if max_pages and len(pages) > max_pages:
            pages = pages[:max_pages]

        for idx, page in enumerate(pages, 1):
            lines.append(f"## Page {idx}: {page.title or 'Untitled Page'}")
            lines.append(f"URL: {page.url}")
            if page.meta_description:
                lines.append(f"Meta Description: {page.meta_description}")

            # Headings Hierarchy
            if page.headings:
                lines.append("\n### Headings Structure:")
                headings_dict = page.headings if isinstance(page.headings, dict) else {}
                for tag in ["h1", "h2", "h3", "h4", "h5", "h6"]:
                    h_list = headings_dict.get(tag, [])
                    if h_list:
                        for h_text in h_list:
                            lines.append(f"- [{tag.upper()}] {h_text}")

            # Paragraph Text
            if page.paragraphs:
                lines.append("\n### Content Paragraphs:")
                paras = page.paragraphs[:max_paragraphs_per_page] if isinstance(page.paragraphs, list) else []
                for p in paras:
                    if p and len(p.strip()) > 5:
                        lines.append(f"> {p.strip()}")

            # Structured Data Tables
            tables = getattr(page, 'tables', None) or getattr(page, 'data_tables', [])
            if tables:
                lines.append("\n### Extracted Data Tables:")
                for tbl_idx, table in enumerate(tables, 1):
                    if isinstance(table, dict):
                        headers = table.get("headers", [])
                        rows = table.get("rows", [])
                    elif isinstance(table, list):
                        headers = table[0] if table else []
                        rows = table[1:] if len(table) > 1 else []
                    else:
                        continue
                    lines.append(f"**Table {tbl_idx}:**")
                    if headers:
                        lines.append(" | ".join([str(h) for h in headers]))
                        lines.append("-" * 30)
                    for r in rows[:5]:
                        lines.append(" | ".join([str(c) for c in r]))

            lines.append("\n" + "-" * 40 + "\n")

        return "\n".join(lines)

    @staticmethod
    def build_batch_dataset_context(
        batch_dataset: BatchDataset,
        max_sites: Optional[int] = 10,
    ) -> str:
        """Serializes a multi-website BatchDataset into clean text context."""
        batch_id = getattr(batch_dataset.batch_metadata, 'batch_id', 'Unknown Batch')
        total_websites = getattr(batch_dataset.batch_statistics, 'total_websites', len(batch_dataset.websites))
        total_pages = getattr(batch_dataset.batch_statistics, 'total_pages', 0)

        lines: List[str] = []
        lines.append(f"# Multi-Website Batch Dataset #{batch_id}")
        lines.append(f"Total Target Websites: {total_websites}")
        lines.append(f"Total Pages Crawled: {total_pages}\n")

        sites = batch_dataset.websites
        if max_sites and len(sites) > max_sites:
            sites = sites[:max_sites]

        for s_idx, site_item in enumerate(sites, 1):
            lines.append("=" * 50)
            lines.append(f"TARGET WEBSITE #{s_idx}: {site_item.website_url}")
            lines.append("=" * 50)
            if site_item.dataset:
                site_ctx = ContextBuilder.build_dataset_context(site_item.dataset, max_pages=5)
                lines.append(site_ctx)
            else:
                lines.append(f"Status: {site_item.status} | Errors: {', '.join(site_item.errors)}")
            lines.append("\n")

        return "\n".join(lines)

    @staticmethod
    def build_page_context(page: ExtractedPage) -> str:
        """Serializes a single ExtractedPage ORM model into a clean text block."""
        lines: List[str] = []
        lines.append(f"Page Title: {page.title or 'Untitled Page'}")
        lines.append(f"URL: {page.url}")
        if page.meta_description:
            lines.append(f"Meta Description: {page.meta_description}")

        if page.headings:
            lines.append("\nHeadings:")
            for tag in ["h1", "h2", "h3", "h4", "h5", "h6"]:
                h_list = page.headings.get(tag, []) if isinstance(page.headings, dict) else []
                if h_list:
                    for h_text in h_list:
                        lines.append(f"- [{tag.upper()}] {h_text}")

        if page.paragraphs:
            lines.append("\nParagraphs:")
            paras = page.paragraphs if isinstance(page.paragraphs, list) else []
            for p in paras:
                if p and len(p.strip()) > 5:
                    lines.append(p.strip())

        if page.data_tables:
            lines.append("\nData Tables:")
            tables = page.data_tables if isinstance(page.data_tables, list) else []
            for tbl in tables:
                headers = tbl.get("headers", [])
                rows = tbl.get("rows", [])
                if headers:
                    lines.append("Headers: " + ", ".join([str(h) for h in headers]))
                for r in rows[:3]:
                    lines.append("Row: " + ", ".join([str(c) for c in r]))

        return "\n".join(lines)
