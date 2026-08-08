"""Unit tests for API Filtering and Sorting parameters."""

import pytest
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)


def test_list_crawl_jobs_filtering():
    """Verifies query parameters filtering on GET /api/v1/crawl/jobs."""
    response = client.get("/api/v1/crawl/jobs?status=COMPLETED&crawl_mode=SINGLE&search=example")
    assert response.status_code == 200

    data = response.json()
    assert "data" in data
    assert isinstance(data["data"], list)


def test_list_batch_jobs_filtering():
    """Verifies query parameters filtering on GET /api/v1/batch/list."""
    response = client.get("/api/v1/batch/list?status=PENDING&sort_by=created_at&sort_order=asc")
    assert response.status_code == 200

    data = response.json()
    assert "data" in data
    assert isinstance(data["data"], list)
