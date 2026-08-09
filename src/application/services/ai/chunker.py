"""Semantic Chunker Module for RAG Pipeline.

Splits ExtractedPage content into structured semantic chunks preserving
heading hierarchy context, source page title, and URL metadata.
"""

from typing import Any, Dict, List, Optional
from src.core.config import settings
from src.db.models.page import ExtractedPage


class Chunker:
    """Semantic document chunking engine preserving heading paths and structural metadata."""

    @staticmethod
    def chunk_page(
        page: ExtractedPage,
        chunk_size: int = 1000,
        chunk_overlap: int = 150,
    ) -> List[Dict[str, Any]]:
        """Splits an ExtractedPage ORM model into metadata-rich text chunks."""
        chunks: List[Dict[str, Any]] = []
        page_title = page.title or "Untitled Page"
        url = page.url
        page_id = page.id
        job_id = page.job_id

        paragraphs = page.paragraphs if isinstance(page.paragraphs, list) else []
        headings = page.headings if isinstance(page.headings, dict) else {}

        current_heading_path = "Main Section"
        h_main = headings.get("h1", []) or headings.get("h2", [])
        if h_main and len(h_main) > 0:
            current_heading_path = h_main[0]

        # Accumulate text blocks with heading context
        text_blocks: List[str] = []

        if headings:
            all_headings = []
            for tag in ["h1", "h2", "h3", "h4", "h5", "h6"]:
                for h in headings.get(tag, []):
                    all_headings.append(f"[{tag.upper()}] {h}")
            if all_headings:
                text_blocks.append("Headings: " + " | ".join(all_headings))

        for p in paragraphs:
            if p and len(p.strip()) > 5:
                text_blocks.append(p.strip())

        # Include tabular data in chunk context
        tables = getattr(page, 'tables', None) or getattr(page, 'data_tables', [])
        if tables:
            tables_list = tables if isinstance(tables, list) else []
            for t_idx, tbl in enumerate(tables_list, 1):
                if isinstance(tbl, dict):
                    headers = tbl.get("headers", [])
                    rows = tbl.get("rows", [])
                elif isinstance(tbl, list):
                    headers = tbl[0] if tbl else []
                    rows = tbl[1:] if len(tbl) > 1 else []
                else:
                    continue
                tbl_str = f"[Table {t_idx}] "
                if headers:
                    tbl_str += "Headers: " + ", ".join([str(h) for h in headers]) + ". "
                for r in rows[:3]:
                    tbl_str += "Row: " + ", ".join([str(c) for c in r]) + "; "
                text_blocks.append(tbl_str)

        if not text_blocks:
            text_blocks.append(f"Page Title: {page_title}. URL: {url}.")

        # Slotted chunk sliding window
        current_chunk_text = ""
        chunk_idx = 0

        for block in text_blocks:
            prefix = f"[{page_title} > {current_heading_path}]\n"
            candidate = current_chunk_text + ("\n\n" if current_chunk_text else "") + block

            if len(candidate) > chunk_size and current_chunk_text:
                full_text = prefix + current_chunk_text
                chunks.append({
                    "job_id": job_id,
                    "page_id": page_id,
                    "url": url,
                    "page_title": page_title,
                    "heading_path": current_heading_path,
                    "chunk_index": chunk_idx,
                    "text": full_text,
                    "char_count": len(full_text),
                })
                chunk_idx += 1
                # Overlap tail calculation
                current_chunk_text = current_chunk_text[-chunk_overlap:] + "\n\n" + block
            else:
                current_chunk_text = candidate

        if current_chunk_text:
            full_text = f"[{page_title} > {current_heading_path}]\n" + current_chunk_text
            chunks.append({
                "job_id": job_id,
                "page_id": page_id,
                "url": url,
                "page_title": page_title,
                "heading_path": current_heading_path,
                "chunk_index": chunk_idx,
                "text": full_text,
                "char_count": len(full_text),
            })

        return chunks
