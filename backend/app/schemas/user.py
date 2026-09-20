import uuid
from pydantic import BaseModel, EmailStr, Field

class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    department_id: uuid.UUID | None = None
    
class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: uuid.UUID
    email: EmailStr
    role_id: int
    department_id: uuid.UUID | None
    is_active: bool

    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    
class UserListResponse(BaseModel):
    id: uuid.UUID
    email: EmailStr
    role_id: int
    department_id: uuid.UUID | None
    is_active: bool

    class Config:
        from_attributes = True

class RoleChangeRequest(BaseModel):
    role_id: int