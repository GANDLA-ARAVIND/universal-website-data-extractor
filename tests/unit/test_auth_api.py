"""Unit tests for User Registration, Login, Logout, and Identity endpoints."""

import uuid
import pytest
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)


def test_user_registration_and_login_flow():
    """Verifies complete registration, login, profile check, and logout lifecycle."""
    unique_email = f"user_{uuid.uuid4().hex[:8]}@example.com"
    password = "SecurePassword123!"

    # 1. Register new user
    reg_res = client.post(
        "/api/v1/auth/register",
        json={"email": unique_email, "password": password},
    )
    assert reg_res.status_code == 201
    reg_data = reg_res.json()
    assert reg_data["email"] == unique_email
    assert reg_data["is_active"] is True
    assert "id" in reg_data

    # 2. Duplicate registration attempt should return HTTP 409
    dup_res = client.post(
        "/api/v1/auth/register",
        json={"email": unique_email, "password": password},
    )
    assert dup_res.status_code == 409
    assert dup_res.json()["type"] == "UserAlreadyExistsException"

    # 3. Login with incorrect password should return HTTP 401
    bad_login = client.post(
        "/api/v1/auth/login",
        json={"email": unique_email, "password": "WrongPassword!"},
    )
    assert bad_login.status_code == 401

    # 4. Valid login returns JWT token and sets HTTP-only access_token cookie
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": unique_email, "password": password},
    )
    assert login_res.status_code == 200
    login_data = login_res.json()
    assert "access_token" in login_data
    token = login_data["access_token"]
    assert "access_token" in login_res.cookies

    # 5. GET /me with Bearer token header
    me_res = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_res.status_code == 200
    assert me_res.json()["email"] == unique_email

    # 6. Logout clears cookie
    logout_res = client.post("/api/v1/auth/logout")
    assert logout_res.status_code == 200
