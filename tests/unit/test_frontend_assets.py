"""Unit tests for Frontend Static SPA Assets & API Client mapping (Phase 5)."""

import pytest
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)


def test_frontend_spa_mounting_and_assets():
    """Verifies that the static frontend SPA is served at /app and includes all assets."""
    response = client.get("/app/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "<title>Website Intelligence Platform</title>" in response.text
    assert '<script src="api.js"></script>' in response.text
    assert '<script src="components.js"></script>' in response.text
    assert '<script src="app.js"></script>' in response.text


def test_frontend_javascript_client_files():
    """Verifies that api.js, components.js, and app.js static files exist and are served."""
    api_res = client.get("/app/api.js")
    assert api_res.status_code == 200
    assert "window.API =" in api_res.text
    assert "BASE_URL = '/api/v1'" in api_res.text
    assert "/auth/register" in api_res.text
    assert "/projects" in api_res.text
    assert "/crawl" in api_res.text
    assert "/batch" in api_res.text

    components_res = client.get("/app/components.js")
    assert components_res.status_code == 200
    assert "window.UI =" in components_res.text

    app_res = client.get("/app/app.js")
    assert app_res.status_code == 200
    assert "startSingleCrawlWorkflow" in app_res.text
    assert "startBatchCrawlWorkflow" in app_res.text
    assert "loadAnalysisWorkspace" in app_res.text
