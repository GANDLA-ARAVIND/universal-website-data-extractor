"""Integration tests for Crawl REST API endpoints."""

import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.crawl_job import CrawlJob, CrawlStatus
from src.db.models.page import ExtractedPage


@pytest.mark.asyncio
async def test_health_check(async_client: AsyncClient) -> None:
    """Verifies system health check endpoint."""
    response = await async_client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"


@pytest.mark.asyncio
async def test_initiate_crawl_success(async_client: AsyncClient) -> None:
    """Verifies POST /api/v1/crawl initiates background crawl job."""
    payload = {
        "url": "https://news.ycombinator.com",
        "max_depth": 2,
        "max_pages": 10,
        "render_js": False,
    }
    response = await async_client.post("/api/v1/crawl", json=payload)
    assert response.status_code == 202
    data = response.json()
    assert "id" in data
    assert data["seed_url"] == "https://news.ycombinator.com/"
    assert data["status"] == "PENDING" or data["status"] == "RUNNING"


@pytest.mark.asyncio
async def test_initiate_crawl_invalid_url(async_client: AsyncClient) -> None:
    """Verifies POST /api/v1/crawl rejects non-HTTP URLs with 422/400 validation error."""
    payload = {"url": "ftp://invalid-scheme.com"}
    response = await async_client.post("/api/v1/crawl", json=payload)
    assert response.status_code in (400, 422)


@pytest.mark.asyncio
async def test_get_crawl_status_not_found(async_client: AsyncClient) -> None:
    """Verifies GET /api/v1/crawl/{job_id} returns 404 for missing jobs."""
    random_id = str(uuid.uuid4())
    response = await async_client.get(f"/api/v1/crawl/{random_id}")
    assert response.status_code == 404
    assert response.json()["type"] == "CrawlJobNotFoundException"


@pytest.mark.asyncio
async def test_get_crawl_results_and_export(
    async_client: AsyncClient, db_session: AsyncSession
) -> None:
    """Verifies retrieval of paginated results and file exports."""
    # Seed test job and page in DB
    job = CrawlJob(
        seed_url="https://example.com",
        status=CrawlStatus.COMPLETED,
        max_depth=1,
        max_pages=5,
    )
    db_session.add(job)
    await db_session.flush()

    page = ExtractedPage(
        job_id=job.id,
        url="https://example.com/about",
        normalized_url="https://example.com/about",
        status_code=200,
        depth=1,
        title="About Us",
        meta_description="Sample description",
        headings={"h1": ["About Us"]},
        paragraphs=["Sample paragraph"],
        response_time_ms=120.5,
    )
    db_session.add(page)
    await db_session.commit()

    # 1. Test GET /results
    res_response = await async_client.get(f"/api/v1/crawl/{job.id}/results")
    assert res_response.status_code == 200
    res_data = res_response.json()
    assert res_data["total"] == 1
    assert res_data["data"][0]["title"] == "About Us"

    # 2. Test GET /statistics
    stat_response = await async_client.get(f"/api/v1/crawl/{job.id}/statistics")
    assert stat_response.status_code == 200
    assert stat_response.json()["job_id"] == str(job.id)

    # 3. Test POST /export JSON
    export_response = await async_client.post(
        f"/api/v1/crawl/{job.id}/export", json={"format": "json"}
    )
    assert export_response.status_code == 200
    assert "application/json" in export_response.headers["content-type"]
    assert "attachment; filename=" in export_response.headers["content-disposition"]
