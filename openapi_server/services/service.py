from sqlalchemy import select
from openapi_server.database.models import Service
from openapi_server.database.session import get_db_session
from typing import AsyncGenerator, Dict
import uuid
from fastapi import Depends, HTTPException

async def create_service(
    payload: Dict,
    session: AsyncSession = Depends(get_db_session),
    base_url: str = None,
) -> str:
    service_id = uuid.uuid4()  # generate a UUID
    payload['id'] = str(service_id)
    if base_url is not None:
        payload['href'] = f'{base_url}/{str(service_id)}'
    db_service = Service(
        id=service_id,
        payload=payload,
    )
    session.add(db_service)
    await session.commit()
    return payload

async def get_service(
    service_id: str,  # ← coming from path as string
    session: AsyncSession = Depends(get_db_session),
) -> Dict:
    try:
        parsed_id = uuid.UUID(service_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid service_id format")

    stmt = select(Service).where(Service.id == parsed_id)
    result = await session.execute(stmt)
    db_service = result.scalar()
    if not db_service:
        raise HTTPException(status_code=404, detail="Service not found")
    return db_service.payload

async def delete_service(
    service_id: str,
    session: AsyncSession = Depends(get_db_session),
):
    try:
        parsed_id = uuid.UUID(service_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid service_id format")

    stmt = select(Service).where(Service.id == parsed_id)
    result = await session.execute(stmt)
    db_service = result.scalar()
    if not db_service:
        raise HTTPException(status_code=404, detail="Service not found")
    await session.delete(db_service)
    await session.commit()