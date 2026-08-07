import io
from typing import List, Optional, Tuple

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt, RGBColor

from src.application.services.exporters.base import BaseExporter
from src.db.models.crawl_job import CrawlJob
from src.db.models.page import ExtractedPage
from src.db.models.statistic import CrawlStatistic
from src.schemas.export import ExportFormat


class DocxExporter(BaseExporter):
    """Strategy Exporter for professional Microsoft Word (.docx) document generation."""

    @property
    def format_type(self) -> ExportFormat:
        return ExportFormat.DOCX

    async def export(
        self,
        pages: List[ExtractedPage],
        job: CrawlJob,
        stats: Optional[CrawlStatistic] = None,
    ) -> Tuple[bytes, str, str]:
        doc = Document()

        # Set Margins
        sections = doc.sections
        for section in sections:
            section.top_margin = Inches(0.75)
            section.bottom_margin = Inches(0.75)
            section.left_margin = Inches(0.75)
            section.right_margin = Inches(0.75)

        # Base Typography Styles
        normal_style = doc.styles["Normal"]
        normal_style.font.name = "Calibri"
        normal_style.font.size = Pt(11)
        normal_style.font.color.rgb = RGBColor(0x33, 0x41, 0x55)

        # =====================================================================
        # 1. DOCUMENT HEADER & SUMMARY TABLE
        # =====================================================================
        title_p = doc.add_paragraph()
        title_run = title_p.add_run("Website Data Extraction Report")
        title_run.font.name = "Calibri"
        title_run.font.size = Pt(24)
        title_run.font.bold = True
        title_run.font.color.rgb = RGBColor(0x0F, 0x17, 0x2A)

        subtitle_p = doc.add_paragraph()
        sub_run = subtitle_p.add_run(f"Target URL: {job.seed_url}")
        sub_run.font.size = Pt(12)
        sub_run.font.color.rgb = RGBColor(0x25, 0x63, 0xEB)
        sub_run.font.bold = True

        doc.add_paragraph().paragraph_format.space_after = Pt(12)

        # Overview Table
        table = doc.add_table(rows=6, cols=2)
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        table.autofit = False

        duration_str = f"{stats.total_duration_sec:.2f}s" if stats else "N/A"
        total_links = stats.total_links if stats else sum(len(p.links or []) for p in pages)
        total_images = stats.total_images if stats else sum(len(p.images or []) for p in pages)

        row_data = [
            ("Job ID", str(job.id)),
            ("Job Status", str(job.status)),
            ("Pages Extracted", str(len(pages))),
            ("Discovered Links", str(total_links)),
            ("Discovered Images", str(total_images)),
            ("Crawl Runtime", duration_str),
        ]

        for i, (k, v) in enumerate(row_data):
            row = table.rows[i]
            row.cells[0].paragraphs[0].add_run(k).bold = True
            row.cells[1].paragraphs[0].add_run(v)
            row.cells[0].width = Inches(2.0)
            row.cells[1].width = Inches(4.5)

        doc.add_page_break()

        # =====================================================================
        # 2. EXTRACTED PAGES CONTENT
        # =====================================================================
        h1 = doc.add_heading("Extracted Web Content", level=1)
        h1.style.font.color.rgb = RGBColor(0x25, 0x63, 0xEB)

        for idx, p in enumerate(pages, 1):
            h2 = doc.add_heading(f"{idx}. {p.title or 'Untitled Page'}", level=2)
            h2.style.font.color.rgb = RGBColor(0x0F, 0x17, 0x2A)

            meta_p = doc.add_paragraph()
            meta_p.add_run(f"URL: ").bold = True
            url_run = meta_p.add_run(p.url)
            url_run.font.color.rgb = RGBColor(0x25, 0x63, 0xEB)
            meta_p.add_run(f" | Status: {p.status_code} | Depth: {p.depth} | Latency: {p.response_time_ms}ms")

            if p.meta_description:
                desc_p = doc.add_paragraph()
                desc_p.add_run("Meta Description: ").bold = True
                desc_p.add_run(p.meta_description).italic = True

            if p.headings:
                doc.add_heading("Headings", level=3)
                for level, txts in p.headings.items():
                    for t in txts:
                        doc.add_paragraph(f"[{level.upper()}] {t}", style="List Bullet")

            if p.paragraphs:
                doc.add_heading("Content Paragraphs", level=3)
                for para in p.paragraphs[:5]:  # Top 5 paragraphs
                    doc.add_paragraph(para)

            if p.tables:
                doc.add_heading("Parsed Data Tables", level=3)
                for tbl_idx, tbl_data in enumerate(p.tables, 1):
                    if not tbl_data:
                        continue
                    num_rows = len(tbl_data)
                    num_cols = max(len(r) for r in tbl_data) if num_rows > 0 else 0
                    if num_cols == 0:
                        continue

                    doc_table = doc.add_table(rows=num_rows, cols=num_cols)
                    doc_table.alignment = WD_TABLE_ALIGNMENT.CENTER
                    for r_idx, row in enumerate(tbl_data):
                        for c_idx, val in enumerate(row):
                            if c_idx < num_cols:
                                cell_p = doc_table.rows[r_idx].cells[c_idx].paragraphs[0]
                                run = cell_p.add_run(str(val))
                                if r_idx == 0:
                                    run.bold = True

            doc.add_paragraph().paragraph_format.space_after = Pt(14)

        buffer = io.BytesIO()
        doc.save(buffer)
        docx_bytes = buffer.getvalue()
        buffer.close()

        filename = self.generate_filename(job.seed_url, str(job.id), "docx")
        return (
            docx_bytes,
            filename,
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
