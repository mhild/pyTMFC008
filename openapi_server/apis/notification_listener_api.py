# coding: utf-8

from typing import Dict, List  # noqa: F401
import importlib
import pkgutil

from openapi_server.apis.notification_listener_api_base import BaseNotificationListenerApi
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
from pydantic import Field
from typing import Any
from typing_extensions import Annotated
from openapi_server.models.error import Error
from openapi_server.models.service_attribute_value_change_event import ServiceAttributeValueChangeEvent
from openapi_server.models.service_create_event import ServiceCreateEvent
from openapi_server.models.service_delete_event import ServiceDeleteEvent
from openapi_server.models.service_operating_status_change_event import ServiceOperatingStatusChangeEvent
from openapi_server.models.service_state_change_event import ServiceStateChangeEvent


router = APIRouter()

ns_pkg = openapi_server.impl
for _, name, _ in pkgutil.iter_modules(ns_pkg.__path__, ns_pkg.__name__ + "."):
    importlib.import_module(name)


@router.post(
    "/listener/serviceAttributeValueChangeEvent",
    responses={
        204: {"description": "Notified"},
        "default": {"model": Error, "description": "Error"},
    },
    tags=["notification listener"],
    summary="Client listener for entity ServiceAttributeValueChangeEvent",
    response_model_by_alias=True,
)
async def service_attribute_value_change_event(
    service_attribute_value_change_event: Annotated[ServiceAttributeValueChangeEvent, Field(description="Service attributeValueChange Event payload")] = Body(None, description="Service attributeValueChange Event payload"),
) -> None:
    """Example of a client listener for receiving the notification ServiceAttributeValueChangeEvent"""
    if not BaseNotificationListenerApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseNotificationListenerApi.subclasses[0]().service_attribute_value_change_event(service_attribute_value_change_event)


@router.post(
    "/listener/serviceCreateEvent",
    responses={
        204: {"description": "Notified"},
        "default": {"model": Error, "description": "Error"},
    },
    tags=["notification listener"],
    summary="Client listener for entity ServiceCreateEvent",
    response_model_by_alias=True,
)
async def service_create_event(
    service_create_event: Annotated[ServiceCreateEvent, Field(description="Service create Event payload")] = Body(None, description="Service create Event payload"),
) -> None:
    """Example of a client listener for receiving the notification ServiceCreateEvent"""
    if not BaseNotificationListenerApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseNotificationListenerApi.subclasses[0]().service_create_event(service_create_event)


@router.post(
    "/listener/serviceDeleteEvent",
    responses={
        204: {"description": "Notified"},
        "default": {"model": Error, "description": "Error"},
    },
    tags=["notification listener"],
    summary="Client listener for entity ServiceDeleteEvent",
    response_model_by_alias=True,
)
async def service_delete_event(
    service_delete_event: Annotated[ServiceDeleteEvent, Field(description="Service delete Event payload")] = Body(None, description="Service delete Event payload"),
) -> None:
    """Example of a client listener for receiving the notification ServiceDeleteEvent"""
    if not BaseNotificationListenerApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseNotificationListenerApi.subclasses[0]().service_delete_event(service_delete_event)


@router.post(
    "/listener/serviceOperatingStatusChangeEvent",
    responses={
        204: {"description": "Notified"},
        "default": {"model": Error, "description": "Error"},
    },
    tags=["notification listener"],
    summary="Client listener for entity ServiceOperatingStatusChangeEvent",
    response_model_by_alias=True,
)
async def service_operating_status_change_event(
    service_operating_status_change_event: Annotated[ServiceOperatingStatusChangeEvent, Field(description="Service operatingStatusChange Event payload")] = Body(None, description="Service operatingStatusChange Event payload"),
) -> None:
    """Example of a client listener for receiving the notification ServiceOperatingStatusChangeEvent"""
    if not BaseNotificationListenerApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseNotificationListenerApi.subclasses[0]().service_operating_status_change_event(service_operating_status_change_event)


@router.post(
    "/listener/serviceStateChangeEvent",
    responses={
        204: {"description": "Notified"},
        "default": {"model": Error, "description": "Error"},
    },
    tags=["notification listener"],
    summary="Client listener for entity ServiceStateChangeEvent",
    response_model_by_alias=True,
)
async def service_state_change_event(
    service_state_change_event: Annotated[ServiceStateChangeEvent, Field(description="Service stateChange Event payload")] = Body(None, description="Service stateChange Event payload"),
) -> None:
    """Example of a client listener for receiving the notification ServiceStateChangeEvent"""
    if not BaseNotificationListenerApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseNotificationListenerApi.subclasses[0]().service_state_change_event(service_state_change_event)
