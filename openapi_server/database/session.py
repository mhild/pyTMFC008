from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from typing import AsyncGenerator

from openapi_server.database.models import Base

DATABASE_URL = "postgresql+asyncpg://app:secret@db:5432/app_db"
#DATABASE_URL = "postgresql+asyncpg://app:secret@localhost:5432/app_db"

engine = create_async_engine(DATABASE_URL, echo=True)
async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session