"""Unit tests for StandardCrawlDataset schema and factory methods."""

import uuid
from datetime import datetime, timezone
from src.db.models.crawl_job import CrawlJob, CrawlMode, CrawlStatus
from src.db.models.page import ExtractedPage
from src.db.models.statistic import CrawlStatistic
from src.schemas.dataset import StandardCrawlDataset


def test_standard_crawl_dataset_from_orm_models() -> None:
    """Verifies construction of StandardCrawlDataset from ORM entities."""
    job_id = uuid.uuid4()
    job = CrawlJob(
        id=job_id,
        seed_url="https://example.com",
        status=CrawlStatus.COMPLETED,
        crawl_mode=CrawlMode.SINGLE,
        max_depth=2,
        max_pages=20,
        render_js=False,
        created_at=datetime.now(timezone.utc),
    )

    page = ExtractedPage(
        id=uuid.uuid4(),
        job_id=job_id,
        url="https://example.com/about",
        normalized_url="https://example.com/about",
        status_code=200,
        depth=1,
        title="About Page",
        meta_description="About description",
        headings={"h1": ["About Title"]},
        paragraphs=["Sample paragraph"],
        lists=[["Item 1"]],
        tables=[[["H1", "H2"], ["C1", "C2"]]],
        response_time_ms=120.5,
    )

    stats = CrawlStatistic(
        job_id=job_id,
        pages_crawled=1,
        failed_pages=0,
        total_images=0,
        total_links=0,
        total_duration_sec=1.5,
    )

    dataset = StandardCrawlDataset.from_orm_models(
        pages=[page],
        job=job,
        stats=stats,
        warnings=["Test warning"],
    )

    assert dataset.website_info.domain == "example.com"
    assert dataset.website_info.status == "COMPLETED"
    assert dataset.metadata.job_id == job_id
    assert dataset.statistics.pages_crawled == 1
    assert dataset.summary.total_pages_extracted == 1
    assert dataset.summary.total_headings_found == 1
    assert dataset.summary.total_tables_found == 1
    assert len(dataset.pages) == 1
    assert dataset.pages[0].title == "About Page"
    assert dataset.warnings == ["Test warning"]


def test_batch_dataset_from_batch_job() -> None:
    """Verifies construction of BatchDataset from BatchJob and child site items."""
    from src.db.models.batch_job import BatchJob
    from src.schemas.dataset import BatchDataset, BatchWebsiteItem

    batch_id = uuid.uuid4()
    batch = BatchJob(
        id=batch_id,
        status=CrawlStatus.COMPLETED,
        total_urls=2,
        created_at=datetime.now(timezone.utc),
    )

    job_id = uuid.uuid4()
    job = CrawlJob(
        id=job_id,
        seed_url="https://site1.com",
        status=CrawlStatus.COMPLETED,
        crawl_mode=CrawlMode.BATCH,
        created_at=datetime.now(timezone.utc),
    )
    page = ExtractedPage(
        id=uuid.uuid4(),
        job_id=job_id,
        url="https://site1.com",
        normalized_url="https://site1.com",
        status_code=200,
        depth=0,
        title="Site 1",
    )
    site1_dataset = StandardCrawlDataset.from_orm_models(pages=[page], job=job)

    item1 = BatchWebsiteItem(
        website_url="https://site1.com",
        status="COMPLETED",
        duration_sec=2.0,
        dataset=site1_dataset,
    )
    item2 = BatchWebsiteItem(
        website_url="https://site2.com",
        status="FAILED",
        duration_sec=0.5,
        dataset=None,
        errors=["Network failure"],
    )

    batch_dataset = BatchDataset.from_batch_job(
        batch_job=batch,
        website_items=[item1, item2],
        stats_dict={"total_pages": 1, "total_images": 0, "total_links": 0, "total_duration_sec": 2.5},
    )

    assert batch_dataset.batch_metadata.batch_id == batch_id
    assert batch_dataset.batch_statistics.total_websites == 2
    assert batch_dataset.batch_statistics.successful_websites == 1
    assert batch_dataset.batch_statistics.failed_websites == 1
    assert len(batch_dataset.websites) == 2
    assert batch_dataset.websites[0].dataset is not None
    assert batch_dataset.websites[1].dataset is None
    assert batch_dataset.websites[1].errors == ["Network failure"]
    assert batch_dataset.batch_summary.successful_websites_count == 1

