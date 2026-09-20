import uuid
from fastapi import Depends, HTTPException, Header
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.jwt_utils import decode_access_token
from app.models.user import User

def get_current_user(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> User:
    if authorization is None or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")

    token = authorization.removeprefix("Bearer ").strip()
    payload = decode_access_token(token)

    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    try:
        user_id = uuid.UUID(payload.get("user_id"))
    except (ValueError, TypeError):
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    token_version = payload.get("token_version")

    user = db.query(User).filter(User.id == user_id).first()

    if user is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    if user.token_version != token_version:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    if not user.is_active:
        raise HTTPException(status_code=401, detail="Account is inactive")

    return user