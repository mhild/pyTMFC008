"""Render filter `Path`s into index-friendly SQL for PostgreSQL and Oracle.

PostgreSQL:  payload @? CAST(:q0 AS jsonpath)
             The whole jsonpath (with JSON-escaped literals) is one bind parameter.
             The @? operator - unlike jsonb_path_exists() - can use the
             GIN (jsonb_path_ops) index for == comparisons.
Oracle:      JSON_EXISTS(payload, '$?(@."state" == $v0)' PASSING :q0_0 AS "v0")
             Oracle requires the path as a literal; it is generated from validated
             keys and fixed tokens only, string values are passed as bind variables.
             Can use multivalue indexes.

A condition through a service reference (see references.py) becomes

    service.id IN (SELECT s.id FROM service s WHERE <embedded value matches>
                   UNION
                   SELECT s.id FROM service s JOIN service t ON <s references t>
                   WHERE <t matches>)          (PostgreSQL: = ANY(ARRAY(...)))

so both the referenced documents (t) and the referencing ones (s, by the id
of t) are found via index. The subquery is evaluated once, not per row.

Oracle multivalue indexes reject object values, so characteristic values are
indexed on the shadow column `search` (a trigger copies the characteristics
without objects, see migration c5d7e9f1a2b4). A condition that only compares
characteristic names/values with constants is checked on both columns:

    JSON_EXISTS(search, '<path>') AND JSON_EXISTS(payload, '<path>')

The first uses the index; it can't miss a match, since a scalar never equals an
object. The second gives the exact result.

Sorting (render_sort) orders by every sort attribute twice: JSON numbers
numerically, then the value as text in byte order - the same order on both
backends (Oracle's JSON_VALUE alone would compare numbers as text).
"""

import json
from typing import Callable, Dict, List, Optional, Tuple

from sqlalchemy import TextClause, text

from .ast import And, AnyElement, Compare, Exists, Filter, Key, Not, Or, Path, Predicate, Ref, Scalar, Var
from .parser import SortKey
from .references import REF_ID_VAR, REFERENCES, embedded_variant, join_variant, single_ref


def _path_text(path: Path, start: str, literal: Callable[[Scalar], str]) -> str:
    out = start
    previous = None
    for step in path.steps:
        if isinstance(step, Key):
            out += f'."{step.name}"'  # names are validated against KEY_RE
        elif isinstance(step, AnyElement):
            out += "[*]"
        elif isinstance(step, Filter):
            if isinstance(previous, Key):
                # Evaluate the filter per array element. Without [*] Oracle applies
                # it to the array as a whole, so `@.name == a && @.value == b` would
                # also match name and value taken from *different* elements.
                out += "[*]"
            out += f" ? ({_predicate_text(step.predicate, literal)})"
        previous = step
    return out


def _predicate_text(pred: Predicate, literal: Callable[[Scalar], str]) -> str:
    if isinstance(pred, Compare):
        return f"{_path_text(pred.path, '@', literal)} {pred.op} {literal(pred.value)}"
    if isinstance(pred, Exists):
        return f"exists({_path_text(pred.path, '@', literal)})"
    if isinstance(pred, And):
        return " && ".join(f"({_predicate_text(p, literal)})" for p in pred.items)
    if isinstance(pred, Or):
        return " || ".join(f"({_predicate_text(p, literal)})" for p in pred.items)
    if isinstance(pred, Not):
        return f"!({_predicate_text(pred.item, literal)})"
    if isinstance(pred, Ref):
        raise ValueError("Unresolved reference; render via render_condition()")
    raise TypeError(f"Unknown predicate {pred!r}")


def _constant(value: Scalar) -> str:
    """Literal text for non-string scalars (safe: generated from Python values)."""
    if isinstance(value, Var):
        return f"${value.name}"
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    return repr(value)


def pg_jsonpath(path: Path) -> str:
    def literal(value: Scalar) -> str:
        if isinstance(value, str):
            return json.dumps(value, ensure_ascii=False)
        return _constant(value)

    return _path_text(path, "$", literal)


def oracle_json_path(path: Path, bind_prefix: str) -> Tuple[str, Dict[str, str]]:
    binds: Dict[str, str] = {}

    def literal(value: Scalar) -> str:
        if isinstance(value, str):
            n = len(binds)
            binds[f"{bind_prefix}_{n}"] = value
            return f"$v{n}"
        return _constant(value)

    return _path_text(path, "$", literal), binds


# characteristic arrays copied into Oracle's `search` column
_SEARCH_CHARACTERISTICS = (
    ("serviceCharacteristic",),
    ("serviceRelationship", "service", "serviceCharacteristic"),
    ("supportingService", "serviceCharacteristic"),
)
_SEARCH_VALUE_PATHS = {c + ("value",) for c in _SEARCH_CHARACTERISTICS}
_SEARCH_PATHS = _SEARCH_VALUE_PATHS | {c + ("name",) for c in _SEARCH_CHARACTERISTICS}


def _compared_paths(path: Path, prefix: Tuple[str, ...]) -> Optional[Tuple[List[Tuple[str, ...]], Tuple[str, ...]]]:
    """(absolute key paths compared with constants, key path at the end of `path`);
    None if a filter uses anything but comparisons with constants."""
    found: List[Tuple[str, ...]] = []
    keys = prefix
    for step in path.steps:
        if isinstance(step, Key):
            keys += (step.name,)
        elif isinstance(step, Filter):
            inner = _predicate_compared_paths(step.predicate, keys)
            if inner is None:
                return None
            found += inner
    return found, keys


def _predicate_compared_paths(pred: Predicate, prefix: Tuple[str, ...]) -> Optional[List[Tuple[str, ...]]]:
    if isinstance(pred, Compare):
        result = None if isinstance(pred.value, Var) else _compared_paths(pred.path, prefix)
        return None if result is None else result[0] + [result[1]]
    if isinstance(pred, (And, Or)):
        found: List[Tuple[str, ...]] = []
        for item in pred.items:
            inner = _predicate_compared_paths(item, prefix)
            if inner is None:
                return None
            found += inner
        return found
    if isinstance(pred, Exists) and pred.path.steps and isinstance(pred.path.steps[-1], Filter):
        # an element matching the filter (e.g. an embedded service's characteristic) is in `search` as well
        result = _compared_paths(pred.path, prefix)
        return None if result is None else result[0]
    return None  # other Exists, Not, Ref: an object removed from `search` could change the result


def uses_search_column(path: Path) -> bool:
    """Oracle: can `path` also be checked on the `search` column (and use its characteristic value indexes)?"""
    if not path.steps or not isinstance(path.steps[-1], Filter):
        return False
    result = _compared_paths(path, ())
    if result is None:
        return False
    found = result[0]
    return all(p in _SEARCH_PATHS for p in found) and any(p in _SEARCH_VALUE_PATHS for p in found)


def _exists_sql(path: Path, dialect: str, bind: str, column: str, extra_passing: str = "") -> Tuple[str, Dict]:
    """SQL condition "document in `column` matches `path`" and its bind values."""
    if dialect == "postgresql":
        if extra_passing:  # path variables -> jsonb_path_exists (operators take no variables)
            return f"jsonb_path_exists({column}, CAST(:{bind} AS jsonpath), {extra_passing})", {bind: pg_jsonpath(path)}
        return f"{column} @? CAST(:{bind} AS jsonpath)", {bind: pg_jsonpath(path)}
    if dialect == "oracle":
        json_path, binds = oracle_json_path(path, bind)
        passing = [f':{name} AS "v{i}"' for i, name in enumerate(binds)]
        if extra_passing:
            passing.append(extra_passing)
        passing_sql = f" PASSING {', '.join(passing)}" if passing else ""
        sql = f"JSON_EXISTS({column}, '{json_path}'{passing_sql})"
        if column.endswith("payload") and uses_search_column(path):
            search_column = column[: -len("payload")] + "search"
            sql = f"(JSON_EXISTS({search_column}, '{json_path}'{passing_sql}) AND {sql})"
        return sql, binds
    raise ValueError(f"Unsupported database dialect: {dialect}")


def _pg_reference_document(ref: Ref, id_expr: str) -> str:
    """jsonb a referencing document must contain, e.g. {"serviceRelationship":[{"service":{"id": ...}}]}"""
    doc = f"jsonb_build_object('id', {id_expr})"
    for key, is_array in reversed(list(zip(ref.trail, REFERENCES[ref.trail]))):
        doc = f"jsonb_build_object('{key}', {f'jsonb_build_array({doc})' if is_array else doc})"
    return doc


def _reference_sql(path: Path, ref: Ref, dialect: str, bind: str) -> Tuple[str, Dict]:
    embedded_sql, binds = _exists_sql(embedded_variant(path), dialect, f"{bind}e", "s1.payload")
    target_sql, target_binds = _exists_sql(ref.target, dialect, f"{bind}t", "t2.payload")
    if dialect == "postgresql":
        ref_id = "t2.payload -> 'id'"
        # containment is indexable (GIN), the exact element-wise check follows
        join_sql = f"s2.payload @> {_pg_reference_document(ref, ref_id)} AND " + _exists_sql(
            join_variant(path), dialect, f"{bind}j", "s2.payload", f"jsonb_build_object('{REF_ID_VAR}', {ref_id})"
        )[0]
        join_binds = {f"{bind}j": pg_jsonpath(join_variant(path))}
    else:
        join_sql, join_binds = _exists_sql(
            join_variant(path), dialect, f"{bind}j", "s2.payload", f"JSON_VALUE(t2.payload, '$.id') AS \"{REF_ID_VAR}\""
        )
    subquery = (
        f"SELECT s1.id FROM service s1 WHERE {embedded_sql} "
        f"UNION SELECT s2.id FROM service s2 JOIN service t2 ON {join_sql} WHERE {target_sql}"
    )
    if dialect == "postgresql":
        # Evaluated once (InitPlan), then looked up via the primary key. With IN (...)
        # PostgreSQL - lacking statistics for JSON paths - hash-joins all service ids.
        sql = f"service.id = ANY(ARRAY({subquery}))"
    else:
        # Left to itself Oracle unnests the subquery into a correlated filter that probes the referenced
        # services once per candidate row (minutes on 1M rows). ROWNUM keeps it a view that is evaluated once,
        # HASH_SJ joins it to the candidates with a hash semi join instead of one index probe per result id.
        sql = f"service.id IN (SELECT /*+ HASH_SJ */ id FROM ({subquery}) WHERE ROWNUM > 0)"
    return sql, {**binds, **target_binds, **join_binds}


def render_condition(path: Path, dialect: str, index: int, column: str = "payload") -> TextClause:
    bind = f"q{index}"
    ref = single_ref(path)
    if ref is None:
        sql, binds = _exists_sql(path, dialect, bind, column)
    else:
        sql, binds = _reference_sql(path, ref, dialect, bind)
    return text(sql).bindparams(**binds)


def needs_join(paths: List[Path]) -> bool:
    return any(single_ref(p) is not None for p in paths)


def _sort_expressions(sort_key: SortKey, dialect: str, column: str) -> List[str]:
    # keys are validated against KEY_RE, so they can't break out of the literal
    if dialect == "postgresql":
        pg_path = "'{" + ",".join(f'"{k}"' for k in sort_key.keys) + "}'"
        value_type = f"jsonb_typeof({column} #> {pg_path})"
        number = f"CASE WHEN {value_type} = 'number' THEN ({column} #>> {pg_path})::numeric END"
        scalar = f"CASE WHEN {value_type} IN ('string', 'number', 'boolean') THEN {column} #>> {pg_path} END"
        return [number, f'({scalar}) COLLATE "C"']
    if dialect == "oracle":
        # lax mode steps into arrays, PostgreSQL's #> doesn't: sorting through arrays is undefined
        json_path = "$" + "".join(f'."{k}"' for k in sort_key.keys)
        number = f"JSON_VALUE({column}, '{json_path} ? (@.type() == \"number\")' RETURNING NUMBER NULL ON ERROR)"
        return [number, f"NLSSORT(JSON_VALUE({column}, '{json_path}' RETURNING VARCHAR2(4000) NULL ON ERROR), 'NLS_SORT=BINARY')"]
    raise ValueError(f"Unsupported database dialect: {dialect}")


def render_sort(sort_keys: List[SortKey], dialect: str, column: str = "service.payload") -> List[TextClause]:
    """ORDER BY items for `sort`; values missing (or not scalar) sort last in both directions."""
    clauses = []
    for sort_key in sort_keys:
        direction = "DESC" if sort_key.descending else "ASC"
        clauses += [text(f"{expr} {direction} NULLS LAST") for expr in _sort_expressions(sort_key, dialect, column)]
    return clauses


def render_conditions(paths: List[Path], dialect: str) -> List[TextClause]:
    return [render_condition(p, dialect, i) for i, p in enumerate(paths)]
