"""Render filter `Path`s into index-friendly SQL for PostgreSQL and Oracle.

PostgreSQL:  payload @? CAST(:q0 AS jsonpath)
             The whole jsonpath (with JSON-escaped literals) is one bind parameter.
             The @? operator - unlike jsonb_path_exists() - can use the
             GIN (jsonb_path_ops) index for == comparisons.
Oracle:      JSON_EXISTS(payload, '$?(@."state" == $v0)' PASSING :q0_0 AS "v0")
             Oracle requires the path as a literal; it is generated from validated
             keys and fixed tokens only, string values are passed as bind variables.
             Can use the JSON search index.
"""

import json
from typing import Callable, Dict, List

from sqlalchemy import TextClause, text

from .ast import And, AnyElement, Compare, Exists, Filter, Key, Not, Or, Path, Predicate, Scalar


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
    raise TypeError(f"Unknown predicate {pred!r}")


def _constant(value: Scalar) -> str:
    """Literal text for non-string scalars (safe: generated from Python values)."""
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


def oracle_json_path(path: Path, bind_prefix: str) -> "tuple[str, Dict[str, str]]":
    binds: Dict[str, str] = {}

    def literal(value: Scalar) -> str:
        if isinstance(value, str):
            n = len(binds)
            binds[f"{bind_prefix}_{n}"] = value
            return f"$v{n}"
        return _constant(value)

    return _path_text(path, "$", literal), binds


def render_condition(path: Path, dialect: str, index: int, column: str = "payload") -> TextClause:
    bind = f"q{index}"
    if dialect == "postgresql":
        return text(f"{column} @? CAST(:{bind} AS jsonpath)").bindparams(**{bind: pg_jsonpath(path)})
    if dialect == "oracle":
        json_path, binds = oracle_json_path(path, bind)
        passing = ", ".join(f':{name} AS "v{i}"' for i, name in enumerate(binds))
        sql = f"JSON_EXISTS({column}, '{json_path}'" + (f" PASSING {passing}" if passing else "") + ")"
        return text(sql).bindparams(**binds)
    raise ValueError(f"Unsupported database dialect: {dialect}")


def render_conditions(paths: List[Path], dialect: str) -> List[TextClause]:
    return [render_condition(p, dialect, i) for i, p in enumerate(paths)]
