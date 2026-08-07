import io
from typing import List, Optional, Tuple
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from src.application.services.exporters.base import BaseExporter
from src.db.models.crawl_job import CrawlJob
from src.db.models.page import ExtractedPage
from src.db.models.statistic import CrawlStatistic
from src.schemas.export import ExportFormat


def clean_pdf_text(text: Optional[str]) -> str:
    """Escapes XML entities (&, <, >) to ensure valid ReportLab Paragraph markup."""
    if not text:
        return ""
    s = str(text)
    # Remove control characters and escape XML entities
    s = "".join(ch for ch in s if ord(ch) >= 32 or ch in "\n\r\t")
    return escape(s)


class NumberedCanvas(canvas.Canvas):
    """Two-pass canvas to dynamically compute and render total page count & footers."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._saved_page_states: List[dict] = []

    def showPage(self) -> None:
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self) -> None:
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            super().showPage()
        super().save()

    def draw_page_number(self, page_count: int) -> None:
        if self._pageNumber == 1:
            return  # Skip cover page footer

        self.saveState()
        self.setFont("Helvetica", 9)
        self.setFillColor(colors.HexColor("#64748b"))

        # Footer divider line
        self.setStrokeColor(colors.HexColor("#e2e8f0"))
        self.setLineWidth(0.5)
        self.line(54, 36, letter[0] - 54, 36)

        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(letter[0] - 54, 22, page_str)
        self.drawString(54, 22, "Universal Website Data Extractor — Confidential Report")
        self.restoreState()


class PdfExporter(BaseExporter):
    """Strategy Exporter for professional PDF document generation."""

    @property
    def format_type(self) -> ExportFormat:
        return ExportFormat.PDF

    async def export(
        self,
        pages: List[ExtractedPage],
        job: CrawlJob,
        stats: Optional[CrawlStatistic] = None,
    ) -> Tuple[bytes, str, str]:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            leftMargin=54,
            rightMargin=54,
            topMargin=54,
            bottomMargin=54,
        )

        styles = getSampleStyleSheet()
        
        # Custom Typography Styles
        title_style = ParagraphStyle(
            "CoverTitle",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=26,
            leading=32,
            textColor=colors.HexColor("#0f172a"),
            alignment=0,
        )
        subtitle_style = ParagraphStyle(
            "CoverSubtitle",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=11,
            leading=15,
            textColor=colors.HexColor("#64748b"),
        )
        section_heading = ParagraphStyle(
            "SectionHeading",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=16,
            leading=20,
            textColor=colors.HexColor("#2563eb"),
            spaceBefore=14,
            spaceAfter=8,
        )
        page_title_style = ParagraphStyle(
            "PageTitle",
            parent=styles["Heading3"],
            fontName="Helvetica-Bold",
            fontSize=13,
            leading=16,
            textColor=colors.HexColor("#0f172a"),
        )
        body_style = ParagraphStyle(
            "Body",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=10,
            leading=14,
            textColor=colors.HexColor("#334155"),
        )
        code_style = ParagraphStyle(
            "CodeText",
            parent=styles["Code"],
            fontName="Courier",
            fontSize=8,
            leading=10,
            textColor=colors.HexColor("#2563eb"),
        )

        story = []

        # =====================================================================
        # 1. COVER PAGE
        # =====================================================================
        story.append(Spacer(1, 40))
        story.append(Paragraph("Website Data Extraction Report", title_style))
        story.append(Spacer(1, 10))
        story.append(Paragraph(f"Target URL: <font color='#2563eb'>{clean_pdf_text(job.seed_url)}</font>", subtitle_style))
        story.append(Spacer(1, 20))
        story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#2563eb"), spaceAfter=30))

        # Overview Table
        pages_count = len(pages)
        duration_str = f"{stats.total_duration_sec:.2f}s" if stats else "N/A"
        total_links = stats.total_links if stats else sum(len(getattr(p, "links", []) or []) for p in pages)
        total_images = stats.total_images if stats else sum(len(getattr(p, "images", []) or []) for p in pages)

        overview_data = [
            [Paragraph("<b>Job ID:</b>", body_style), Paragraph(clean_pdf_text(str(job.id)), code_style)],
            [Paragraph("<b>Status:</b>", body_style), Paragraph(f"<b>{clean_pdf_text(job.status)}</b>", body_style)],
            [Paragraph("<b>Pages Extracted:</b>", body_style), Paragraph(str(pages_count), body_style)],
            [Paragraph("<b>Total Links Discovered:</b>", body_style), Paragraph(str(total_links), body_style)],
            [Paragraph("<b>Total Images Discovered:</b>", body_style), Paragraph(str(total_images), body_style)],
            [Paragraph("<b>Crawl Duration:</b>", body_style), Paragraph(duration_str, body_style)],
            [Paragraph("<b>Created At:</b>", body_style), Paragraph(job.created_at.strftime("%Y-%m-%d %H:%M:%S UTC") if getattr(job, "created_at", None) is not None else "N/A", body_style)],
        ]

        overview_table = Table(overview_data, colWidths=[160, 340])
        overview_table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
                ("PADDING", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ])
        )
        story.append(overview_table)
        story.append(PageBreak())

        # =====================================================================
        # 2. TABLE OF CONTENTS / SUMMARY
        # =====================================================================
        story.append(Paragraph("Index of Extracted Pages", section_heading))
        story.append(Spacer(1, 10))

        toc_data = [[Paragraph("<b>#</b>", body_style), Paragraph("<b>Page Title</b>", body_style), Paragraph("<b>URL</b>", body_style), Paragraph("<b>Status</b>", body_style)]]
        for idx, p in enumerate(pages, 1):
            toc_data.append([
                Paragraph(str(idx), body_style),
                Paragraph(clean_pdf_text(p.title) or "Untitled", body_style),
                Paragraph(clean_pdf_text(p.url), code_style),
                Paragraph(f"{p.status_code} OK", body_style),
            ])

        toc_table = Table(toc_data, colWidths=[30, 150, 260, 60])
        toc_table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eff6ff")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#1e40af")),
                ("PADDING", (0, 0), (-1, -1), 6),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ])
        )
        story.append(toc_table)
        story.append(Spacer(1, 20))

        # =====================================================================
        # 3. PAGE DETAILS SECTIONS
        # =====================================================================
        story.append(Paragraph("Detailed Extracted Content", section_heading))
        story.append(Spacer(1, 10))

        for idx, p in enumerate(pages, 1):
            header_items = [
                Paragraph(f"{idx}. {clean_pdf_text(p.title) or 'Untitled Page'}", page_title_style),
                Paragraph(f"<b>URL:</b> <font color='#2563eb'>{clean_pdf_text(p.url)}</font> | <b>Depth:</b> {p.depth} | <b>Latency:</b> {p.response_time_ms}ms", body_style),
            ]
            story.append(KeepTogether(header_items))

            if p.meta_description:
                story.append(Spacer(1, 4))
                story.append(Paragraph(f"<i>Meta Description:</i> {clean_pdf_text(p.meta_description)}", body_style))

            if p.headings:
                story.append(Spacer(1, 6))
                story.append(Paragraph("<b>Headings:</b>", body_style))
                for level, txts in p.headings.items():
                    for t in txts[:5]:  # Limit top headings
                        story.append(Paragraph(f"• <b>[{clean_pdf_text(level.upper())}]</b> {clean_pdf_text(t)}", body_style))

            if p.paragraphs:
                story.append(Spacer(1, 6))
                story.append(Paragraph("<b>Sample Content:</b>", body_style))
                for para in p.paragraphs[:3]:  # Top paragraphs
                    story.append(Paragraph(f"“{clean_pdf_text(para)}”", body_style))

            story.append(Spacer(1, 10))
            story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cbd5e1"), spaceAfter=12))

        doc.build(story, canvasmaker=NumberedCanvas)
        pdf_bytes = buffer.getvalue()
        buffer.close()

        filename = self.generate_filename(job.seed_url, str(job.id), "pdf")
        return pdf_bytes, filename, "application/pdf"
