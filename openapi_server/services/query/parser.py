"""Parsers for TMF630 query parameters.

* Attribute filtering:  ?serviceType=Cloud&state=active,inactive
                        ?relatedParty.partyOrPartyRole.name=Peter Meyer
                        ?startDate.gte=2024-01-01   (also: startDate>=2024-01-01)
* JSONPath filtering:   ?filter=$.serviceCharacteristic[?(@.name=='mac' && @.value=='00:11:22:33:44:55')]
* Sorting:              ?sort=-startDate,name

Both produce `Path`s (see ast.py). Every object key is validated against KEY_RE,
so nothing user-supplied but validated identifiers ends up in the path text;
values are rendered as escaped literals or bind variables by the renderers.
"""

import re
from collections import Counter
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Tuple

from .ast import (
    COMPARISON_OPS,
    And,
    AnyElement,
    Compare,
    Exists,
    Filter,
    FilterError,
    Key,
    Not,
    Or,
    Path,
    Predicate,
    Scalar,
    root_filter,
)
from .references import resolve_references

RESERVED_PARAMS = {
    "fields", "offset", "limit", "sort", "filter", "includeHistory", "revisionStartTimestamp", "revisionEndTimestamp"
}
KEY_RE = re.compile(r"^[A-Za-z_@][A-Za-z0-9_@\-]*$")

_SUFFIX_OPS = {"eq": "==", "ne": "!=", "gt": ">", "gte": ">=", "lt": "<", "lte": "<="}
# "startDate>=x" arrives as key "startDate>" with value "x"
_KEY_TAIL_OPS = {">": ">=", "<": "<=", "!": "!="}
_NUMBER_RE = re.compile(r"^-?\d+(\.\d+)?([eE][+-]?\d+)?$")


def _key(name: str) -> Key:
    if not KEY_RE.match(name):
        raise FilterError(f"Invalid attribute name: {name!r}")
    return Key(name)


# --------------------------------------------------------------------------- #
# Attribute filtering
# --------------------------------------------------------------------------- #

def _value_alternatives(raw: str, op: str) -> List[Scalar]:
    """Query values are untyped text; also match numbers/booleans stored as such."""
    if _NUMBER_RE.match(raw):
        number = float(raw) if any(c in raw for c in ".eE") else int(raw)
        return [number] if op != "==" else [raw, number]
    if op == "==" and raw in ("true", "false"):
        return [raw, raw == "true"]
    return [raw]


def _split_attribute(name: str) -> Tuple[str, List[str]]:
    """'startDate.gte' -> ('>=', ['startDate'])"""
    op = "=="
    if name and name[-1] in _KEY_TAIL_OPS:
        op, name = _KEY_TAIL_OPS[name[-1]], name[:-1]
    parts = name.split(".")
    if len(parts) > 1 and parts[-1] in _SUFFIX_OPS:
        op = _SUFFIX_OPS[parts.pop()]
    for part in parts:
        _key(part)
    return op, parts


def _leaf(path: Path, op: str, raw_value: str) -> Predicate:
    comparisons: List[Predicate] = []
    for raw in raw_value.split(","):  # comma = OR (TMF630)
        for value in _value_alternatives(raw, op):
            comparisons.append(Compare(path, op, value))
    if len(comparisons) == 1:
        return comparisons[0]
    # "!=": not equal to any of the values
    return And(tuple(comparisons)) if op == "!=" else Or(tuple(comparisons))


@dataclass
class _Node:
    leaves: List[Tuple[str, str]] = field(default_factory=list)  # (op, raw value) on this node
    children: Dict[str, "_Node"] = field(default_factory=dict)

    def leaf_count(self) -> int:
        return len(self.leaves) + sum(c.leaf_count() for c in self.children.values())


def _node_predicate(keys: Tuple[str, ...], node: _Node) -> Predicate:
    while not node.leaves and len(node.children) == 1:
        ((key, node),) = node.children.items()
        keys += (key,)
    path = tuple(Key(k) for k in keys)
    if node.leaf_count() == 1:
        ((op, raw),) = node.leaves
        return _leaf(Path(path), op, raw)
    # several conditions below a common prefix must hold for the same (array) element
    parts = [_leaf(Path(()), op, raw) for op, raw in node.leaves]
    parts += [_node_predicate((k,), child) for k, child in node.children.items()]
    return Exists(Path(path + (Filter(And(tuple(parts))),)))


def parse_attribute_filters(params: Iterable[Tuple[str, str]]) -> List[Path]:
    """Attribute filters; those sharing a path prefix are evaluated per element:
    serviceCharacteristic.name=mac&serviceCharacteristic.value=x
      -> $.serviceCharacteristic[*] ? (@.name == "mac" && @.value == "x")
    A repeated parameter name starts a separate condition (name=a&name=b: both must exist).
    """
    trees: List[_Node] = []
    occurrence: Counter = Counter()
    for name, raw_value in params:
        op, parts = _split_attribute(name)
        k = occurrence[name]
        occurrence[name] += 1
        while len(trees) <= k:
            trees.append(_Node())
        node = trees[k]
        for part in parts:
            node = node.children.setdefault(part, _Node())
        node.leaves.append((op, raw_value))

    paths: List[Path] = []
    for tree in trees:
        for key, child in tree.children.items():
            pred = _node_predicate((key,), child)
            paths.append(pred.path if isinstance(pred, Exists) else root_filter(pred))
    return paths


def parse_attribute_filter(name: str, raw_value: str) -> Path:
    (path,) = parse_attribute_filters([(name, raw_value)])
    return path


# --------------------------------------------------------------------------- #
# JSONPath filtering (Jayway-style subset used by TMF630)
# --------------------------------------------------------------------------- #

_TOKEN_RE = re.compile(
    r"""
    \s*(?:
      (?P<str>'(?:[^'\\]|\\.)*'|"(?:[^"\\]|\\.)*")
    | (?P<num>-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)
    | (?P<ident>(?:[A-Za-z_]|@(?=[A-Za-z_]))[A-Za-z0-9_@\-]*)
    | (?P<op>==|!=|<=|>=|&&|\|\||[<>!$@.\[\]()*?,])
    )""",
    re.VERBOSE,
)


def _tokenize(expr: str) -> List[Tuple[str, str]]:
    tokens, pos = [], 0
    expr = expr.strip()
    while pos < len(expr):
        m = _TOKEN_RE.match(expr, pos)
        if not m or m.end() == pos:
            raise FilterError(f"Unexpected character at position {pos}: {expr[pos:pos + 10]!r}")
        kind = m.lastgroup
        tokens.append((kind, m.group(kind)))
        pos = m.end()
    return tokens


def _unquote(token: str) -> str:
    body = token[1:-1]
    return re.sub(r"\\(.)", r"\1", body)


class _JsonPathParser:
    def __init__(self, expr: str):
        self.tokens = _tokenize(expr)
        self.i = 0

    # helpers
    def _peek(self, offset: int = 0) -> Optional[Tuple[str, str]]:
        j = self.i + offset
        return self.tokens[j] if j < len(self.tokens) else None

    def _accept(self, value: str) -> bool:
        tok = self._peek()
        if tok and tok[0] == "op" and tok[1] == value:
            self.i += 1
            return True
        return False

    def _expect(self, value: str) -> None:
        if not self._accept(value):
            tok = self._peek()
            raise FilterError(f"Expected {value!r} but found {tok[1] if tok else 'end of expression'!r}")

    # grammar
    def parse(self) -> Path:
        self._expect("$")
        path = self._steps()
        if self._peek() is not None:
            raise FilterError(f"Unexpected token {self._peek()[1]!r}")
        if not path.steps:
            raise FilterError("Empty JSONPath filter")
        return path

    def _steps(self) -> Path:
        steps = []
        while True:
            if self._accept("."):
                tok = self._peek()
                if tok and tok[0] == "op" and tok[1] == "*":
                    self.i += 1
                    steps.append(AnyElement())
                elif tok and tok[0] == "ident":
                    self.i += 1
                    steps.append(_key(tok[1]))
                else:
                    raise FilterError("Expected attribute name after '.'")
            elif self._accept("["):
                tok = self._peek()
                if self._accept("*"):
                    steps.append(AnyElement())
                elif self._accept("?"):
                    self._expect("(")
                    predicate = self._or()
                    self._expect(")")
                    steps.append(Filter(predicate))
                elif tok and tok[0] == "str":
                    self.i += 1
                    steps.append(_key(_unquote(tok[1])))
                else:
                    raise FilterError("Unsupported bracket expression (use [*], [?(...)] or ['name'])")
                self._expect("]")
            else:
                return Path(tuple(steps))

    def _or(self) -> Predicate:
        items = [self._and()]
        while self._accept("||"):
            items.append(self._and())
        return items[0] if len(items) == 1 else Or(tuple(items))

    def _and(self) -> Predicate:
        items = [self._unary()]
        while self._accept("&&"):
            items.append(self._unary())
        return items[0] if len(items) == 1 else And(tuple(items))

    def _unary(self) -> Predicate:
        if self._accept("!"):
            return Not(self._unary())
        if self._accept("("):
            inner = self._or()
            self._expect(")")
            return inner
        self._expect("@")
        path = self._steps()
        tok = self._peek()
        if tok and tok[0] == "op" and tok[1] in COMPARISON_OPS:
            self.i += 1
            return Compare(path, tok[1], self._literal())
        return Exists(path)

    def _literal(self) -> Scalar:
        tok = self._peek()
        if tok is None:
            raise FilterError("Expected a value")
        self.i += 1
        kind, text = tok
        if kind == "str":
            return _unquote(text)
        if kind == "num":
            return float(text) if any(c in text for c in ".eE") else int(text)
        if kind == "ident" and text in ("true", "false"):
            return text == "true"
        if kind == "ident" and text == "null":
            return None
        raise FilterError(f"Unsupported value {text!r}")


def parse_jsonpath_filter(expr: str) -> Path:
    return _JsonPathParser(expr).parse()


# --------------------------------------------------------------------------- #

def parse_query_params(params: Iterable[Tuple[str, str]]) -> List[Path]:
    """All filter conditions of a request; the result set must match all of them."""
    conditions: List[Path] = []
    attributes: List[Tuple[str, str]] = []
    for name, value in params:
        if name == "filter":
            conditions.append(parse_jsonpath_filter(value))
        elif name not in RESERVED_PARAMS:
            attributes.append((name, value))
    conditions += parse_attribute_filters(attributes)
    return [resolve_references(c) for c in conditions]


# --------------------------------------------------------------------------- #
# Sorting
# --------------------------------------------------------------------------- #

@dataclass(frozen=True)
class SortKey:
    keys: Tuple[str, ...]  # validated object keys, e.g. ("relatedParty", "role")
    descending: bool = False


def parse_sort(values: Iterable[str]) -> List[SortKey]:
    """sort=-startDate,name (TMF630): comma-separated attributes, "-" descending, "+" or none ascending."""
    sort_keys: List[SortKey] = []
    for value in values:
        for item in value.split(","):
            item = item.strip()
            descending = item.startswith("-")
            name = item[1:] if item[:1] in "+-" else item
            if not name:
                raise FilterError(f"Invalid sort attribute: {item!r}")
            sort_keys.append(SortKey(tuple(_key(part).name for part in name.split(".")), descending))
    return sort_keys
