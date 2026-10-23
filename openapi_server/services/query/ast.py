"""Small AST for TMF630 filters, rendered to SQL/JSON path by the dialect renderers.

A filter is a `Path` that must exist in the document (SQL: jsonb @? / JSON_EXISTS).
Paths start at the document root; `Filter` steps carry a predicate evaluated
relative to the current item (`@`).
"""

from dataclasses import dataclass
from typing import Tuple, Union

Scalar = Union[str, int, float, bool, None]

COMPARISON_OPS = ("==", "!=", "<", "<=", ">", ">=")


@dataclass(frozen=True)
class Key:
    name: str


@dataclass(frozen=True)
class AnyElement:
    """`[*]` – every element of an array."""


@dataclass(frozen=True)
class Filter:
    predicate: "Predicate"


Step = Union[Key, AnyElement, Filter]


@dataclass(frozen=True)
class Path:
    steps: Tuple[Step, ...] = ()


@dataclass(frozen=True)
class Compare:
    path: Path  # relative to `@`
    op: str
    value: Scalar


@dataclass(frozen=True)
class Exists:
    path: Path  # relative to `@`


@dataclass(frozen=True)
class And:
    items: Tuple["Predicate", ...]


@dataclass(frozen=True)
class Or:
    items: Tuple["Predicate", ...]


@dataclass(frozen=True)
class Not:
    item: "Predicate"


Predicate = Union[Compare, Exists, And, Or, Not]


def root_filter(predicate: Predicate) -> Path:
    """`$ ? (predicate)` – the document itself must satisfy the predicate."""
    return Path((Filter(predicate),))
