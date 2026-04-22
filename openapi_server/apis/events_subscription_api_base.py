# coding: utf-8

from typing import ClassVar, Dict, List, Tuple  # noqa: F401

from pydantic import Field, StrictStr
from typing import Any
from typing_extensions import Annotated
from openapi_server.models.error import Error
from openapi_server.models.hub import Hub
from openapi_server.models.hub_fvo import HubFVO


class BaseEventsSubscriptionApi:
    subclasses: ClassVar[Tuple] = ()

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        BaseEventsSubscriptionApi.subclasses = BaseEventsSubscriptionApi.subclasses + (cls,)
    async def create_hub(
        self,
        hub_fvo: Annotated[HubFVO, Field(description="Data containing the callback endpoint to deliver the information")],
    ) -> Hub:
        """Sets the communication endpoint to receive Events."""
        ...


    async def hub_delete(
        self,
        id: Annotated[StrictStr, Field(description="Identifier of the Resource")],
    ) -> None:
        """"""
        ...
