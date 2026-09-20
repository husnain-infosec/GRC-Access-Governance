import uuid
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.rbac import require_roles, ADMIN, MANAGER
from app.core.audit import log_audit_event
from app.models.user import User
from app.schemas.user import UserListResponse, RoleChangeRequest

router = APIRouter(prefix="/api/users", tags=["users"])

def get_client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"

@router.get("", response_model=list[UserListResponse])
def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(ADMIN, MANAGER)),
):
    query = db.query(User)
    if current_user.role_id == MANAGER:
        query = query.filter(User.department_id == current_user.department_id)
    return query.all()

@router.patch("/{user_id}/role", response_model=UserListResponse)
def change_user_role(
    user_id: uuid.UUID,
    payload: RoleChangeRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(ADMIN)),
):
    target_user = db.query(User).filter(User.id == user_id).with_for_update().first()
    if target_user is None:
        raise HTTPException(status_code=404, detail="User not found")

    if target_user.role_id == 1 and payload.role_id != 1:
        active_admins = (
            db.query(User)
            .filter(User.role_id == 1, User.is_active == True)
            .with_for_update()
            .all()
        )
        if len(active_admins) <= 1:
            db.rollback()
            raise HTTPException(status_code=400, detail="Cannot remove the last active Admin")

    old_role_id = target_user.role_id
    target_user.role_id = payload.role_id
    target_user.token_version += 1

    log_audit_event(
        db, action="ROLE_CHANGED", ip_address=get_client_ip(request), status="SUCCESS",
        user_id=current_user.id, department_id=current_user.department_id,
        target_user_id=target_user.id,
        metadata={"old_role_id": old_role_id, "new_role_id": payload.role_id},
    )

    db.commit()
    db.refresh(target_user)
    return target_user

@router.patch("/{user_id}/deactivate", response_model=UserListResponse)
def deactivate_user(
    user_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(ADMIN)),
):
    target_user = db.query(User).filter(User.id == user_id).with_for_update().first()
    if target_user is None:
        raise HTTPException(status_code=404, detail="User not found")

    if target_user.role_id == 1:
        active_admins = (
            db.query(User)
            .filter(User.role_id == 1, User.is_active == True)
            .with_for_update()
            .all()
        )
        if len(active_admins) <= 1:
            db.rollback()
            raise HTTPException(status_code=400, detail="Cannot deactivate the last active Admin")

    target_user.is_active = False
    target_user.token_version += 1

    log_audit_event(
        db, action="USER_DEACTIVATED", ip_address=get_client_ip(request), status="SUCCESS",
        user_id=current_user.id, department_id=current_user.department_id,
        target_user_id=target_user.id,
    )

    db.commit()
    db.refresh(target_user)
    return target_user