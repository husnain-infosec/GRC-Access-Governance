import uuid
from pydantic import BaseModel

class ResourceCreate(BaseModel):
    name: str
    description: str | None = None

class ResourceResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    is_active: bool

    class Config:
        from_attributes = True