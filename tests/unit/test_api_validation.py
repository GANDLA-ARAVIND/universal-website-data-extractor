"""Unit tests for API Pydantic Request Validation and Error Contracts."""

import pytest
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)


def test_single_crawl_invalid_url_ssrf_rejection():
    """Verifies single crawl POST endpoint rejects private/SSRF URLs with HTTP 400 and RFC 7807 error format."""
    payload = {
        "url": "http://127.0.0.1/admin",
        "max_depth": 2,
        "max_pages": 50,
    }
    response = client.post("/api/v1/crawl", json=payload)
    assert response.status_code == 400
    data = response.json()
    assert data["status"] == 400
    assert data["type"] == "InvalidURLException"
    assert "restricted" in data["detail"].lower() or "private" in data["detail"].lower()


def test_batch_crawl_invalid_urls_rejection():
    """Verifies batch crawl POST endpoint rejects invalid/private URLs in batch list."""
    payload = {
        "urls": ["https://example.com", "http://10.0.0.1/secret"],
        "max_depth": 2,
        "max_pages": 50,
    }
    response = client.post("/api/v1/batch", json=payload)
    assert response.status_code == 400
    data = response.json()
    assert data["status"] == 400
    assert data["type"] == "InvalidURLException"


def test_crawl_request_numeric_bounds_validation():
    """Verifies Pydantic numeric boundary validation (e.g. max_depth > 10 returns 422)."""
    payload = {
        "url": "https://example.com",
        "max_depth": 999,  # Violates le=10 constraint
        "max_pages": 50,
    }
    response = client.post("/api/v1/crawl", json=payload)
    assert response.status_code == 422
