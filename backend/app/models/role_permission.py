import uuid
from sqlalchemy import Column, SmallInteger, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base

class RolePermission(Base):
    __tablename__ = "role_permissions"

    role_id = Column(SmallInteger, ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True)
    permission_id = Column(UUID(as_uuid=True), ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True)