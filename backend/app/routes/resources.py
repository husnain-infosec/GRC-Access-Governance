import uuid
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.rbac import require_roles, ADMIN
from app.core.audit import log_audit_event
from app.models.user import User
from app.models.resource import Resource
from app.schemas.resource import ResourceCreate, ResourceResponse

router = APIRouter(prefix="/api/resources", tags=["resources"])

def get_client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"

@router.get("", response_model=list[ResourceResponse])
def list_resources(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return db.query(Resource).filter(Resource.is_active == True).all()

@router.post("", response_model=ResourceResponse)
def create_resource(
    payload: ResourceCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(ADMIN)),
):
    resource = Resource(name=payload.name, description=payload.description)
    db.add(resource)

    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="A resource with this name already exists")

    log_audit_event(
        db, action="RESOURCE_CREATED", ip_address=get_client_ip(request), status="SUCCESS",
        user_id=current_user.id, department_id=current_user.department_id,
        resource_id=resource.id,
    )

    db.commit()
    db.refresh(resource)
    return resource

@router.patch("/{resource_id}/deactivate", response_model=ResourceResponse)
def deactivate_resource(
    resource_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(ADMIN)),
):
    resource = db.query(Resource).filter(Resource.id == resource_id).first()
    if resource is None:
        raise HTTPException(status_code=404, detail="Resource not found")

    resource.is_active = False

    log_audit_event(
        db, action="RESOURCE_DEACTIVATED", ip_address=get_client_ip(request), status="SUCCESS",
        user_id=current_user.id, department_id=current_user.department_id,
        resource_id=resource.id,
    )

    db.commit()
    db.refresh(resource)
    return resource