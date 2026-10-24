"""Revision history: parameter checks and bookkeeping, no API and no database."""
import uuid
from datetime import datetime

import pytest
from fastapi import HTTPException

from openapi_server.database.models import Service, ServiceHistory
from openapi_server.services import history
from openapi_server.services.query.ast import FilterError
from openapi_server.services.service import list_statements


@pytest.fixture
def enabled(monkeypatch):
    monkeypatch.setattr(history, "ENABLED", True)


def status(call, *args):
    with pytest.raises(HTTPException) as caught:
        call(*args)
    return caught.value.status_code


def test_list_range_without_history_is_none(enabled):
    assert history.list_range([("state", "active")]) is None
    assert history.list_range([("includeHistory", "false")]) is None


def test_list_range_parses_the_period(enabled):
    rng = history.list_range([
        ("includeHistory", "true"),
        ("revisionStartTimestamp", "2026-10-24T10:00:00Z"),
        ("revisionEndTimestamp", "2026-10-24T14:00:00+02:00"),
    ])
    assert rng.start == datetime(2026, 10, 24, 10, 0) and rng.end == datetime(2026, 10, 24, 12, 0)  # UTC
    assert history.list_range([("includeHistory", "true"), ("revisionStartTimestamp", "2026-10-24")]).start == datetime(2026, 10, 24)


@pytest.mark.parametrize(
    "params",
    [
        [("includeHistory", "maybe")],
        [("revisionStartTimestamp", "2026-10-24T10:00:00Z")],  # needs includeHistory=true
        [("includeHistory", "false"), ("revisionEndTimestamp", "2026-10-24T10:00:00Z")],
        [("includeHistory", "true"), ("revisionStartTimestamp", "yesterday")],
    ],
)
def test_list_range_rejects(enabled, params):
    assert status(history.list_range, params) == 400


def test_include_history_needs_the_setting(monkeypatch):
    monkeypatch.setattr(history, "ENABLED", False)
    assert status(history.list_range, [("includeHistory", "true")]) == 400
    assert history.list_range([("includeHistory", "false")]) is None


def test_by_id_revision(enabled):
    assert history.by_id_revision(None, None) is None
    assert history.by_id_revision("true", "3") == 3
    for include, revision in [("true", None), (None, "1"), ("false", "1"), ("true", "0"), ("true", "x")]:
        assert status(history.by_id_revision, include, revision) == 400


def test_filters_through_references_are_not_supported_on_history(enabled):
    with pytest.raises(FilterError):
        list_statements([("includeHistory", "true"), ("serviceRelationship.service.state", "active")], "postgresql", 0, 10)


@pytest.mark.parametrize("dialect", ["postgresql", "oracle"])
def test_history_statements_cover_both_tables(enabled, dialect):
    count, page, joins = list_statements([("includeHistory", "true"), ("state", "active")], dialect, 0, 10)
    assert joins is False
    for stmt in (count, page):
        sql = str(stmt.compile(compile_kwargs={"render_postcompile": True}))
        assert "UNION ALL" in sql and "service_history" in sql


def test_archive_advances_the_revision(enabled):
    moment, earlier = datetime(2026, 10, 24, 12), datetime(2026, 10, 24, 10)
    service = Service(id=uuid.uuid4(), payload={"state": "active"}, revision=2, rev_start=earlier)
    row = history.archive(service, history.UPDATE, moment)
    assert (row.revision, row.rev_start, row.rev_end, row.operation) == (2, earlier, moment, "update")
    assert (service.revision, service.rev_start) == (3, moment)


def test_archive_of_a_service_untouched_since_activation(enabled):
    """No revision yet: its version becomes revision 1 with an unknown start."""
    moment = datetime(2026, 10, 24, 12)
    service = Service(id=uuid.uuid4(), payload={"state": "active"})
    row = history.archive(service, history.DELETE, moment)
    assert (row.revision, row.rev_start, row.operation) == (1, None, "delete")
    assert (service.revision, service.rev_start) == (2, moment)
    assert "startTimestamp" not in history.with_revision(row.payload, row)["revision"]


def test_archive_is_a_no_op_when_disabled(monkeypatch):
    monkeypatch.setattr(history, "ENABLED", False)
    service = Service(id=uuid.uuid4(), payload={})
    assert history.archive(service, history.UPDATE, datetime.now()) is None and service.revision is None
    history.start_revision(service, datetime.now())
    assert service.revision is None


def test_with_revision_separates_the_revision_data():
    row = ServiceHistory(revision=2, rev_start=datetime(2026, 10, 24, 10, 0, 0, 5), rev_end=datetime(2026, 10, 24, 11))
    doc = history.with_revision({"name": "a"}, row)
    assert doc == {
        "name": "a",
        "revision": {"id": 2, "startTimestamp": "2026-10-24T10:00:00.000005Z", "endTimestamp": "2026-10-24T11:00:00.000000Z"},
    }
