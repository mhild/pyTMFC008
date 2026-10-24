# coding: utf-8

from typing import Dict, List  # noqa: F401
import importlib
import pkgutil

from openapi_server.apis.service_api_base import BaseServiceApi
import openapi_server.impl

from fastapi import (  # noqa: F401
    APIRouter,
    BackgroundTasks,
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
    Request,
)

from openapi_server.models.extra_models import TokenModel  # noqa: F401
from pydantic import Field, StrictInt, StrictStr
from typing import Dict, Any, List, Optional
from typing_extensions import Annotated
from openapi_server.models.error import Error
from openapi_server.models.service import Service
from openapi_server.models.service_fvo import ServiceFVO
from openapi_server.models.service_mvo import ServiceMVO

from sqlalchemy.ext.asyncio import AsyncSession

from openapi_server.services import events
from openapi_server.services.service import (
    create_service,
    delete_service,
    get_service,
    list_services,
    parse_fields,
    patch_service as patch_service_doc,
    project,
)
from openapi_server.database.session import get_db_session

router = APIRouter()

ns_pkg = openapi_server.impl
for _, name, _ in pkgutil.iter_modules(ns_pkg.__path__, ns_pkg.__name__ + "."):
    importlib.import_module(name)

DEFAULT_LIMIT = 100
MAX_LIMIT = 1000

FIELDS_QUERY = Query(None, description="Comma-separated properties to be provided in response")


@router.post(
    "/service",
    responses={
        201: {"model": Service, "description": "OK/Created"},
        202: {"description": "Accepted"},
        400: {"model": Error, "description": "Bad Request"},
        401: {"model": Error, "description": "Unauthorized"},
        403: {"model": Error, "description": "Forbidden"},
        404: {"model": Error, "description": "Not Found"},
        405: {"model": Error, "description": "Method Not allowed"},
        409: {"model": Error, "description": "Conflict"},
        500: {"model": Error, "description": "Internal Server Error"},
        501: {"model": Error, "description": "Not Implemented"},
        503: {"model": Error, "description": "Service Unavailable"},
    },
    tags=["service"],
    summary="Creates a Service",
    status_code=201,
    response_model_by_alias=True,
)
async def post_service(
    request: Request,
    response: Response,
    background_tasks: BackgroundTasks,
    payload: Dict = Body(...),
    fields: Optional[str] = FIELDS_QUERY,
    db_session: AsyncSession = Depends(get_db_session),
):
    service = await create_service(payload, db_session, base_url=str(request.url.remove_query_params("fields")))
    await events.publish([events.build_event(events.CREATE, service)], db_session, background_tasks)
    response.headers["Location"] = service["href"]
    return project(service, parse_fields(fields))

@router.delete(
    "/service/{service_id}",
    responses={
        202: {"description": "Accepted"},
        204: {"description": "Deleted"},
        400: {"model": Error, "description": "Bad Request"},
        401: {"model": Error, "description": "Unauthorized"},
        403: {"model": Error, "description": "Forbidden"},
        404: {"model": Error, "description": "Not Found"},
        405: {"model": Error, "description": "Method Not allowed"},
        409: {"model": Error, "description": "Conflict"},
        500: {"model": Error, "description": "Internal Server Error"},
        501: {"model": Error, "description": "Not Implemented"},
        503: {"model": Error, "description": "Service Unavailable"},
    },
    tags=["service"],
    summary="Deletes a Service",
    status_code=204,
    response_model_by_alias=True,
)
async def delete_service_endpoint(
    service_id: str,
    background_tasks: BackgroundTasks,
    db_session: AsyncSession = Depends(get_db_session),
):
    service = await delete_service(service_id, db_session)
    await events.publish([events.build_event(events.DELETE, service)], db_session, background_tasks)
    return Response(status_code=204)

@router.get(
    "/service",
    responses={
        200: {"model": List[Service], "description": "Success"},
        400: {"model": Error, "description": "Bad Request"},
        401: {"model": Error, "description": "Unauthorized"},
        403: {"model": Error, "description": "Forbidden"},
        404: {"model": Error, "description": "Not Found"},
        405: {"model": Error, "description": "Method Not allowed"},
        500: {"model": Error, "description": "Internal Server Error"},
        501: {"model": Error, "description": "Not Implemented"},
        503: {"model": Error, "description": "Service Unavailable"},
    },
    tags=["service"],
    summary="List or find Service objects",
    response_model_by_alias=True,
)
async def get_services(
    request: Request,
    response: Response,
    fields: Optional[str] = FIELDS_QUERY,
    offset: int = Query(0, ge=0, description="Requested index for start of resources to be provided in response"),
    limit: int = Query(DEFAULT_LIMIT, ge=1, le=MAX_LIMIT, description="Requested number of resources to be provided in response"),
    sort: Optional[str] = Query(
        None, description="Comma-separated attributes to sort by, '-' for descending, e.g. -startDate,name (TMF630)"
    ),
    filter: Optional[str] = Query(
        None,
        description="JSONPath filter (TMF630), e.g. $.serviceCharacteristic[?(@.name=='mac' && @.value=='00:11:22:33:44:55')]. "
        "Any other query parameter is an attribute filter, e.g. serviceType=Cloud or relatedParty.partyOrPartyRole.name=Peter Meyer",
    ),
    session: AsyncSession = Depends(get_db_session),
) -> List[Dict]:
    services, total = await list_services(request.query_params.multi_items(), session, offset, limit)
    response.headers["X-Total-Count"] = str(total)
    response.headers["X-Result-Count"] = str(len(services))
    if offset + len(services) < total:
        response.status_code = 206  # partial content (TMF630 pagination)
    field_set = parse_fields(fields)
    return [project(s, field_set) for s in services]

@router.patch(
    "/service/{service_id}",
    responses={
        200: {"model": Service, "description": "Success"},
        202: {"description": "Accepted"},
        400: {"model": Error, "description": "Bad Request"},
        401: {"model": Error, "description": "Unauthorized"},
        403: {"model": Error, "description": "Forbidden"},
        404: {"model": Error, "description": "Not Found"},
        405: {"model": Error, "description": "Method Not allowed"},
        409: {"model": Error, "description": "Conflict"},
        500: {"model": Error, "description": "Internal Server Error"},
        501: {"model": Error, "description": "Not Implemented"},
        503: {"model": Error, "description": "Service Unavailable"},
    },
    tags=["service"],
    summary="Updates partially a Service",
    response_model_by_alias=True,
)
async def patch_service(
    service_id: str,
    request: Request,
    background_tasks: BackgroundTasks,
    fields: Optional[str] = FIELDS_QUERY,
    session: AsyncSession = Depends(get_db_session),
) -> Dict[str, Any]:
    content_type = request.headers.get("content-type", "").split(";")[0].strip()
    try:
        patch_body = await request.json()
    except ValueError:
        raise HTTPException(status_code=400, detail="Request body is not valid JSON")
    old, service = await patch_service_doc(service_id, content_type, patch_body, session)
    await events.publish(events.change_events(old, service), session, background_tasks)
    return project(service, parse_fields(fields))

@router.get(
    "/service/{service_id}",
    responses={
        200: {"model": Service, "description": "Success"},
        400: {"model": Error, "description": "Bad Request"},
        401: {"model": Error, "description": "Unauthorized"},
        403: {"model": Error, "description": "Forbidden"},
        404: {"model": Error, "description": "Not Found"},
        405: {"model": Error, "description": "Method Not allowed"},
        500: {"model": Error, "description": "Internal Server Error"},
        501: {"model": Error, "description": "Not Implemented"},
        503: {"model": Error, "description": "Service Unavailable"},
    },
    tags=["service"],
    summary="Retrieves a Service by ID",
    response_model_by_alias=True,
)
async def get_service_endpoint(
    service_id: str,
    fields: Optional[str] = FIELDS_QUERY,
    db_session: AsyncSession = Depends(get_db_session),
):
    return project(await get_service(service_id, db_session), parse_fields(fields))
