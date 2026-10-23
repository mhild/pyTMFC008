"""Unit tests for the TMF630 filter parser and SQL/JSON path renderers (no DB needed)."""
import pytest

from openapi_server.services.query.parser import FilterError, parse_query_params
from openapi_server.services.query.render import oracle_json_path, pg_jsonpath, render_condition

MAC_FILTER = "$.serviceCharacteristic[?(@.name=='mac' && @.value=='00:11:22:33:44:55')]"


def one(params):
    (path,) = parse_query_params(params)
    return path


@pytest.mark.parametrize(
    "params, expected",
    [
        ([("serviceType", "Cloud")], '$ ? (@."serviceType" == "Cloud")'),
        ([("state", "active,inactive")], '$ ? ((@."state" == "active") || (@."state" == "inactive"))'),
        (
            [("relatedParty.partyOrPartyRole.name", "Peter Meyer")],
            '$ ? (@."relatedParty"."partyOrPartyRole"."name" == "Peter Meyer")',
        ),
        ([("startDate.gte", "2024-01-01")], '$ ? (@."startDate" >= "2024-01-01")'),
        ([("startDate>", "2024-01-01")], '$ ? (@."startDate" >= "2024-01-01")'),
        ([("state.ne", "active")], '$ ? (@."state" != "active")'),
        ([("value", "300")], '$ ? ((@."value" == "300") || (@."value" == 300))'),
        ([("isEnabled", "true")], '$ ? ((@."isEnabled" == "true") || (@."isEnabled" == true))'),
        ([("@type", "Service")], '$ ? (@."@type" == "Service")'),
    ],
)
def test_attribute_filter_pg(params, expected):
    assert pg_jsonpath(one(params)) == expected


@pytest.mark.parametrize(
    "expr, expected",
    [
        (MAC_FILTER, '$."serviceCharacteristic"[*] ? ((@."name" == "mac") && (@."value" == "00:11:22:33:44:55"))'),
        (
            "$.relatedParty[?(@.partyOrPartyRole.name=='Peter Meyer')]",
            '$."relatedParty"[*] ? (@."partyOrPartyRole"."name" == "Peter Meyer")',
        ),
        ("$.feature[*].featureCharacteristic[?(@.value==true)]", '$."feature"[*]."featureCharacteristic"[*] ? (@."value" == true)'),
        ("$[?(@.state=='a' || !(@.x > 3.5))]", '$ ? ((@."state" == "a") || (!(@."x" > 3.5)))'),
        ("$['@type']", '$."@type"'),
        ("$[?(@.@type=='Service')]", '$ ? (@."@type" == "Service")'),
        ("$[?(@.endDate)]", '$ ? (exists(@."endDate"))'),
        ('$[?(@.name=="a\\"b")]', '$ ? (@."name" == "a\\"b")'),
    ],
)
def test_jsonpath_filter_pg(expr, expected):
    assert pg_jsonpath(one([("filter", expr)])) == expected


def test_oracle_uses_bind_variables_for_strings():
    path, binds = oracle_json_path(one([("filter", MAC_FILTER)]), "q0")
    assert path == '$."serviceCharacteristic"[*] ? ((@."name" == $v0) && (@."value" == $v1))'
    assert binds == {"q0_0": "mac", "q0_1": "00:11:22:33:44:55"}


def test_oracle_sql_contains_no_user_strings():
    clause = render_condition(one([("name", "x' OR 1=1 --")]), "oracle", 0)
    assert "OR 1=1" not in str(clause)
    assert 'PASSING :q0_0 AS "v0"' in str(clause)


def test_pg_sql_binds_the_whole_path():
    clause = render_condition(one([("name", "x' OR 1=1 --")]), "postgresql", 0)
    assert str(clause) == "payload @? CAST(:q0 AS jsonpath)"


def test_reserved_params_are_not_filters():
    assert parse_query_params([("fields", "id"), ("offset", "0"), ("limit", "5"), ("sort", "id")]) == []


@pytest.mark.parametrize(
    "params",
    [
        [("na'me", "x")],
        [("a..b", "x")],
        [("filter", "$.a[?(@.b == 'x')")],
        [("filter", "$.a[0]")],
        [("filter", "relatedParty")],
        [("filter", "$.a; DROP TABLE service")],
        [("filter", "$")],
    ],
)
def test_invalid_filters_are_rejected(params):
    with pytest.raises(FilterError):
        parse_query_params(params)
