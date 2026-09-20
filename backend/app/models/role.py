from sqlalchemy import Column, SmallInteger, String
from app.core.database import Base

class Role(Base):
    __tablename__ = "roles"

    id = Column(SmallInteger, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(String(255), nullable=True)