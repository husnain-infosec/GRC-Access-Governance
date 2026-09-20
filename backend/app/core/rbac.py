from fastapi import Depends, HTTPException
from app.core.dependencies import get_current_user
from app.models.user import User

ADMIN = 1
MANAGER = 2
EMPLOYEE = 3

def require_roles(*allowed_role_ids: int):
    def dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role_id not in allowed_role_ids:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return current_user
    return dependency