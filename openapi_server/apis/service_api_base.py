# coding: utf-8

from typing import ClassVar, Dict, List, Tuple  # noqa: F401

from pydantic import Field, StrictInt, StrictStr
from typing import Any, List, Optional
from typing_extensions import Annotated
from openapi_server.models.error import Error
from openapi_server.models.service import Service
from openapi_server.models.service_fvo import ServiceFVO
from openapi_server.models.service_mvo import ServiceMVO


class BaseServiceApi:
    subclasses: ClassVar[Tuple] = ()

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        BaseServiceApi.subclasses = BaseServiceApi.subclasses + (cls,)
    async def create_service(
        self,
        service_fvo: Annotated[ServiceFVO, Field(description="The Service to be created")],
        fields: Annotated[Optional[StrictStr], Field(description="Comma-separated properties to be provided in response")],
    ) -> Service:
        """This operation creates a Service entity."""
        ...


    async def delete_service(
        self,
        id: Annotated[StrictStr, Field(description="Identifier of the Resource")],
    ) -> None:
        """This operation deletes a Service entity."""
        ...


    async def list_service(
        self,
        fields: Annotated[Optional[StrictStr], Field(description="Comma-separated properties to be provided in response")],
        offset: Annotated[Optional[StrictInt], Field(description="Requested index for start of resources to be provided in response")],
        limit: Annotated[Optional[StrictInt], Field(description="Requested number of resources to be provided in response")],
    ) -> List[Service]:
        """List or find Service objects"""
        ...


    async def patch_service(
        self,
        id: Annotated[StrictStr, Field(description="Identifier of the Resource")],
        service_mvo: Annotated[ServiceMVO, Field(description="The Service to be patched")],
        fields: Annotated[Optional[StrictStr], Field(description="Comma-separated properties to be provided in response")],
    ) -> Service:
        """This operation updates partially a Service entity."""
        ...


    async def retrieve_service(
        self,
        id: Annotated[StrictStr, Field(description="Identifier of the Resource")],
        fields: Annotated[Optional[StrictStr], Field(description="Comma-separated properties to be provided in response")],
    ) -> Service:
        """This operation retrieves a Service entity. Attribute selection enabled for all first level attributes."""
        ...
