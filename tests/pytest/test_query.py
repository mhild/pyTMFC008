"""Unit tests for the TMF630 filter parser and SQL/JSON path renderers (no DB needed)."""
import pytest

from openapi_server.services.query.parser import FilterError, SortKey, parse_query_params, parse_sort
from openapi_server.services.query.references import embedded_variant, join_variant, single_ref
from openapi_server.services.query.render import oracle_json_path, pg_jsonpath, render_condition, render_sort

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


# --- attribute filters sharing a prefix are evaluated per element ---------------

@pytest.mark.parametrize(
    "params, expected",
    [
        (
            [("serviceCharacteristic.name", "mac"), ("serviceCharacteristic.value", "x")],
            ['$."serviceCharacteristic"[*] ? ((@."name" == "mac") && (@."value" == "x"))'],
        ),
        (
            [("relatedParty.role", "user"), ("relatedParty.partyOrPartyRole.name", "Peter Meyer")],
            ['$."relatedParty"[*] ? ((@."role" == "user") && (@."partyOrPartyRole"."name" == "Peter Meyer"))'],
        ),
        (
            [("serviceType", "Cloud"), ("state", "active")],
            ['$ ? (@."serviceType" == "Cloud")', '$ ? (@."state" == "active")'],
        ),
        (
            [("serviceCharacteristic.name", "mac"), ("serviceCharacteristic.name", "vlan")],
            ['$ ? (@."serviceCharacteristic"."name" == "mac")', '$ ? (@."serviceCharacteristic"."name" == "vlan")'],
        ),
    ],
)
def test_attribute_filters_grouped_by_prefix(params, expected):
    assert [pg_jsonpath(p) for p in parse_query_params(params)] == expected


# --- filters through service references -----------------------------------------

REL_PARAMS = [
    ("serviceRelationship.relationshipType", "DependentOn"),
    ("serviceRelationship.service.serviceCharacteristic.name", "mac"),
    ("serviceRelationship.service.serviceCharacteristic.value", "x"),
]


def test_reference_is_resolved():
    (path,) = parse_query_params(REL_PARAMS)
    ref = single_ref(path)
    assert ref.trail == ("serviceRelationship", "service")
    assert pg_jsonpath(ref.target) == '$."serviceCharacteristic"[*] ? ((@."name" == "mac") && (@."value" == "x"))'
    assert pg_jsonpath(join_variant(path)) == (
        '$."serviceRelationship"[*] ? ((@."relationshipType" == "DependentOn") && (@."service"."id" == $ref_id))'
    )
    assert pg_jsonpath(embedded_variant(path)) == (
        '$."serviceRelationship"[*] ? ((@."relationshipType" == "DependentOn") && '
        '(exists(@."service"."serviceCharacteristic"[*] ? ((@."name" == "mac") && (@."value" == "x")))))'
    )


def test_jsonpath_and_attribute_syntax_resolve_alike():
    (attr,) = parse_query_params(REL_PARAMS[1:])
    (jp,) = parse_query_params(
        [("filter", "$.serviceRelationship[?(@.service.serviceCharacteristic[?(@.name=='mac' && @.value=='x')])]")]
    )
    assert single_ref(attr).target == single_ref(jp).target
    assert single_ref(attr).trail == single_ref(jp).trail
    # different but equivalent paths to the reference id
    assert pg_jsonpath(join_variant(attr)) == '$."serviceRelationship"."service"[*] ? (@."id" == $ref_id)'
    assert pg_jsonpath(join_variant(jp)) == '$."serviceRelationship"[*] ? (@."service"."id" == $ref_id)'


@pytest.mark.parametrize("dialect", ["postgresql", "oracle"])
def test_reference_sql_joins_by_id(dialect):
    (path,) = parse_query_params(REL_PARAMS)
    sql = str(render_condition(path, dialect, 0))
    prefix = "service.id = ANY(ARRAY(" if dialect == "postgresql" else "service.id IN ("
    assert sql.startswith(prefix + "SELECT s1.id FROM service s1 WHERE ")
    assert " UNION SELECT s2.id FROM service s2 JOIN service t2 ON " in sql
    assert "'x'" not in sql and '"x"' not in sql  # values are bound
    if dialect == "postgresql":
        assert "s2.payload @> jsonb_build_object('serviceRelationship', jsonb_build_array(" in sql
    else:
        assert "JSON_VALUE(t2.payload, '$.id') AS \"ref_id\"" in sql


@pytest.mark.parametrize(
    "params, joins",
    [
        ([("serviceRelationship.service.id", "1")], False),
        ([("serviceRelationship.service.href", "h")], False),
        ([("serviceRelationship.service.name", "B")], True),
        ([("supportingService.state", "active")], True),
        ([("serviceRelationship.relationshipType", "DependentOn")], False),
    ],
)
def test_join_only_when_dereferencing(params, joins):
    (path,) = parse_query_params(params)
    assert (single_ref(path) is not None) == joins


def test_nested_references_are_rejected():
    with pytest.raises(FilterError):
        parse_query_params([("serviceRelationship.service.supportingService.name", "x")])


@pytest.mark.parametrize(
    "values, expected",
    [
        (["name"], [SortKey(("name",))]),
        (["-startDate,+name"], [SortKey(("startDate",), True), SortKey(("name",))]),
        ([" name"], [SortKey(("name",))]),  # "+name" arrives URL-decoded as " name"
        (["relatedParty.role", "-@type"], [SortKey(("relatedParty", "role")), SortKey(("@type",), True)]),
    ],
)
def test_parse_sort(values, expected):
    assert parse_sort(values) == expected


@pytest.mark.parametrize("value", ["", "-", "a..b", "na'me", "name,", "a[0]"])
def test_invalid_sort_is_rejected(value):
    with pytest.raises(FilterError):
        parse_sort([value])


@pytest.mark.parametrize(
    "dialect, expected",
    [
        (
            "postgresql",
            [
                "CASE WHEN jsonb_typeof(service.payload #> '{\"a\",\"b\"}') = 'number' "
                "THEN (service.payload #>> '{\"a\",\"b\"}')::numeric END DESC NULLS LAST",
                "(CASE WHEN jsonb_typeof(service.payload #> '{\"a\",\"b\"}') IN ('string', 'number', 'boolean') "
                "THEN service.payload #>> '{\"a\",\"b\"}' END) COLLATE \"C\" DESC NULLS LAST",
            ],
        ),
        (
            "oracle",
            [
                "JSON_VALUE(service.payload, '$.\"a\".\"b\" ? (@.type() == \"number\")' RETURNING NUMBER NULL ON ERROR) "
                "DESC NULLS LAST",
                "NLSSORT(JSON_VALUE(service.payload, '$.\"a\".\"b\"' RETURNING VARCHAR2(4000) NULL ON ERROR), "
                "'NLS_SORT=BINARY') DESC NULLS LAST",
            ],
        ),
    ],
)
def test_render_sort(dialect, expected):
    assert [c.text for c in render_sort([SortKey(("a", "b"), True)], dialect)] == expected
