"""TMF638 event notifications (TMF630 hub/listener pattern).

Clients register a hub (`POST /hub`) with a callback URL and an optional query.
After a service was created, changed or deleted - and the change is committed -
the events are POSTed to `<callback>/listener/<eventType>` of every hub whose
query matches. Delivery is best effort: one attempt per hub, failures are logged
(no outbox, no retry).
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional
from urllib.parse import parse_qsl

import httpx
from fastapi import BackgroundTasks, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from openapi_server.database.models import Hub

logger = logging.getLogger(__name__)

CREATE = "ServiceCreateEvent"
STATE_CHANGE = "ServiceStateChangeEvent"
OPERATING_STATUS_CHANGE = "ServiceOperatingStatusChangeEvent"
ATTRIBUTE_VALUE_CHANGE = "ServiceAttributeValueChangeEvent"
DELETE = "ServiceDeleteEvent"
EVENT_TYPES = (CREATE, STATE_CHANGE, OPERATING_STATUS_CHANGE, ATTRIBUTE_VALUE_CHANGE, DELETE)

DELIVERY_TIMEOUT = 5.0  # seconds per callback

# attributes whose change has its own event type or that are no attribute values
_NOT_ATTRIBUTE_VALUES = {"state", "operatingStatus", "id", "href"}


def build_event(event_type: str, service: Dict[str, Any]) -> Dict[str, Any]:
    now = datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")
    event_id = str(uuid.uuid4())
    return {
        "@type": event_type,
        "@baseType": "Event",
        "id": event_id,
        "eventId": event_id,
        "eventType": event_type,
        "eventTime": now,
        "timeOccurred": now,
        "title": event_type,
        "event": {"service": service},
    }


def change_events(old: Dict[str, Any], new: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Events for a modified service: state, operating status and/or other attribute values changed."""
    events = []
    if old.get("state") != new.get("state"):
        events.append(build_event(STATE_CHANGE, new))
    if old.get("operatingStatus") != new.get("operatingStatus"):
        events.append(build_event(OPERATING_STATUS_CHANGE, new))
    if any(old.get(k) != new.get(k) for k in (old.keys() | new.keys()) - _NOT_ATTRIBUTE_VALUES):
        events.append(build_event(ATTRIBUTE_VALUE_CHANGE, new))
    return events


# --------------------------------------------------------------------------- #
# Hub query: "eventType=ServiceStateChangeEvent,ServiceDeleteEvent&event.service.state=active"
# --------------------------------------------------------------------------- #

def _values_at(node: Any, keys: List[str]) -> Iterable[Any]:
    """All values at a dotted path; arrays on the way are searched element-wise."""
    if isinstance(node, list):
        for item in node:
            yield from _values_at(item, keys)
    elif not keys:
        yield node
    elif isinstance(node, dict) and keys[0] in node:
        yield from _values_at(node[keys[0]], keys[1:])


def _as_text(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def parse_hub_query(query: Optional[str]) -> List[tuple]:
    """(path, accepted values) pairs; raises ValueError if the query is malformed."""
    if not query:
        return []
    terms = parse_qsl(query, keep_blank_values=True, strict_parsing=True)
    return [(name.split("."), set(value.split(","))) for name, value in terms]


def matches(query: Optional[str], event: Dict[str, Any]) -> bool:
    """All terms must match; a term matches if any value at its path equals one of its comma-separated values."""
    try:
        terms = parse_hub_query(query)
    except ValueError:
        return False
    return all(any(_as_text(v) in accepted for v in _values_at(event, path)) for path, accepted in terms)


# --------------------------------------------------------------------------- #
# Hubs and delivery
# --------------------------------------------------------------------------- #

def validate_hub(body: Dict[str, Any]) -> None:
    if not isinstance(body.get("callback"), str) or not body["callback"].startswith(("http://", "https://")):
        raise HTTPException(status_code=400, detail="$.callback: an http(s) URL is required")
    if body.get("query") is not None:
        if not isinstance(body["query"], str):
            raise HTTPException(status_code=400, detail="$.query: must be a string")
        try:
            parse_hub_query(body["query"])
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=f"$.query: {exc}")


def listener_url(callback: str, event_type: str) -> str:
    return f"{callback.rstrip('/')}/listener/{event_type[0].lower()}{event_type[1:]}"


async def _deliver(targets: List[tuple]) -> None:
    async with httpx.AsyncClient(timeout=DELIVERY_TIMEOUT) as client:
        for url, event in targets:
            try:
                response = await client.post(url, json=event)
                if response.status_code >= 300:
                    logger.warning("Event %s to %s: HTTP %s", event["eventId"], url, response.status_code)
            except httpx.HTTPError as exc:
                logger.warning("Event %s to %s failed: %r", event["eventId"], url, exc)


async def publish(events: List[Dict[str, Any]], session: AsyncSession, background_tasks: BackgroundTasks) -> None:
    """Send `events` (of a committed change) to all matching hubs after the response."""
    if not events:
        return
    hubs = (await session.execute(select(Hub))).scalars().all()
    targets = [
        (listener_url(hub.payload["callback"], event["eventType"]), event)
        for event in events
        for hub in hubs
        if matches(hub.payload.get("query"), event)
    ]
    if targets:
        background_tasks.add_task(_deliver, targets)
