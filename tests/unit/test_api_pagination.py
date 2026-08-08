"""Unit tests for Standardized API Pagination and Metadata."""

import pytest
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)


def test_list_crawl_jobs_pagination():
    """Verifies GET /api/v1/crawl/jobs returns PaginatedResponse structure with PageMeta."""
    response = client.get("/api/v1/crawl/jobs?page=1&page_size=10")
    assert response.status_code == 200

    data = response.json()
    assert "data" in data
    assert "meta" in data
    meta = data["meta"]
    assert meta["page"] == 1
    assert meta["page_size"] == 10
    assert "total" in meta
    assert "total_pages" in meta
    assert "has_next" in meta
    assert "has_previous" in meta


def test_list_batch_jobs_pagination():
    """Verifies GET /api/v1/batch/list returns PaginatedResponse structure with PageMeta."""
    response = client.get("/api/v1/batch/list?page=1&page_size=5")
    assert response.status_code == 200

    data = response.json()
    assert "data" in data
    assert "meta" in data
    meta = data["meta"]
    assert meta["page"] == 1
    assert meta["page_size"] == 5
    assert "total" in meta
    assert "total_pages" in meta
