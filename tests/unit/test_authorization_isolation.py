"""Unit tests for Multi-Tenant Authorization Isolation and IDOR Protection."""

import uuid
import pytest
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)


def test_user_cannot_access_another_users_project_or_crawl():
    """Verifies strict server-side authorization enforcement across tenants (IDOR protection)."""
    client_a = TestClient(app)
    client_b = TestClient(app)
    client_unauth = TestClient(app)

    # User A setup
    email_a = f"usera_{uuid.uuid4().hex[:8]}@example.com"
    pwd = "Password123!"
    client_a.post("/api/v1/auth/register", json={"email": email_a, "password": pwd})
    token_a = client_a.post("/api/v1/auth/login", json={"email": email_a, "password": pwd}).json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # User B setup
    email_b = f"userb_{uuid.uuid4().hex[:8]}@example.com"
    client_b.post("/api/v1/auth/register", json={"email": email_b, "password": pwd})
    token_b = client_b.post("/api/v1/auth/login", json={"email": email_b, "password": pwd}).json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # User A creates Project A and Crawl A inside Project A
    proj_a_res = client_a.post("/api/v1/projects", json={"name": "Project A"}, headers=headers_a)
    proj_a_id = proj_a_res.json()["id"]

    crawl_a_res = client_a.post(
        "/api/v1/crawl",
        json={"url": "https://example.com", "project_id": proj_a_id},
        headers=headers_a,
    )
    crawl_a_id = crawl_a_res.json()["id"]

    # 1. User B attempts to access User A's Project -> HTTP 404
    user_b_get_proj = client_b.get(f"/api/v1/projects/{proj_a_id}", headers=headers_b)
    assert user_b_get_proj.status_code == 404

    # 2. User B attempts to access User A's Crawl Job -> HTTP 404
    user_b_get_crawl = client_b.get(f"/api/v1/crawl/{crawl_a_id}", headers=headers_b)
    assert user_b_get_crawl.status_code == 404

    # 3. Unauthenticated user attempts to access User A's Crawl Job -> HTTP 404
    unauth_get_crawl = client_unauth.get(f"/api/v1/crawl/{crawl_a_id}")
    assert unauth_get_crawl.status_code == 404
