"""Unit tests for Security Headers and Rate Limiting Middlewares."""

import pytest
from fastapi.testclient import TestClient
from src.core.config import settings
from src.main import app

client = TestClient(app)


def test_security_headers_present():
    """Verifies standard OWASP security headers are attached to responses."""
    response = client.get("/")
    assert response.status_code == 200

    headers = response.headers
    assert headers.get("X-Frame-Options") == "DENY"
    assert headers.get("X-Content-Type-Options") == "nosniff"
    assert headers.get("X-XSS-Protection") == "1; mode=block"
    assert headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
    assert "Content-Security-Policy" in headers


def test_rate_limiting_enforcement(monkeypatch):
    """Verifies that exceeding client request limits triggers HTTP 429 Too Many Requests."""
    import uuid
    monkeypatch.setattr(settings, "RATE_LIMIT_PER_MINUTE", 3)
    monkeypatch.setattr(settings, "ENABLE_RATE_LIMITING", True)

    unique_ip = f"198.51.100.{uuid.uuid4().int % 200}"
    target_path = f"/api/v1/crawl/{uuid.uuid4()}"

    # First 3 requests to an API route should proceed to endpoint handler
    for i in range(3):
        res = client.get(target_path, headers={"X-Forwarded-For": unique_ip})
        assert res.status_code == 404

    # 4th request should trigger 429 Rate Limit Exceeded
    res = client.get(target_path, headers={"X-Forwarded-For": unique_ip})
    assert res.status_code == 429
    assert res.headers.get("Retry-After") == "60"

    data = res.json()
    assert data["status"] == 429
    assert data["error_type"] == "https://errors.websiteintelligence.dev/rate-limit-exceeded"
    assert "exceeded" in data["detail"]
