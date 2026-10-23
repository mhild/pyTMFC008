"""Filters through service references (TMF638 ServiceRefOrValue).

A filter path that continues *through* a reference, e.g.

    serviceRelationship.service.serviceCharacteristic.name=mac

addresses the referenced service document. `resolve_references` marks such
places with a `Ref` node; the renderer turns a condition containing a `Ref`
into "embedded value matches  OR  referenced document (joined by id) matches".
"""

from typing import Callable, List, Optional, Tuple

from .ast import (
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
    Ref,
    Step,
    Var,
    root_filter,
)

# absolute key path of a reference -> is each key an array? (for the PG containment prefilter)
REFERENCES = {
    ("serviceRelationship", "service"): (True, False),
    ("supportingService",): (True,),
}
# attributes that only describe the reference itself - filtering on them needs no join
# (others, like name, may be on the reference or the referenced service: both are checked)
REF_FIELDS = {"id", "href", "@referredType"}

REF_ID_VAR = "ref_id"


def _resolve_steps(steps: Tuple[Step, ...], trail: Tuple[str, ...]):
    """-> (steps up to and including a dereferenced reference, (ref trail, remaining steps) or None)."""
    out: List[Step] = []
    i = 0
    while i < len(steps):
        step = steps[i]
        if isinstance(step, Key):
            trail = trail + (step.name,)
            out.append(step)
            j = i + 1
            while j < len(steps) and isinstance(steps[j], AnyElement):
                out.append(steps[j])
                j += 1
            nxt = steps[j] if j < len(steps) else None
            dereferences = isinstance(nxt, Filter) or (isinstance(nxt, Key) and nxt.name not in REF_FIELDS)
            if trail in REFERENCES and dereferences:
                return tuple(out), (trail, steps[j:])
            i = j
            continue
        if isinstance(step, Filter):
            out.append(Filter(_resolve_predicate(step.predicate, trail)))
        else:
            out.append(step)
        i += 1
    return tuple(out), None


def _target(path: Path) -> Path:
    if find_refs(resolve_references(path)):
        raise FilterError("Filters through more than one level of references are not supported")
    return path


def _resolve_predicate(pred: Predicate, trail: Tuple[str, ...]) -> Predicate:
    if isinstance(pred, Compare):
        prefix, split = _resolve_steps(pred.path.steps, trail)
        if split:
            ref_trail, rest = split
            return Ref(Path(prefix), _target(root_filter(Compare(Path(rest), pred.op, pred.value))), ref_trail)
        return Compare(Path(prefix), pred.op, pred.value)
    if isinstance(pred, Exists):
        prefix, split = _resolve_steps(pred.path.steps, trail)
        if split:
            ref_trail, rest = split
            return Ref(Path(prefix), _target(Path(rest)), ref_trail)
        return Exists(Path(prefix))
    if isinstance(pred, And):
        return And(tuple(_resolve_predicate(p, trail) for p in pred.items))
    if isinstance(pred, Or):
        return Or(tuple(_resolve_predicate(p, trail) for p in pred.items))
    if isinstance(pred, Not):
        return Not(_resolve_predicate(pred.item, trail))
    return pred


def resolve_references(path: Path) -> Path:
    """Mark the places where a filter path continues through a service reference."""
    prefix, split = _resolve_steps(path.steps, ())
    if split:
        ref_trail, rest = split
        return Path(prefix + (Filter(Ref(Path(()), _target(Path(rest)), ref_trail)),))
    return Path(prefix)


# --------------------------------------------------------------------------- #

def _map_path(path: Path, fn: Callable[[Ref], Predicate]) -> Path:
    return Path(tuple(Filter(_map_predicate(s.predicate, fn)) if isinstance(s, Filter) else s for s in path.steps))


def _map_predicate(pred: Predicate, fn: Callable[[Ref], Predicate]) -> Predicate:
    if isinstance(pred, Ref):
        return fn(pred)
    if isinstance(pred, Compare):
        return Compare(_map_path(pred.path, fn), pred.op, pred.value)
    if isinstance(pred, Exists):
        return Exists(_map_path(pred.path, fn))
    if isinstance(pred, And):
        return And(tuple(_map_predicate(p, fn) for p in pred.items))
    if isinstance(pred, Or):
        return Or(tuple(_map_predicate(p, fn) for p in pred.items))
    if isinstance(pred, Not):
        return Not(_map_predicate(pred.item, fn))
    return pred


def find_refs(path: Path) -> List[Ref]:
    found: List[Ref] = []

    def collect(ref: Ref) -> Predicate:
        found.append(ref)
        return ref

    _map_path(path, collect)
    return found


def single_ref(path: Path) -> Optional[Ref]:
    refs = find_refs(path)
    if len(refs) > 1:
        raise FilterError("Only one reference per filter condition is supported; use separate conditions")
    return refs[0] if refs else None


def embedded_variant(path: Path) -> Path:
    """The reference holds the service by value: apply the target filter in place."""
    return _map_path(path, lambda ref: Exists(Path(ref.path.steps + ref.target.steps)))


def join_variant(path: Path) -> Path:
    """The reference points to another document: match its id against $ref_id."""
    return _map_path(path, lambda ref: Compare(Path(ref.path.steps + (Key("id"),)), "==", Var(REF_ID_VAR)))
