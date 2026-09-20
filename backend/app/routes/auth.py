from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import hash_password, verify_password
from app.core.jwt_utils import create_access_token
from app.core.audit import log_audit_event
from app.schemas.user import UserRegister, UserLogin, UserResponse, TokenResponse
from app.models.user import User

router = APIRouter(prefix="/api/auth", tags=["auth"])

@router.post("/register", response_model=UserResponse)
def register(payload: UserRegister, request: Request, db: Session = Depends(get_db)):
    email = payload.email.lower()
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        email=email,
        password_hash=hash_password(payload.password),
        role_id=3,
        department_id=payload.department_id,
    )
    db.add(user)
    db.flush()

    raw_ip = request.client.host if request.client else "unknown"
    client_ip = raw_ip if raw_ip not in ("testclient", "unknown") else "127.0.0.1"
    log_audit_event(
        db, action="USER_CREATED", ip_address=client_ip, status="SUCCESS",
        user_id=user.id, department_id=user.department_id, target_user_id=user.id,
    )

    db.commit()
    db.refresh(user)
    return user

@router.post("/login", response_model=TokenResponse)
def login(payload: UserLogin, request: Request, db: Session = Depends(get_db)):
    email = payload.email.lower()
    user = db.query(User).filter(User.email == email).first()
    raw_ip = request.client.host if request.client else "unknown"
    client_ip = raw_ip if raw_ip not in ("testclient", "unknown") else "127.0.0.1"

    if not user or not verify_password(payload.password, user.password_hash):
        if user:
            log_audit_event(
                db, action="LOGIN_FAILURE", ip_address=client_ip, status="FAILURE",
                user_id=user.id, department_id=user.department_id,
            )
            db.commit()
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not user.is_active:
        log_audit_event(
            db, action="LOGIN_FAILURE", ip_address=client_ip, status="FAILURE",
            user_id=user.id, department_id=user.department_id,
            metadata={"reason": "account_inactive"},
        )
        db.commit()
        raise HTTPException(status_code=401, detail="Account is inactive")

    log_audit_event(
        db, action="LOGIN_SUCCESS", ip_address=client_ip, status="SUCCESS",
        user_id=user.id, department_id=user.department_id,
    )
    db.commit()

    token = create_access_token(
        user_id=str(user.id),
        role_id=user.role_id,
        department_id=str(user.department_id) if user.department_id else None,
        token_version=user.token_version,
    )
    return TokenResponse(access_token=token)