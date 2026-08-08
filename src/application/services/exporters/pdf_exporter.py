import io
from typing import Any, List, Optional, Tuple
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
from src.schemas.dataset import StandardCrawlDataset


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


def build_single_dataset_pdf_story(dataset: StandardCrawlDataset) -> List[Any]:
    """Constructs Platypus story flowables for a full 9-section single website PDF report."""
    styles = getSampleStyleSheet()

    cover_title_style = ParagraphStyle(
        "PDFCoverTitle",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=22,
        leading=26,
        textColor=colors.HexColor("#0F172A"),
        alignment=0,
    )
    h1_style = ParagraphStyle(
        "PDFH1",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=14,
        leading=18,
        textColor=colors.HexColor("#2563EB"),
        spaceBefore=14,
        spaceAfter=8,
    )
    h2_style = ParagraphStyle(
        "PDFH2",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=15,
        textColor=colors.HexColor("#0F172A"),
        spaceBefore=10,
        spaceAfter=6,
    )
    body_style = ParagraphStyle(
        "PDFBody",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#334155"),
    )
    code_style = ParagraphStyle(
        "PDFCode",
        parent=styles["Code"],
        fontName="Courier",
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#1e293b"),
        backColor=colors.HexColor("#f8fafc"),
        borderColor=colors.HexColor("#e2e8f0"),
        borderWidth=0.5,
        borderPadding=6,
        spaceBefore=6,
        spaceAfter=10,
    )

    story: List[Any] = []

    # 1. Cover Header
    story.append(Paragraph(f"Website Extraction Report: {clean_pdf_text(dataset.website_info.domain)}", cover_title_style))
    story.append(Spacer(1, 10))

    meta_table_data = [
        ["Target Seed URL:", clean_pdf_text(dataset.website_info.seed_url)],
        ["Crawl Status:", clean_pdf_text(dataset.website_info.status)],
        ["Job ID:", str(dataset.metadata.job_id)],
        ["Created At:", str(dataset.metadata.created_at or "N/A")],
        ["Total Duration:", f"{dataset.statistics.total_duration_sec}s"],
    ]
    t_meta = Table(meta_table_data, colWidths=[130, 390])
    t_meta.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor("#0F172A")),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(t_meta)
    story.append(Spacer(1, 15))

    # 2. Executive Summary
    story.append(Paragraph("1. Executive Summary", h1_style))
    exec_data = [
        ["Metric", "Value"],
        ["Total Pages Extracted", str(dataset.statistics.pages_crawled)],
        ["Failed Pages Count", str(dataset.statistics.failed_pages)],
        ["Total Images Discovered", str(dataset.statistics.total_images)],
        ["Total Hyperlinks Discovered", str(dataset.statistics.total_links)],
        ["Total Crawl Duration", f"{dataset.statistics.total_duration_sec} sec"],
    ]
    t_exec = Table(exec_data, colWidths=[260, 260])
    t_exec.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (1, 0), colors.HexColor("#2563EB")),
        ('TEXTCOLOR', (0, 0), (1, 0), colors.white),
        ('FONTNAME', (0, 0), (1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(t_exec)
    story.append(Spacer(1, 15))

    # 3. Website Overview
    story.append(Paragraph("2. Website Overview", h1_style))
    story.append(Paragraph(f"<b>Website Title:</b> {clean_pdf_text(dataset.summary.title or 'N/A')}", body_style))
    story.append(Spacer(1, 4))
    story.append(Paragraph(f"<b>Meta Description:</b> {clean_pdf_text(dataset.summary.meta_description or 'N/A')}", body_style))
    story.append(Spacer(1, 4))
    story.append(Paragraph(f"<b>Target Domain:</b> {clean_pdf_text(dataset.website_info.domain)} | <b>Max Depth:</b> {dataset.metadata.max_depth}", body_style))
    if dataset.summary.main_sections:
        story.append(Spacer(1, 4))
        sections_str = ", ".join(dataset.summary.main_sections)
        story.append(Paragraph(f"<b>Main Sections Discovered:</b> {clean_pdf_text(sections_str)}", body_style))
    story.append(Spacer(1, 15))

    # 4. Website Structure
    story.append(Paragraph("3. Website Structure Hierarchy", h1_style))
    tree_text = "<br/>".join([clean_pdf_text(line).replace(" ", "&nbsp;") for line in dataset.summary.structure_tree])
    story.append(Paragraph(tree_text, code_style))
    story.append(Spacer(1, 15))

    # 5. Page Index
    story.append(Paragraph("4. Discovered Page Index", h1_style))
    idx_data = [["#", "Title", "URL", "Status", "Depth", "Latency"]]
    for idx, p in enumerate(dataset.pages[:25], 1):
        idx_data.append([
            str(idx),
            clean_pdf_text(p.title or "Untitled")[:25],
            clean_pdf_text(p.url)[:35],
            str(p.status_code),
            str(p.depth),
            f"{p.response_time_ms:.0f}ms",
        ])
    t_idx = Table(idx_data, colWidths=[20, 120, 240, 45, 45, 50])
    t_idx.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#0F172A")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    story.append(t_idx)
    story.append(Spacer(1, 15))

    # 6. Detailed Page Information
    story.append(Paragraph("5. Detailed Page Information", h1_style))
    for idx, p in enumerate(dataset.pages[:10], 1):
        page_header = [
            Paragraph(f"<b>Page {idx}: {clean_pdf_text(p.title or 'Untitled')}</b>", h2_style),
            Paragraph(f"<b>URL:</b> <font color='#2563eb'>{clean_pdf_text(p.url)}</font> | <b>Status:</b> {p.status_code} | <b>Depth:</b> {p.depth} | <b>Latency:</b> {p.response_time_ms:.1f}ms", body_style),
        ]
        story.append(KeepTogether(page_header))

        if p.meta_description:
            story.append(Spacer(1, 3))
            story.append(Paragraph(f"<i>Description:</i> {clean_pdf_text(p.meta_description)}", body_style))

        if p.headings:
            story.append(Spacer(1, 4))
            for level, txts in p.headings.items():
                for t in txts[:3]:
                    story.append(Paragraph(f"• <b>[{clean_pdf_text(level.upper())}]</b> {clean_pdf_text(t)}", body_style))

        if p.paragraphs:
            story.append(Spacer(1, 4))
            for para in p.paragraphs[:2]:
                story.append(Paragraph(f"“{clean_pdf_text(para)}”", body_style))

        story.append(Spacer(1, 8))
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cbd5e1"), spaceAfter=8))

    # 7. Errors & Warnings
    story.append(Paragraph("6. Errors & Warnings", h1_style))
    if dataset.errors or dataset.warnings:
        for err in dataset.errors:
            story.append(Paragraph(f"• <font color='#dc2626'><b>[ERROR]</b></font> {clean_pdf_text(err)}", body_style))
        for warn in dataset.warnings:
            story.append(Paragraph(f"• <font color='#d97706'><b>[WARNING]</b></font> {clean_pdf_text(warn)}", body_style))
    else:
        story.append(Paragraph("No execution errors or warnings recorded.", body_style))

    story.append(Spacer(1, 15))

    # 8. Technical Appendix
    story.append(Paragraph("7. Technical Appendix", h1_style))
    app_data = [
        ["Generated Timestamp:", str(dataset.download_metadata.get("generated_at", "N/A"))],
        ["Exporter Version:", str(dataset.download_metadata.get("exporter_version", "3.0.0"))],
        ["Schema Contract:", "StandardCrawlDataset v3.0"],
    ]
    t_app = Table(app_data, colWidths=[150, 370])
    t_app.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
    ]))
    story.append(t_app)

    return story


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
        dataset = StandardCrawlDataset.from_orm_models(pages, job, stats)
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            leftMargin=36,
            rightMargin=36,
            topMargin=36,
            bottomMargin=45,
        )

        story = build_single_dataset_pdf_story(dataset)

        doc.build(story, canvasmaker=NumberedCanvas)
        pdf_bytes = buffer.getvalue()
        buffer.close()

        filename = self.generate_filename(job.seed_url, str(job.id), "pdf")
        return pdf_bytes, filename, "application/pdf"

    async def export_batch_dataset(
        self,
        batch_dataset: Any,
    ) -> Tuple[bytes, str, str]:
        """Generates PDF document payload for a BatchDataset."""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            leftMargin=36,
            rightMargin=36,
            topMargin=36,
            bottomMargin=45,
        )

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "BatchTitleStyle",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=22,
            leading=26,
            textColor=colors.HexColor("#0F172A"),
            alignment=0,
        )

        story: List[Any] = []
        story.append(Paragraph("Multi-Website Batch Crawl Executive Report", title_style))
        story.append(Spacer(1, 10))

        summary_data = [
            ["Batch ID", str(batch_dataset.batch_metadata.batch_id)],
            ["Overall Status", batch_dataset.batch_statistics.overall_status],
            ["Total Websites", str(batch_dataset.batch_statistics.total_websites)],
            ["Successful / Failed", f"{batch_dataset.batch_statistics.successful_websites} / {batch_dataset.batch_statistics.failed_websites}"],
            ["Total Pages Extracted", str(batch_dataset.batch_statistics.total_pages)],
            ["Total Execution Duration", f"{batch_dataset.batch_statistics.total_duration_sec}s"],
        ]
        sum_table = Table(summary_data, colWidths=[150, 370])
        sum_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor("#0f172a")),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        story.append(sum_table)
        story.append(Spacer(1, 20))
        story.append(PageBreak())

        for idx, site in enumerate(batch_dataset.websites, 1):
            if site.dataset:
                site_story = build_single_dataset_pdf_story(site.dataset)
                story.extend(site_story)
                story.append(PageBreak())

        doc.build(story, canvasmaker=NumberedCanvas)
        pdf_bytes = buffer.getvalue()
        buffer.close()

        short_id = str(batch_dataset.batch_metadata.batch_id)[:8]
        filename = f"batch_export_{short_id}.pdf"
        return pdf_bytes, filename, "application/pdf"
