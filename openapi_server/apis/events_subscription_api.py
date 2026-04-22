# coding: utf-8

from typing import Dict, List  # noqa: F401
import importlib
import pkgutil

from openapi_server.apis.events_subscription_api_base import BaseEventsSubscriptionApi
import openapi_server.impl

from fastapi import (  # noqa: F401
    APIRouter,
    Body,
    Cookie,
    Depends,
    Form,
    Header,
    HTTPException,
    Path,
    Query,
    Response,
    Security,
    status,
)

from openapi_server.models.extra_models import TokenModel  # noqa: F401
from pydantic import Field, StrictStr
from typing import Any
from typing_extensions import Annotated
from openapi_server.models.error import Error
from openapi_server.models.hub import Hub
from openapi_server.models.hub_fvo import HubFVO


router = APIRouter()

ns_pkg = openapi_server.impl
for _, name, _ in pkgutil.iter_modules(ns_pkg.__path__, ns_pkg.__name__ + "."):
    importlib.import_module(name)


@router.post(
    "/hub",
    responses={
        201: {"model": Hub, "description": "Notified"},
        "default": {"model": Error, "description": "Error"},
    },
    tags=["events subscription"],
    summary="Create a subscription (hub) to receive Events",
    response_model_by_alias=True,
)
async def create_hub(
    hub_fvo: Annotated[HubFVO, Field(description="Data containing the callback endpoint to deliver the information")] = Body(None, description="Data containing the callback endpoint to deliver the information"),
) -> Hub:
    """Sets the communication endpoint to receive Events."""
    if not BaseEventsSubscriptionApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseEventsSubscriptionApi.subclasses[0]().create_hub(hub_fvo)


@router.delete(
    "/hub/{id}",
    responses={
        204: {"description": "Deleted"},
        "default": {"model": Error, "description": "Error"},
    },
    tags=["events subscription"],
    summary="Remove a subscription (hub) to receive Events",
    response_model_by_alias=True,
)
async def hub_delete(
    id: Annotated[StrictStr, Field(description="Identifier of the Resource")] = Path(..., description="Identifier of the Resource"),
) -> None:
    """"""
    if not BaseEventsSubscriptionApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseEventsSubscriptionApi.subclasses[0]().hub_delete(id)
