"""Standardized Crawl Dataset Schema (Single Source of Truth).

Defines the unified data contract representing extracted website content, metadata,
statistics, and page hierarchies for consumption by Exporters, Frontend, and AI Agents.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse
from uuid import UUID, uuid4
from pydantic import BaseModel, Field


class PageDetail(BaseModel):
    """Standardized representation of a single crawled web page."""

    id: UUID
    url: str
    normalized_url: str
    status_code: int
    depth: int
    title: Optional[str] = None
    meta_description: Optional[str] = None
    headings: Dict[str, List[str]] = Field(default_factory=dict)
    paragraphs: List[str] = Field(default_factory=list)
    lists: List[List[str]] = Field(default_factory=list)
    tables: List[List[List[str]]] = Field(default_factory=list)
    images: List[Dict[str, Optional[str]]] = Field(default_factory=list)
    internal_links: List[Dict[str, Any]] = Field(default_factory=list)
    external_links: List[Dict[str, Any]] = Field(default_factory=list)
    response_time_ms: float = 0.0
    created_at: Optional[datetime] = None
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


from src.utils.status_classifier import ExtractionStatus, classify_extraction_status


class WebsiteInformation(BaseModel):
    """General website identity and seed information."""

    seed_url: str
    domain: str
    crawl_mode: str = "SINGLE"
    status: str = "COMPLETED"
    extraction_status: ExtractionStatus = ExtractionStatus.SUCCESS


class CrawlMetadata(BaseModel):
    """Execution parameters and timestamps."""

    job_id: UUID
    batch_id: Optional[UUID] = None
    max_depth: int
    max_pages: int
    render_js: bool
    created_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None


class CrawlStatistics(BaseModel):
    """Aggregated numerical metrics."""

    pages_crawled: int = 0
    failed_pages: int = 0
    total_images: int = 0
    total_links: int = 0
    total_duration_sec: float = 0.0


from src.utils.url_utils import build_website_structure_tree


class WebsiteSummary(BaseModel):
    """Textual executive summary of extracted features."""

    title: Optional[str] = None
    meta_description: Optional[str] = None
    total_pages_extracted: int = 0
    total_headings_found: int = 0
    total_tables_found: int = 0
    main_sections: List[str] = Field(default_factory=list)
    structure_tree: List[str] = Field(default_factory=list)


class StandardCrawlDataset(BaseModel):
    """Unified standardized output container for single and batch crawl jobs."""

    website_info: WebsiteInformation
    extraction_status: ExtractionStatus = ExtractionStatus.SUCCESS
    metadata: CrawlMetadata
    statistics: CrawlStatistics
    summary: WebsiteSummary
    pages: List[PageDetail] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    download_metadata: Dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def from_orm_models(
        cls,
        pages: List[Any],
        job: Any,
        stats: Optional[Any] = None,
        errors: Optional[List[str]] = None,
        warnings: Optional[List[str]] = None,
    ) -> "StandardCrawlDataset":
        """Constructs a StandardCrawlDataset instance from ORM entities."""
        domain_name = urlparse(job.seed_url).netloc.lower() if job.seed_url else "unknown"

        # Build PageDetail items
        page_details: List[PageDetail] = []
        total_headings = 0
        total_tables = 0
        first_title = None
        first_desc = None

        for p in pages:
            if not first_title and getattr(p, "title", None):
                first_title = p.title
            if not first_desc and getattr(p, "meta_description", None):
                first_desc = p.meta_description

            headings_map = getattr(p, "headings", {}) or {}
            for h_list in headings_map.values():
                total_headings += len(h_list)

            tables_list = getattr(p, "tables", []) or []
            total_tables += len(tables_list)

            images_data = []
            for img in getattr(p, "images", []):
                if isinstance(img, dict):
                    images_data.append(img)
                else:
                    images_data.append({"image_url": img.image_url, "alt_text": img.alt_text})

            internal_links_data = []
            external_links_data = []
            for link in getattr(p, "links", []):
                link_obj = {
                    "source_url": getattr(link, "source_url", getattr(p, "url", "")),
                    "target_url": getattr(link, "target_url", ""),
                    "anchor_text": getattr(link, "anchor_text", None),
                    "is_external": getattr(link, "is_external", False),
                }
                if getattr(link, "is_external", False):
                    external_links_data.append(link_obj)
                else:
                    internal_links_data.append(link_obj)

            detail = PageDetail(
                id=p.id,
                url=p.url,
                normalized_url=p.normalized_url,
                status_code=p.status_code,
                depth=p.depth,
                title=p.title,
                meta_description=p.meta_description,
                headings=headings_map,
                paragraphs=getattr(p, "paragraphs", []) or [],
                lists=getattr(p, "lists", []) or [],
                tables=tables_list,
                images=images_data,
                internal_links=internal_links_data,
                external_links=external_links_data,
                response_time_ms=getattr(p, "response_time_ms", 0.0) or 0.0,
                created_at=getattr(p, "created_at", None),
            )
            page_details.append(detail)

        job_status = getattr(job, "status", "COMPLETED")
        status_val = job_status.value if hasattr(job_status, "value") else str(job_status or "COMPLETED")

        job_mode = getattr(job, "crawl_mode", "SINGLE")
        mode_val = job_mode.value if hasattr(job_mode, "value") else str(job_mode or "SINGLE")

        ext_status = classify_extraction_status(pages=pages, job=job, errors=errors)

        seed_url_val = getattr(job, "seed_url", "") or ""
        domain_name = urlparse(seed_url_val).netloc.lower() if seed_url_val else "unknown"

        website_info = WebsiteInformation(
            seed_url=seed_url_val,
            domain=domain_name,
            crawl_mode=mode_val,
            status=status_val,
            extraction_status=ext_status,
        )

        job_id_val = getattr(job, "id", None) or uuid4()
        max_depth_val = getattr(job, "max_depth", None)
        max_pages_val = getattr(job, "max_pages", None)
        render_js_val = getattr(job, "render_js", None)

        metadata = CrawlMetadata(
            job_id=job_id_val,
            batch_id=getattr(job, "batch_id", None),
            max_depth=max_depth_val if max_depth_val is not None else 2,
            max_pages=max_pages_val if max_pages_val is not None else 50,
            render_js=render_js_val if render_js_val is not None else False,
            created_at=getattr(job, "created_at", None),
            finished_at=getattr(job, "finished_at", None),
        )

        statistics = CrawlStatistics(
            pages_crawled=getattr(stats, "pages_crawled", len(pages)) if stats else len(pages),
            failed_pages=getattr(stats, "failed_pages", 0) if stats else 0,
            total_images=getattr(stats, "total_images", sum(len(p.images) for p in page_details)) if stats else sum(len(p.images) for p in page_details),
            total_links=getattr(stats, "total_links", sum(len(p.internal_links) + len(p.external_links) for p in page_details)) if stats else sum(len(p.internal_links) + len(p.external_links) for p in page_details),
            total_duration_sec=getattr(stats, "total_duration_sec", 0.0) if stats else 0.0,
        )

        tree_lines, main_sections = build_website_structure_tree(
            urls=[p.url for p in page_details if p.url], seed_url=seed_url_val
        )

        summary = WebsiteSummary(
            title=first_title,
            meta_description=first_desc,
            total_pages_extracted=len(pages),
            total_headings_found=total_headings,
            total_tables_found=total_tables,
            main_sections=main_sections,
            structure_tree=tree_lines,
        )

        return cls(
            website_info=website_info,
            extraction_status=ext_status,
            metadata=metadata,
            statistics=statistics,
            summary=summary,
            pages=page_details,
            errors=errors or [],
            warnings=warnings or [],
            download_metadata={
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "exporter_version": "3.0.0",
            },
        )


class BatchMetadata(BaseModel):
    """Metadata tracking batch execution identity and timestamps."""

    batch_id: UUID
    created_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None


class BatchStatistics(BaseModel):
    """Aggregated metrics across all websites in a batch."""

    total_websites: int = 0
    successful_websites: int = 0
    failed_websites: int = 0
    total_pages: int = 0
    total_images: int = 0
    total_links: int = 0
    total_duration_sec: float = 0.0
    overall_status: str = "COMPLETED"


class BatchWebsiteItem(BaseModel):
    """Independent website crawl result record within a batch."""

    website_url: str
    status: str
    extraction_status: ExtractionStatus = ExtractionStatus.SUCCESS
    duration_sec: float = 0.0
    dataset: Optional[StandardCrawlDataset] = None
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class BatchSummary(BaseModel):
    """Executive summary of batch processing results."""

    total_websites_processed: int = 0
    total_pages_extracted: int = 0
    successful_websites_count: int = 0
    failed_websites_count: int = 0


class BatchDataset(BaseModel):
    """Unified multi-website batch crawl dataset container."""

    batch_metadata: BatchMetadata
    batch_statistics: BatchStatistics
    websites: List[BatchWebsiteItem] = Field(default_factory=list)
    batch_summary: BatchSummary
    download_metadata: Dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def from_batch_job(
        cls,
        batch_job: Any,
        website_items: List[BatchWebsiteItem],
        stats_dict: Optional[Dict[str, Any]] = None,
    ) -> "BatchDataset":
        """Constructs a BatchDataset instance from a BatchJob ORM entity and child site items."""
        b_stats = stats_dict or {}

        for item in website_items:
            if item.dataset:
                item.extraction_status = item.dataset.extraction_status
            else:
                item.extraction_status = classify_extraction_status(pages=[], job=batch_job, errors=item.errors)

        completed_cnt = sum(1 for item in website_items if item.status == "COMPLETED")
        failed_cnt = sum(1 for item in website_items if item.status == "FAILED")
        total_cnt = len(website_items)

        total_pages = sum(
            len(item.dataset.pages) if item.dataset and item.dataset.pages else 0
            for item in website_items
        )
        total_images = sum(
            item.dataset.statistics.total_images if item.dataset and item.dataset.statistics else 0
            for item in website_items
        )
        total_links = sum(
            item.dataset.statistics.total_links if item.dataset and item.dataset.statistics else 0
            for item in website_items
        )
        total_duration = sum(item.duration_sec for item in website_items)

        batch_meta = BatchMetadata(
            batch_id=batch_job.id,
            created_at=getattr(batch_job, "created_at", None),
            finished_at=getattr(batch_job, "finished_at", None),
        )

        status_str = (
            batch_job.status.value if hasattr(batch_job.status, "value") else str(batch_job.status)
        )

        batch_stats = BatchStatistics(
            total_websites=total_cnt,
            successful_websites=completed_cnt,
            failed_websites=failed_cnt,
            total_pages=b_stats.get("total_pages", total_pages),
            total_images=b_stats.get("total_images", total_images),
            total_links=b_stats.get("total_links", total_links),
            total_duration_sec=b_stats.get("total_duration_sec", round(total_duration, 2)),
            overall_status=status_str,
        )

        batch_sum = BatchSummary(
            total_websites_processed=total_cnt,
            total_pages_extracted=total_pages,
            successful_websites_count=completed_cnt,
            failed_websites_count=failed_cnt,
        )

        return cls(
            batch_metadata=batch_meta,
            batch_statistics=batch_stats,
            websites=website_items,
            batch_summary=batch_sum,
            download_metadata={
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "exporter_version": "3.0.0",
            },
        )

