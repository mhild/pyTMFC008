# coding: utf-8

from typing import ClassVar, Dict, List, Tuple  # noqa: F401

from pydantic import Field
from typing import Any
from typing_extensions import Annotated
from openapi_server.models.error import Error
from openapi_server.models.service_attribute_value_change_event import ServiceAttributeValueChangeEvent
from openapi_server.models.service_create_event import ServiceCreateEvent
from openapi_server.models.service_delete_event import ServiceDeleteEvent
from openapi_server.models.service_operating_status_change_event import ServiceOperatingStatusChangeEvent
from openapi_server.models.service_state_change_event import ServiceStateChangeEvent


class BaseNotificationListenerApi:
    subclasses: ClassVar[Tuple] = ()

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        BaseNotificationListenerApi.subclasses = BaseNotificationListenerApi.subclasses + (cls,)
    async def service_attribute_value_change_event(
        self,
        service_attribute_value_change_event: Annotated[ServiceAttributeValueChangeEvent, Field(description="Service attributeValueChange Event payload")],
    ) -> None:
        """Example of a client listener for receiving the notification ServiceAttributeValueChangeEvent"""
        ...


    async def service_create_event(
        self,
        service_create_event: Annotated[ServiceCreateEvent, Field(description="Service create Event payload")],
    ) -> None:
        """Example of a client listener for receiving the notification ServiceCreateEvent"""
        ...


    async def service_delete_event(
        self,
        service_delete_event: Annotated[ServiceDeleteEvent, Field(description="Service delete Event payload")],
    ) -> None:
        """Example of a client listener for receiving the notification ServiceDeleteEvent"""
        ...


    async def service_operating_status_change_event(
        self,
        service_operating_status_change_event: Annotated[ServiceOperatingStatusChangeEvent, Field(description="Service operatingStatusChange Event payload")],
    ) -> None:
        """Example of a client listener for receiving the notification ServiceOperatingStatusChangeEvent"""
        ...


    async def service_state_change_event(
        self,
        service_state_change_event: Annotated[ServiceStateChangeEvent, Field(description="Service stateChange Event payload")],
    ) -> None:
        """Example of a client listener for receiving the notification ServiceStateChangeEvent"""
        ...
