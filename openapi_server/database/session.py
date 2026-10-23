import os
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

# e.g. postgresql+asyncpg://app:secret@db:5432/app_db
#  or  oracle+oracledb_async://app:secret@oracle:1521/?service_name=FREEPDB1
DATABASE_URL = os.environ["DATABASE_URL"]
SQL_ECHO = os.environ.get("SQL_ECHO", "false").lower() in ("1", "true", "yes")

engine = create_async_engine(DATABASE_URL, echo=SQL_ECHO, pool_pre_ping=True)
async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session
