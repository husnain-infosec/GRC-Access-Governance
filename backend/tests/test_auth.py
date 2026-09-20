import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_register_creates_employee():
    response = client.post(
        "/api/auth/register",
        json={"email": "pytest_user1@example.com", "password": "TestPassword123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["role_id"] == 3
    assert "password_hash" not in data

def test_register_duplicate_email_rejected():
    client.post(
        "/api/auth/register",
        json={"email": "pytest_dup@example.com", "password": "TestPassword123"},
    )
    response = client.post(
        "/api/auth/register",
        json={"email": "pytest_dup@example.com", "password": "TestPassword123"},
    )
    assert response.status_code == 400

def test_register_short_password_rejected():
    response = client.post(
        "/api/auth/register",
        json={"email": "pytest_short@example.com", "password": "short"},
    )
    assert response.status_code == 422

def test_login_with_correct_credentials():
    client.post(
        "/api/auth/register",
        json={"email": "pytest_login1@example.com", "password": "TestPassword123"},
    )
    response = client.post(
        "/api/auth/login",
        json={"email": "pytest_login1@example.com", "password": "TestPassword123"},
    )
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_login_with_wrong_password_rejected():
    client.post(
        "/api/auth/register",
        json={"email": "pytest_login2@example.com", "password": "TestPassword123"},
    )
    response = client.post(
        "/api/auth/login",
        json={"email": "pytest_login2@example.com", "password": "WrongPassword"},
    )
    assert response.status_code == 401

def test_login_with_unknown_email_rejected():
    response = client.post(
        "/api/auth/login",
        json={"email": "pytest_nonexistent@example.com", "password": "TestPassword123"},
    )
    assert response.status_code == 401

def test_protected_route_rejects_missing_token():
    response = client.get("/api/access-requests/me")
    assert response.status_code == 401