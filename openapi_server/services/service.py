import uuid
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple, Type

import jsonpatch
from fastapi import HTTPException
from sqlalchemy import TIMESTAMP, Select, cast, func, literal_column, null, or_, select, text, union_all
from sqlalchemy.ext.asyncio import AsyncSession

from openapi_server.database.models import Base, Service, ServiceHistory
from openapi_server.services import history
from openapi_server.services.merge_patch import apply_merge_patch
from openapi_server.services.query.parser import FilterError, parse_query_params, parse_sort
from openapi_server.services.query.render import needs_join, render_conditions, render_sort
from openapi_server.services.validation import first_error

# Always returned, even when `fields` selects other attributes (TMF630)
MANDATORY_FIELDS = ("id", "href", "@type", "revision")  # "revision": of a historised revision


def parse_fields(fields: Optional[str]) -> Optional[Set[str]]:
    if not fields:
        return None
    return {f.strip() for f in fields.split(",") if f.strip()}


def project(doc: Dict[str, Any], field_set: Optional[Set[str]]) -> Dict[str, Any]:
    if field_set is None:
        return doc
    return {k: v for k, v in doc.items() if k in field_set or k in MANDATORY_FIELDS}


async def load(session: AsyncSession, model: Type[Base], resource_id: str, for_update: bool = False) -> Base:
    """Row of `model` with this id; 404 also for ids that can't exist (ids are UUIDs)."""
    try:
        parsed_id = uuid.UUID(resource_id)
    except ValueError:
        parsed_id = None
    row = None
    if parsed_id is not None:
        stmt = select(model).where(model.id == parsed_id)
        if for_update:
            stmt = stmt.with_for_update()
        row = (await session.execute(stmt)).scalar()
    if row is None:
        raise HTTPException(status_code=404, detail=f"{model.__name__} not found")
    return row


def validate(document: Any, schema_name: str) -> None:
    error = first_error(document, schema_name)
    if error:
        raise HTTPException(status_code=400, detail=f"Invalid {schema_name}: {error}")


async def _load(session: AsyncSession, service_id: str, for_update: bool = False) -> Service:
    return await load(session, Service, service_id, for_update)


async def create_service(payload: Dict, session: AsyncSession, base_url: str) -> Dict:
    payload.setdefault("@type", "Service")
    validate(payload, "Service_FVO")
    service_id = uuid.uuid4()
    payload["id"] = str(service_id)
    payload["href"] = f"{base_url.rstrip('/')}/{service_id}"
    service = Service(id=service_id, payload=payload)
    history.start_revision(service, history.now())
    session.add(service)
    await session.commit()
    return payload


async def get_service(
    service_id: str, session: AsyncSession, include_history: Optional[str] = None, revision: Optional[str] = None
) -> Dict:
    """The current document; with includeHistory=true the given revision (current or historised)."""
    number = history.by_id_revision(include_history, revision)
    if number is None:
        return (await _load(session, service_id)).payload
    # a deleted service has no current document, but its revisions stay retrievable
    try:
        parsed_id = uuid.UUID(service_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Service not found")
    row = await session.get(ServiceHistory, (parsed_id, number))
    if row is not None:
        return history.with_revision(row.payload, row)
    current = (await session.execute(select(Service).where(Service.id == parsed_id))).scalar()
    if current is None or number != (current.revision or 1):
        raise HTTPException(status_code=404, detail=f"Revision {number} of the Service not found")
    return current.payload  # the current revision carries no revision attributes


def _all_revisions(dialect: str):
    """Current services and historised revisions as one derived table named `service`, so that the rendered
    conditions (which address `payload` / `search`) apply to both. Current rows have is_history 0."""
    search = dialect == "oracle"  # the shadow column, see the Oracle migrations
    current = select(
        Service.id,
        Service.payload,
        *([literal_column("service.search").label("search")] if search else []),
        literal_column("0").label("is_history"),
        func.coalesce(Service.revision, 0).label("revision"),
        Service.rev_start,
        cast(null(), TIMESTAMP).label("rev_end"),
    )
    past = select(
        ServiceHistory.id,
        ServiceHistory.payload,
        *([literal_column("service_history.search").label("search")] if search else []),
        literal_column("1").label("is_history"),
        ServiceHistory.revision,
        ServiceHistory.rev_start,
        ServiceHistory.rev_end,
    )
    return union_all(current, past).subquery("service")


def _history_statements(conditions, order_by_keys, rng: history.Range, dialect: str, offset: int, limit: int):
    rows = _all_revisions(dialect)
    where = list(conditions)
    # revisions valid at some point of [start, end]; an open end / unknown start does not exclude
    if rng.start is not None:
        where.append(or_(rows.c.rev_end.is_(None), rows.c.rev_end >= rng.start))
    if rng.end is not None:
        where.append(or_(rows.c.rev_start.is_(None), rows.c.rev_start <= rng.end))
    order_by = order_by_keys + [rows.c.id, rows.c.is_history.desc(), rows.c.revision]
    count_stmt = select(func.count()).select_from(rows).where(*where)
    # No deferred join here (as in list_statements): joining the ids back to a UNION ALL of both tables scans them
    # in full. The sort keeps only the requested page (top-N), which is enough for a rarely used search.
    page_stmt = (
        select(rows.c.payload, rows.c.is_history, rows.c.revision, rows.c.rev_start, rows.c.rev_end)
        .where(*where)
        .order_by(*order_by)
        .offset(offset)
        .limit(limit)
    )
    return count_stmt, page_stmt


def list_statements(
    query_params: Iterable[Tuple[str, str]], dialect: str, offset: int, limit: int
) -> Tuple[Select, Select, bool]:
    """(count statement, page statement, joins other services?) for a list request; raises FilterError.

    With includeHistory=true the page statement returns rows (payload, is_history, revision, rev_start, rev_end)."""
    query_params = list(query_params)
    paths = parse_query_params(query_params)
    sort_keys = parse_sort(v for k, v in query_params if k == "sort")
    conditions = render_conditions(paths, dialect)
    rng = history.list_range(query_params)
    if rng is not None:
        if needs_join(paths):
            raise FilterError("Filters through references are not supported with includeHistory=true")
        count_stmt, page_stmt = _history_statements(conditions, render_sort(sort_keys, dialect), rng, dialect, offset, limit)
        return count_stmt, page_stmt, False
    order_by = render_sort(sort_keys, dialect) + [Service.id]
    count_stmt = select(func.count()).select_from(Service).where(*conditions)
    # Deferred join: sort and skip only the (indexed) ids, then load the documents
    # of the requested page - instead of sorting whole documents for deep offsets.
    page_ids = select(Service.id).where(*conditions).order_by(*order_by).offset(offset).limit(limit).subquery("page")
    page_stmt = (
        select(Service.payload)
        .join(page_ids, Service.id == page_ids.c.id)
        .order_by(*order_by)
        # Oracle can't estimate the page size (bind variables) and would full-scan for the join
        .prefix_with("/*+ NO_MERGE(page) LEADING(page) USE_NL(service) INDEX(service) */", dialect="oracle")
    )
    return count_stmt, page_stmt, needs_join(paths)


async def disable_parallel_query(session: AsyncSession) -> None:
    """PostgreSQL estimates every JSON path condition at 1% of the rows; for reference
    joins that makes parallel seq scans look cheaper than the (far better) GIN index."""
    if session.bind.dialect.name == "postgresql":
        await session.execute(text("SET LOCAL max_parallel_workers_per_gather = 0"))


async def list_services(
    query_params: Iterable[Tuple[str, str]],
    session: AsyncSession,
    offset: int,
    limit: int,
) -> Tuple[List[Dict], int]:
    """Filtered page of services and the total number of matches."""
    try:
        count_stmt, page_stmt, joins = list_statements(query_params, session.bind.dialect.name, offset, limit)
    except FilterError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    if joins:
        await disable_parallel_query(session)
    total = (await session.execute(count_stmt)).scalar_one()
    result = await session.execute(page_stmt)
    if "is_history" not in result.keys():
        return list(result.scalars().all()), total
    return [history.with_revision(row.payload, row) if row.is_history else row.payload for row in result], total


async def patch_service(
    service_id: str, content_type: str, patch_body: Any, session: AsyncSession
) -> Tuple[Dict, Dict]:
    """(document before, document after) the patch."""
    db_service = await _load(session, service_id, for_update=True)  # row lock: no lost updates
    current = db_service.payload

    if content_type == "application/json-patch+json":
        if not isinstance(patch_body, list):
            raise HTTPException(status_code=400, detail="JSON Patch body must be a list")
        try:
            new_doc = jsonpatch.JsonPatch(patch_body).apply(current, in_place=False)
        except (jsonpatch.JsonPatchException, jsonpatch.JsonPointerException) as exc:
            raise HTTPException(status_code=400, detail=f"Invalid JSON Patch: {exc}")
    elif content_type in ("application/merge-patch+json", "application/json"):
        new_doc = apply_merge_patch(current, patch_body)
    else:
        raise HTTPException(
            status_code=415,
            detail="Unsupported Content-Type. Use application/json-patch+json or application/merge-patch+json",
        )
    if not isinstance(new_doc, dict):
        raise HTTPException(status_code=400, detail="Patch must result in a JSON object")

    # id and href are owned by the server
    new_doc["id"], new_doc["href"] = current["id"], current.get("href")
    validate(new_doc, "Service")
    if new_doc != current:
        archived = history.archive(db_service, history.UPDATE, history.now())
        if archived is not None:
            session.add(archived)
    db_service.payload = new_doc
    await session.commit()
    return current, new_doc


async def delete_service(service_id: str, session: AsyncSession) -> Dict:
    """Deletes the service and returns its last document."""
    db_service = await _load(session, service_id)
    archived = history.archive(db_service, history.DELETE, history.now())
    if archived is not None:
        session.add(archived)
    await session.delete(db_service)
    await session.commit()
    return db_service.payload
