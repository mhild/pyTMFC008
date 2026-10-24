from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import text

from openapi_server.database.session import engine

# Operational endpoints, not part of the TMF638 API (hence not in the OpenAPI document)
router = APIRouter(include_in_schema=False)


@router.get("/livez")
async def livez() -> dict:
    """Liveness: the process answers. Does not touch the database."""
    return {"status": "ok"}


@router.get("/readyz")
async def readyz() -> JSONResponse:
    """Readiness: the database is reachable and has the schema (migrations applied)."""
    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1 FROM service WHERE 1 = 0"))
    except Exception as exc:  # any failure means not ready; the reason goes to the caller, not the details
        return JSONResponse(status_code=503, content={"status": "unavailable", "reason": type(exc).__name__})
    return JSONResponse(content={"status": "ok"})
