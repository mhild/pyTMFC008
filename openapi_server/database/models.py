from sqlalchemy import Column
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase

from sqlalchemy.dialects.postgresql import UUID, JSONB  # ← use JSONB

class Base(AsyncAttrs, DeclarativeBase):
    pass

class Service(Base):
    __tablename__ = "service"

    id = Column(UUID(as_uuid=True), primary_key=True)
    payload = Column(JSONB, nullable=False)  # maps to PostgreSQL JSONB