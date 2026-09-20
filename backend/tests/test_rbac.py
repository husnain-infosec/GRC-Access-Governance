import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def register_and_login(email, password="TestPassword123"):
    client.post("/api/auth/register", json={"email": email, "password": password})
    response = client.post("/api/auth/login", json={"email": email, "password": password})
    return response.json()["access_token"]


def test_employee_cannot_access_admin_only_users_endpoint():
    token = register_and_login("pytest_rbac_employee@example.com")
    response = client.get(
        "/api/users", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 403


def test_employee_cannot_approve_requests():
    token = register_and_login("pytest_rbac_employee2@example.com")
    fake_request_id = "00000000-0000-0000-0000-000000000000"
    response = client.post(
        f"/api/access-requests/{fake_request_id}/approve",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403


def test_unauthenticated_request_rejected():
    response = client.get("/api/access-requests/pending")
    assert response.status_code == 401


def test_employee_can_view_own_requests():
    token = register_and_login("pytest_rbac_employee3@example.com")
    response = client.get(
        "/api/access-requests/me", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json() == []


def test_employee_cannot_create_resource():
    token = register_and_login("pytest_rbac_employee4@example.com")
    response = client.post(
        "/api/resources",
        json={"name": "pytest_test_resource"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403


def test_employee_cannot_view_resource_list_without_auth():
    response = client.get("/api/resources")
    assert response.status_code == 401