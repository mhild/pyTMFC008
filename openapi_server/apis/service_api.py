# coding: utf-8

from typing import Dict, List  # noqa: F401
import importlib
import pkgutil

from openapi_server.apis.service_api_base import BaseServiceApi
import openapi_server.impl

from sqlalchemy import select, text
from openapi_server.database.models import Service as ServiceDB

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

import uuid
from typing import Dict
import jsonpatch

from openapi_server.services.service import create_service, get_service, delete_service
from openapi_server.database.session import get_db_session
from openapi_server.services.merge_patch import apply_merge_patch

router = APIRouter()

ns_pkg = openapi_server.impl
for _, name, _ in pkgutil.iter_modules(ns_pkg.__path__, ns_pkg.__name__ + "."):
    importlib.import_module(name)

import re

def jayway_to_pg_jsonpath(expr: str) -> str:
    # 1. Convert "[?(@." to "[*] ? (@."
    expr = expr.replace("[?(@.", "[*] ? (@.")

    # 2. Replace @.foo=='bar' with @.foo == "bar"
    expr = re.sub(
        r"(@\.[^=!]+)==\'([^\']*)\'",
        r'\1 == "\2"',
        expr,
    )

    # 3. If expression ends with ")]", drop the last "]"
    if expr.endswith(")]"):
        expr = expr[:-1]

    return expr

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
    response_model_by_alias=True,
)
async def post_service(
    request: Request,
    payload: Dict = Body(...),
    db_session: AsyncSession = Depends(get_db_session),
):
    service = await create_service(payload, db_session, base_url=f'{str(request.url)}')
    return service

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
    response_model_by_alias=True,
)
async def delete_service_endpoint(
    service_id: str,
    db_session: AsyncSession = Depends(get_db_session),
):
    await delete_service(service_id, db_session)
    return {"ok": True}

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
@router.get("/service")
async def get_services(
    *,
    name: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    tags: List[str] = Query([]),
    filter: Optional[str] = Query(
        None,
        description="JSONPath expression on payload (PostgreSQL jsonb_path_exists)",
    ),
    fields: Optional[str] = Query(
        None,
        description="Comma-separated list of top-level fields to include in each service",
    ),
    session: AsyncSession = Depends(get_db_session),
) -> List[Dict]:
    stmt = select(ServiceDB)

    # top‑level key filters (name, status, tags)
    params = {}

    if name is not None:
        stmt = stmt.where(
            text("payload->> 'name' = :name")
        ).params(name=name)
        params["name"] = name

    if status is not None:
        stmt = stmt.where(
            text("payload->> 'status' = :status")
        ).params(status=status)
        params["status"] = status

    if tags:
        tag_strs = [f"'{t}'" for t in tags]
        stmt = stmt.where(
            text(f"payload->'tags' ?| ARRAY[{','.join(tag_strs)}]")
        )

    # JSONPath filter on payload
    if filter is not None:
        pg_expr = jayway_to_pg_jsonpath(filter)
        # Bind the path as a string
        stmt = stmt.where(
            text("jsonb_path_exists(payload, :jsonpath)")
        ).params(jsonpath=pg_expr)

    # rebinding is not needed; text(...) + .params already knows the names
    # but if you mix, you can do:
    # stmt = stmt.params(**params)  # for consistency

    result = await session.execute(stmt)
    rows = result.scalars().all()

    ###
    # Parse fields param into a set of keys (strip whitespace)
    field_set: Optional[set[str]] = None
    if fields:
        field_set = {f.strip() for f in fields.split(",") if f.strip()}
    services: List[Dict] = []
    for row in rows:
        base = {
            "id": str(row.id),
            **(row.payload or {}),
        }
        if field_set is not None:
            # Always keep `id`; filter the rest
            filtered = {"id": base["id"]}
            for key in field_set:
                if key in base:
                    filtered[key] = base[key]
            services.append(filtered)
        else:
            services.append(base)

    return services

    # return [
    #     {"id": str(row.id), "payload": row.payload}
    #     for row in rows
    # ]

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
    session: AsyncSession = Depends(get_db_session),
) -> Dict[str, Any]:
    # 1. Parse path param
    try:
        sid = uuid.UUID(service_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid service_id format")

    # 2. Load current document from DB
    stmt = select(ServiceDB).where(ServiceDB.id == sid)
    result = await session.execute(stmt)
    service_row = result.scalar()

    if not service_row:
        raise HTTPException(status_code=404, detail="Service not found")

    current_doc = service_row.payload  # dict

    # 3. Inspect Content-Type
    content_type = request.headers.get("content-type", "").split(";")[0].strip()

    # 4. Read body as JSON
    patch_body = await request.json()

    if content_type == "application/json-patch+json":
        # 4a: JSON Patch (RFC 6902)
        if not isinstance(patch_body, list):
            raise HTTPException(status_code=400, detail="JSON Patch body must be a list")

        try:
            patch = jsonpatch.JsonPatch(patch_body)
            new_doc = patch.apply(current_doc, in_place=False)
        except jsonpatch.JsonPatchException as exc:
            raise HTTPException(status_code=400, detail=f"Invalid JSON Patch: {exc}")

    elif content_type == "application/merge-patch+json":
        # 4b: JSON Merge Patch (RFC 7396)
        new_doc = apply_merge_patch(current_doc, patch_body)

    else:
        raise HTTPException(
            status_code=415,
            detail="Unsupported Content-Type. Use application/json-patch+json or application/merge-patch+json",
        )

    # 5. Persist back to DB
    service_row.payload = new_doc
    session.add(service_row)
    await session.commit()
    await session.refresh(service_row)

    return {
        "id": str(service_row.id),
        "payload": service_row.payload,
    }

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
    service_id: str,  # ← path param as string
    db_session: AsyncSession = Depends(get_db_session),
    fields: Optional[str] = Query(
        None,
        description="Comma-separated list of top-level fields to include in each service",
    ),
):
    data = await get_service(service_id, db_session)

    # Parse fields param into a set of keys (strip whitespace)
    field_set: Optional[set[str]] = None
    if fields:
        field_set = {f.strip() for f in fields.split(",") if f.strip()}

    if field_set is not None:
        # Always keep `id`; filter the rest
        filtered = {"id": data["id"]}
        for key in field_set:
            if key in data:
                filtered[key] = data[key]
        return filtered
    return data
