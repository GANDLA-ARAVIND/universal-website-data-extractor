"""Unit tests for Projects Workspace CRUD API."""

import uuid
import pytest
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)


def test_projects_crud_workflow():
    """Verifies Project creation, retrieval, listing, updating, and deletion."""
    email = f"proj_user_{uuid.uuid4().hex[:8]}@example.com"
    pwd = "Password123!"

    # Register & Login
    client.post("/api/v1/auth/register", json={"email": email, "password": pwd})
    login_res = client.post("/api/v1/auth/login", json={"email": email, "password": pwd})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create Project
    create_res = client.post(
        "/api/v1/projects",
        json={"name": "SaaS Competitors", "description": "Tracking feature pages"},
        headers=headers,
    )
    assert create_res.status_code == 201
    proj_data = create_res.json()
    project_id = proj_data["id"]
    assert proj_data["name"] == "SaaS Competitors"

    # 2. Get Project
    get_res = client.get(f"/api/v1/projects/{project_id}", headers=headers)
    assert get_res.status_code == 200
    assert get_res.json()["id"] == project_id

    # 3. List Projects
    list_res = client.get("/api/v1/projects?page=1&page_size=10", headers=headers)
    assert list_res.status_code == 200
    assert len(list_res.json()["data"]) >= 1

    # 4. Update Project
    update_res = client.put(
        f"/api/v1/projects/{project_id}",
        json={"name": "Updated SaaS Benchmarks"},
        headers=headers,
    )
    assert update_res.status_code == 200
    assert update_res.json()["name"] == "Updated SaaS Benchmarks"

    # 5. Delete Project
    del_res = client.delete(f"/api/v1/projects/{project_id}", headers=headers)
    assert del_res.status_code == 204

    # Verify 404 after deletion
    get_after_del = client.get(f"/api/v1/projects/{project_id}", headers=headers)
    assert get_after_del.status_code == 404
