"""Revision history of the inventory (HISTORY_ENABLED).

With history enabled, every create, patch and delete of a service keeps the version that was current until then
in `service_history` and, for a change, makes the new document the next revision. The current version carries no
revision attributes in the API; a historised revision is returned with

    "revision": {"id": 2, "startTimestamp": "2026-10-24T10:54:00.123456Z", "endTimestamp": "..."}

separate from the business payload. `startTimestamp` is absent for a revision that predates the activation of
history (its start is unknown).

Written by the application in the transaction of the change; the row lock of the patch makes revision numbers gap-free.
"""

import os
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, Optional, Tuple

from fastapi import HTTPException

from openapi_server.database.models import Service, ServiceHistory

ENABLED = os.environ.get("HISTORY_ENABLED", "false").lower() in ("1", "true", "yes")

UPDATE = "update"
DELETE = "delete"


def now() -> datetime:
    """Current time as naive UTC (the columns are TIMESTAMP without time zone)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def iso(moment: datetime) -> str:
    return moment.isoformat(timespec="microseconds") + "Z"


def parse_timestamp(name: str, value: str) -> datetime:
    """ISO 8601 timestamp (UTC if it carries no offset) as naive UTC; 400 if invalid."""
    try:
        moment = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid {name}: {value!r} is not an ISO 8601 timestamp")
    if moment.tzinfo is not None:
        moment = moment.astimezone(timezone.utc).replace(tzinfo=None)
    return moment


def start_revision(service: Service, moment: datetime) -> None:
    """First revision of a new service."""
    if ENABLED:
        service.revision, service.rev_start = 1, moment


def archive(service: Service, operation: str, moment: datetime) -> Optional[ServiceHistory]:
    """History row for the revision `service` holds now (to be added to the session), if history is enabled.

    Afterwards `service` is advanced to the next revision (for a delete the row is removed anyway)."""
    if not ENABLED:
        return None
    # a service untouched since the activation of history has no revision yet: its (unknown-start) version becomes 1
    revision = service.revision or 1
    row = ServiceHistory(
        id=service.id,
        revision=revision,
        payload=service.payload,
        rev_start=service.rev_start,
        rev_end=moment,
        operation=operation,
    )
    service.revision, service.rev_start = revision + 1, moment
    return row


def with_revision(document: Dict[str, Any], row: ServiceHistory) -> Dict[str, Any]:
    """The document of a historised revision, including its `revision` attributes."""
    revision: Dict[str, Any] = {"id": row.revision}
    if row.rev_start is not None:
        revision["startTimestamp"] = iso(row.rev_start)
    revision["endTimestamp"] = iso(row.rev_end)
    return {**document, "revision": revision}


def parse_include_history(value: Optional[str]) -> bool:
    if value is None or value.lower() == "false":
        return False
    if value.lower() == "true":
        if not ENABLED:
            raise HTTPException(status_code=400, detail="History is not enabled (HISTORY_ENABLED)")
        return True
    raise HTTPException(status_code=400, detail="includeHistory must be true or false")


def parse_revision(value: str) -> int:
    try:
        number = int(value)
    except ValueError:
        number = 0
    if number < 1:
        raise HTTPException(status_code=400, detail="revision must be a positive integer")
    return number


def by_id_revision(include_history: Optional[str], revision: Optional[str]) -> Optional[int]:
    """Revision asked for by GET /service/{id}; None: the current document. 400 for invalid combinations."""
    included = parse_include_history(include_history)
    if revision is not None and not included:
        raise HTTPException(status_code=400, detail="revision requires includeHistory=true")
    if included and revision is None:
        raise HTTPException(status_code=400, detail="includeHistory=true requires the revision to retrieve")
    return None if revision is None else parse_revision(revision)


class Range:
    """Revisions asked for by GET /service?includeHistory=true; the timestamps limit them to a period."""

    def __init__(self, start: Optional[datetime], end: Optional[datetime]):
        self.start, self.end = start, end


def list_range(params: Iterable[Tuple[str, str]]) -> Optional[Range]:
    """Range of revisions for a list request; None: current versions only. 400 for invalid combinations."""
    values = {k: v for k, v in params if k in ("includeHistory", "revisionStartTimestamp", "revisionEndTimestamp")}
    if not parse_include_history(values.get("includeHistory")):
        if "revisionStartTimestamp" in values or "revisionEndTimestamp" in values:
            raise HTTPException(
                status_code=400, detail="revisionStartTimestamp and revisionEndTimestamp require includeHistory=true"
            )
        return None
    return Range(
        *(
            parse_timestamp(name, values[name]) if name in values else None
            for name in ("revisionStartTimestamp", "revisionEndTimestamp")
        )
    )
