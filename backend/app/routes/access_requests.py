import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from pydantic import BaseModel

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.rbac import require_roles, ADMIN, MANAGER
from app.core.audit import log_audit_event
from app.models.user import User
from app.models.resource import Resource
from app.models.access_request import AccessRequest
from app.models.user_resource_access import UserResourceAccess
from app.schemas.access_request import AccessRequestCreate, AccessRequestResponse

router = APIRouter(prefix="/api/access-requests", tags=["access-requests"])

def get_client_ip(request: Request) -> str:
    raw_ip = request.client.host if request.client else "unknown"
    return raw_ip if raw_ip not in ("testclient", "unknown") else "127.0.0.1"

@router.post("", response_model=AccessRequestResponse)
def create_access_request(
    payload: AccessRequestCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    resource = db.query(Resource).filter(Resource.id == payload.resource_id).first()
    if resource is None or not resource.is_active:
        raise HTTPException(status_code=404, detail="Resource not found")

    access_request = AccessRequest(
        user_id=current_user.id,
        resource_id=payload.resource_id,
        reason=payload.reason,
        status="PENDING",
    )
    db.add(access_request)

    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="A pending request for this resource already exists")

    log_audit_event(
        db, action="ACCESS_REQUEST_CREATED", ip_address=get_client_ip(request), status="SUCCESS",
        user_id=current_user.id, department_id=current_user.department_id,
        resource_id=payload.resource_id,
    )

    db.commit()
    db.refresh(access_request)
    return access_request

@router.get("/pending", response_model=list[AccessRequestResponse])
def list_pending_requests(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(ADMIN, MANAGER)),
):
    query = db.query(AccessRequest).filter(AccessRequest.status == "PENDING")

    if current_user.role_id == MANAGER:
        query = (
            query.join(User, AccessRequest.user_id == User.id)
            .filter(User.department_id == current_user.department_id)
        )

    return query.order_by(AccessRequest.created_at.desc()).all()

@router.get("/granted")
def list_granted_access(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(ADMIN, MANAGER)),
):
    query = db.query(UserResourceAccess).filter(UserResourceAccess.status == "GRANTED")

    if current_user.role_id == MANAGER:
        query = (
            query.join(User, UserResourceAccess.user_id == User.id)
            .filter(User.department_id == current_user.department_id)
        )

    results = query.all()
    return [
        {
            "user_id": str(r.user_id),
            "resource_id": str(r.resource_id),
            "granted_at": r.granted_at,
        }
        for r in results
    ]

@router.get("/me", response_model=list[AccessRequestResponse])
def list_my_access_requests(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return (
        db.query(AccessRequest)
        .filter(AccessRequest.user_id == current_user.id)
        .order_by(AccessRequest.created_at.desc())
        .all()
    )

@router.post("/{request_id}/approve", response_model=AccessRequestResponse)
def approve_access_request(
    request_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(ADMIN, MANAGER)),
):
    access_request = db.query(AccessRequest).filter(AccessRequest.id == request_id).first()
    if access_request is None:
        raise HTTPException(status_code=404, detail="Access request not found")

    if access_request.status != "PENDING":
        raise HTTPException(status_code=400, detail="Only pending requests can be approved")

    requester = db.query(User).filter(User.id == access_request.user_id).first()
    if requester is None:
        raise HTTPException(status_code=404, detail="Requesting user not found")

    if current_user.role_id == MANAGER and current_user.department_id != requester.department_id:
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    access_request.status = "APPROVED"
    access_request.reviewed_by = current_user.id
    access_request.reviewed_at = datetime.now(timezone.utc)

    existing_access = (
        db.query(UserResourceAccess)
        .filter(
            UserResourceAccess.user_id == access_request.user_id,
            UserResourceAccess.resource_id == access_request.resource_id,
        )
        .first()
    )

    if existing_access:
        existing_access.status = "GRANTED"
        existing_access.granted_at = datetime.now(timezone.utc)
        existing_access.granted_by = current_user.id
        existing_access.revoked_at = None
        existing_access.revoked_by = None
    else:
        db.add(UserResourceAccess(
            user_id=access_request.user_id,
            resource_id=access_request.resource_id,
            status="GRANTED",
            granted_at=datetime.now(timezone.utc),
            granted_by=current_user.id,
        ))

    client_ip = get_client_ip(request)
    log_audit_event(
        db, action="ACCESS_REQUEST_APPROVED", ip_address=client_ip, status="SUCCESS",
        user_id=current_user.id, department_id=current_user.department_id,
        target_user_id=access_request.user_id, resource_id=access_request.resource_id,
    )
    log_audit_event(
        db, action="ACCESS_GRANTED", ip_address=client_ip, status="SUCCESS",
        user_id=current_user.id, department_id=current_user.department_id,
        target_user_id=access_request.user_id, resource_id=access_request.resource_id,
    )

    db.commit()
    db.refresh(access_request)
    return access_request

@router.post("/{request_id}/reject", response_model=AccessRequestResponse)
def reject_access_request(
    request_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(ADMIN, MANAGER)),
):
    access_request = db.query(AccessRequest).filter(AccessRequest.id == request_id).first()
    if access_request is None:
        raise HTTPException(status_code=404, detail="Access request not found")

    if access_request.status != "PENDING":
        raise HTTPException(status_code=400, detail="Only pending requests can be rejected")

    requester = db.query(User).filter(User.id == access_request.user_id).first()
    if requester is None:
        raise HTTPException(status_code=404, detail="Requesting user not found")

    if current_user.role_id == MANAGER and current_user.department_id != requester.department_id:
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    access_request.status = "REJECTED"
    access_request.reviewed_by = current_user.id
    access_request.reviewed_at = datetime.now(timezone.utc)

    log_audit_event(
        db, action="ACCESS_REQUEST_REJECTED", ip_address=get_client_ip(request), status="SUCCESS",
        user_id=current_user.id, department_id=current_user.department_id,
        target_user_id=access_request.user_id, resource_id=access_request.resource_id,
    )

    db.commit()
    db.refresh(access_request)
    return access_request

class RevokeRequest(BaseModel):
    user_id: uuid.UUID
    resource_id: uuid.UUID

@router.post("/revoke")
def revoke_access(
    payload: RevokeRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(ADMIN, MANAGER)),
):
    target_user = db.query(User).filter(User.id == payload.user_id).first()
    if target_user is None:
        raise HTTPException(status_code=404, detail="User not found")

    if current_user.role_id == MANAGER and current_user.department_id != target_user.department_id:
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    access = (
        db.query(UserResourceAccess)
        .filter(
            UserResourceAccess.user_id == payload.user_id,
            UserResourceAccess.resource_id == payload.resource_id,
            UserResourceAccess.status == "GRANTED",
        )
        .first()
    )

    if access is None:
        raise HTTPException(status_code=404, detail="No active access found for this user and resource")

    access.status = "REVOKED"
    access.revoked_at = datetime.now(timezone.utc)
    access.revoked_by = current_user.id

    log_audit_event(
        db, action="ACCESS_REVOKED", ip_address=get_client_ip(request), status="SUCCESS",
        user_id=current_user.id, department_id=current_user.department_id,
        target_user_id=payload.user_id, resource_id=payload.resource_id,
    )

    db.commit()
    db.refresh(access)
    return access