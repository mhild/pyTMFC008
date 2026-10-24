# coding: utf-8

import uuid
from typing import Any, Dict

from fastapi import APIRouter, Body, Depends, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from openapi_server.database.models import Hub as HubRow
from openapi_server.database.session import get_db_session
from openapi_server.models.error import Error
from openapi_server.models.hub import Hub
from openapi_server.services.events import validate_hub
from openapi_server.services.service import load

router = APIRouter()

HUB_ERRORS = {
    400: {"model": Error, "description": "Bad Request"},
    404: {"model": Error, "description": "Not Found"},
    500: {"model": Error, "description": "Internal Server Error"},
}


@router.post(
    "/hub",
    responses={201: {"model": Hub, "description": "Notified"}, **HUB_ERRORS},
    tags=["events subscription"],
    summary="Create a subscription (hub) to receive Events",
    status_code=201,
)
async def create_hub(
    request: Request,
    response: Response,
    payload: Dict = Body(..., description="Data containing the callback endpoint to deliver the information"),
    session: AsyncSession = Depends(get_db_session),
) -> Dict[str, Any]:
    """Sets the communication endpoint to receive Events."""
    validate_hub(payload)
    hub_id = uuid.uuid4()
    hub = {
        "id": str(hub_id),
        "href": f"{str(request.url).rstrip('/')}/{hub_id}",
        "@type": payload.get("@type", "Hub"),
        "callback": payload["callback"],
    }
    if payload.get("query"):
        hub["query"] = payload["query"]
    session.add(HubRow(id=hub_id, payload=hub))
    await session.commit()
    response.headers["Location"] = hub["href"]
    return hub


@router.get(
    "/hub/{id}",
    responses={200: {"model": Hub, "description": "Success"}, **HUB_ERRORS},
    tags=["events subscription"],
    summary="Retrieves a subscription (hub)",
)
async def get_hub(id: str, session: AsyncSession = Depends(get_db_session)) -> Dict[str, Any]:
    return (await load(session, HubRow, id)).payload


@router.delete(
    "/hub/{id}",
    responses={204: {"description": "Deleted"}, **HUB_ERRORS},
    tags=["events subscription"],
    summary="Remove a subscription (hub) to receive Events",
    status_code=204,
)
async def hub_delete(id: str, session: AsyncSession = Depends(get_db_session)):
    await session.delete(await load(session, HubRow, id))
    await session.commit()
    return Response(status_code=204)
