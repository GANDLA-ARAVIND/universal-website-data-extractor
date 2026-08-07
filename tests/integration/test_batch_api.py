"""Integration Tests for Batch Crawl REST API Endpoints."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.batch_job import BatchJob
from src.db.models.crawl_job import CrawlJob, CrawlMode, CrawlStatus
from src.db.models.page import ExtractedPage


@pytest.mark.asyncio
async def test_initiate_batch_crawl_endpoint(async_client: AsyncClient) -> None:
    """Verifies POST /api/v1/batch creates batch and child crawl jobs."""
    payload = {
        "urls": ["https://site1.com", "https://site2.com", "https://site1.com"],  # includes duplicate
        "max_depth": 1,
        "max_pages": 5,
    }
    response = await async_client.post("/api/v1/batch", json=payload)
    assert response.status_code == 202
    data = response.json()
    assert "id" in data
    assert data["status"] in ("PENDING", "RUNNING")
    assert data["total_urls"] == 2  # Deduplicated from 3 to 2
    assert len(data["jobs"]) == 2


@pytest.mark.asyncio
async def test_initiate_batch_crawl_invalid_url(async_client: AsyncClient) -> None:
    """Verifies rejection of invalid URLs prior to batch creation."""
    payload = {"urls": ["not-a-valid-url"]}
    response = await async_client.post("/api/v1/batch", json=payload)
    assert response.status_code == 400
    assert "Invalid URL" in response.json()["detail"]


@pytest.mark.asyncio
async def test_batch_status_statistics_and_retry(
    async_client: AsyncClient, db_session: AsyncSession
) -> None:
    """Verifies status retrieval, aggregated metrics, and failed job retry endpoint."""
    batch = BatchJob(status=CrawlStatus.RUNNING, total_urls=2)
    db_session.add(batch)
    await db_session.flush()

    job_completed = CrawlJob(
        batch_id=batch.id,
        seed_url="https://site-ok.com",
        crawl_mode=CrawlMode.BATCH,
        status=CrawlStatus.COMPLETED,
        max_depth=1,
        max_pages=5,
    )
    job_failed = CrawlJob(
        batch_id=batch.id,
        seed_url="https://site-fail.com",
        crawl_mode=CrawlMode.BATCH,
        status=CrawlStatus.FAILED,
        max_depth=1,
        max_pages=5,
    )
    db_session.add(job_completed)
    db_session.add(job_failed)
    await db_session.commit()

    # 1. GET /batch/{id}
    res_status = await async_client.get(f"/api/v1/batch/{batch.id}")
    assert res_status.status_code == 200
    s_data = res_status.json()
    assert s_data["total_urls"] == 2
    assert s_data["completed_urls"] == 1
    assert s_data["failed_urls"] == 1
    assert s_data["progress_percentage"] == 100.0

    # 2. GET /batch/{id}/statistics
    res_stats = await async_client.get(f"/api/v1/batch/{batch.id}/statistics")
    assert res_stats.status_code == 200
    stat_data = res_stats.json()
    assert stat_data["total_websites"] == 2
    assert stat_data["completed_websites"] == 1
    assert stat_data["failed_websites"] == 1

    # 3. POST /batch/{id}/retry
    res_retry = await async_client.post(f"/api/v1/batch/{batch.id}/retry")
    assert res_retry.status_code == 202
    retry_data = res_retry.json()
    assert retry_data["status"] == "RUNNING"


@pytest.mark.asyncio
async def test_batch_export_all_formats(
    async_client: AsyncClient, db_session: AsyncSession
) -> None:
    """Verifies batch multi-website export generation across JSON, CSV, MD, PDF, DOCX, XLSX."""
    batch = BatchJob(status=CrawlStatus.COMPLETED, total_urls=1)
    db_session.add(batch)
    await db_session.flush()

    job = CrawlJob(
        batch_id=batch.id,
        seed_url="https://example-batch.com",
        crawl_mode=CrawlMode.BATCH,
        status=CrawlStatus.COMPLETED,
        max_depth=1,
        max_pages=5,
    )
    db_session.add(job)
    await db_session.flush()

    page = ExtractedPage(
        job_id=job.id,
        url="https://example-batch.com/about",
        normalized_url="https://example-batch.com/about",
        status_code=200,
        depth=1,
        title="Batch About",
        meta_description="Sample description",
        headings={"h1": ["Batch Heading"]},
        paragraphs=["Sample paragraph"],
        response_time_ms=100.0,
    )
    db_session.add(page)
    await db_session.commit()

    for fmt in ("json", "csv", "markdown", "pdf", "docx", "xlsx"):
        res = await async_client.post(
            f"/api/v1/batch/{batch.id}/export", json={"format": fmt}
        )
        assert res.status_code == 200, f"Failed for format {fmt}"
        assert "attachment; filename=" in res.headers["content-disposition"]
