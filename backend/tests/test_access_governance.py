import uuid
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import SessionLocal
from app.models.user import User
from app.models.department import Department
from app.models.resource import Resource

client = TestClient(app)


def register_and_login(email, password="TestPassword123"):
    client.post("/api/auth/register", json={"email": email, "password": password})
    response = client.post("/api/auth/login", json={"email": email, "password": password})
    return response.json()["access_token"]


def promote_to_manager(email, department_id):
    db = SessionLocal()
    user = db.query(User).filter(User.email == email).first()
    user.role_id = 2
    user.department_id = department_id
    db.commit()
    db.close()


def get_or_create_test_department():
    db = SessionLocal()
    dept = db.query(Department).filter(Department.name == "PytestDept").first()
    if dept is None:
        dept = Department(id=uuid.uuid4(), name="PytestDept")
        db.add(dept)
        db.commit()
        db.refresh(dept)
    dept_id = dept.id
    db.close()
    return dept_id


def get_or_create_test_resource():
    db = SessionLocal()
    resource = db.query(Resource).filter(Resource.name == "PytestResource").first()
    if resource is None:
        resource = Resource(id=uuid.uuid4(), name="PytestResource", is_active=True)
        db.add(resource)
        db.commit()
        db.refresh(resource)
    resource_id = resource.id
    db.close()
    return resource_id


def test_create_request_then_approve_grants_access():
    dept_id = get_or_create_test_department()
    resource_id = get_or_create_test_resource()

    employee_email = f"pytest_gov_emp_{uuid.uuid4().hex[:8]}@example.com"
    manager_email = f"pytest_gov_mgr_{uuid.uuid4().hex[:8]}@example.com"

    employee_token = register_and_login(employee_email)
    manager_token = register_and_login(manager_email)

    db = SessionLocal()
    employee = db.query(User).filter(User.email == employee_email).first()
    employee.department_id = dept_id
    db.commit()
    db.close()

    promote_to_manager(manager_email, dept_id)

    manager_token = client.post(
        "/api/auth/login",
        json={"email": manager_email, "password": "TestPassword123"},
    ).json()["access_token"]

    create_response = client.post(
        "/api/access-requests",
        json={"resource_id": str(resource_id), "reason": "pytest test"},
        headers={"Authorization": f"Bearer {employee_token}"},
    )
    assert create_response.status_code == 200
    request_id = create_response.json()["id"]
    assert create_response.json()["status"] == "PENDING"

    approve_response = client.post(
        f"/api/access-requests/{request_id}/approve",
        headers={"Authorization": f"Bearer {manager_token}"},
    )
    assert approve_response.status_code == 200
    assert approve_response.json()["status"] == "APPROVED"


def test_cannot_approve_already_approved_request():
    dept_id = get_or_create_test_department()
    resource_id = get_or_create_test_resource()

    employee_email = f"pytest_gov_emp2_{uuid.uuid4().hex[:8]}@example.com"
    manager_email = f"pytest_gov_mgr2_{uuid.uuid4().hex[:8]}@example.com"

    employee_token = register_and_login(employee_email)
    register_and_login(manager_email)

    db = SessionLocal()
    employee = db.query(User).filter(User.email == employee_email).first()
    employee.department_id = dept_id
    db.commit()
    db.close()

    promote_to_manager(manager_email, dept_id)

    manager_token = client.post(
        "/api/auth/login",
        json={"email": manager_email, "password": "TestPassword123"},
    ).json()["access_token"]

    create_response = client.post(
        "/api/access-requests",
        json={"resource_id": str(resource_id), "reason": "pytest test 2"},
        headers={"Authorization": f"Bearer {employee_token}"},
    )
    request_id = create_response.json()["id"]

    client.post(
        f"/api/access-requests/{request_id}/approve",
        headers={"Authorization": f"Bearer {manager_token}"},
    )

    second_approve = client.post(
        f"/api/access-requests/{request_id}/approve",
        headers={"Authorization": f"Bearer {manager_token}"},
    )
    assert second_approve.status_code == 400


def test_duplicate_pending_request_rejected():
    resource_id = get_or_create_test_resource()
    employee_email = f"pytest_gov_dup_{uuid.uuid4().hex[:8]}@example.com"
    employee_token = register_and_login(employee_email)

    client.post(
        "/api/access-requests",
        json={"resource_id": str(resource_id), "reason": "first"},
        headers={"Authorization": f"Bearer {employee_token}"},
    )
    second_response = client.post(
        "/api/access-requests",
        json={"resource_id": str(resource_id), "reason": "second"},
        headers={"Authorization": f"Bearer {employee_token}"},
    )
    assert second_response.status_code == 400