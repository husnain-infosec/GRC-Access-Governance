import uuid
from datetime import datetime
from pydantic import BaseModel

class AccessRequestCreate(BaseModel):
    resource_id: uuid.UUID
    reason: str | None = None

class AccessRequestResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    resource_id: uuid.UUID
    status: str
    reason: str | None
    reviewed_by: uuid.UUID | None
    reviewed_at: datetime | None
    created_at: datetime

    class Config:
        from_attributes = True