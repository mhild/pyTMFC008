"""Validate service documents against the TMF638 v5 schemas of the OpenAPI spec.

The spec models polymorphism as `oneOf` + `discriminator`. Plain JSON Schema ignores
the discriminator, and several `oneOf` branches are structurally identical (PartyRef
and PartyRoleRef, ...), so a valid document would match "more than one" schema.
When loading the spec, every such `oneOf` is rewritten into a dispatch on `@type`:
the `@type` must be one of the mapping's keys and the document is validated against
the schema mapped to it.
"""

from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012

SPEC_FILE = Path(__file__).resolve().parents[2] / "api_specs" / "TMF638-Service_Inventory_Management-v5.0.0.oas.yaml"
SPEC_URI = "urn:tmf638"

format_checker = FormatChecker()


@format_checker.checks("date-time", raises=ValueError)
def _is_date_time(value: Any) -> bool:
    # jsonschema checks date-time only with the optional rfc3339-validator package
    if not isinstance(value, str) or "T" not in value.upper():
        return False
    datetime.fromisoformat(value)  # Python 3.11+ accepts RFC 3339 incl. "Z"
    return True


def _dispatch_on_type(node: Any) -> Any:
    if isinstance(node, list):
        return [_dispatch_on_type(item) for item in node]
    if not isinstance(node, dict):
        return node
    node = {key: _dispatch_on_type(value) for key, value in node.items()}
    mapping = (node.get("discriminator") or {}).get("mapping")
    if "oneOf" in node and mapping:
        del node["oneOf"]
        prop = node["discriminator"]["propertyName"]
        node["required"] = sorted(set(node.get("required", [])) | {prop})
        node.setdefault("properties", {})[prop] = {"enum": sorted(mapping)}
        node["allOf"] = node.get("allOf", []) + [
            {"if": {"properties": {prop: {"const": name}}}, "then": {"$ref": ref}} for name, ref in mapping.items()
        ]
    return node


@lru_cache(maxsize=None)
def _registry() -> Registry:
    with open(SPEC_FILE, encoding="utf-8") as f:
        spec = _dispatch_on_type(yaml.safe_load(f))
    return Registry().with_resource(SPEC_URI, Resource.from_contents(spec, default_specification=DRAFT202012))


@lru_cache(maxsize=None)
def _validator(schema_name: str) -> Draft202012Validator:
    schema = {"$ref": f"{SPEC_URI}#/components/schemas/{schema_name}"}
    return Draft202012Validator(schema, registry=_registry(), format_checker=format_checker)


def first_error(document: Any, schema_name: str) -> Optional[str]:
    """None if `document` is valid against the named spec schema, else a description of the first error."""
    errors = sorted(_validator(schema_name).iter_errors(document), key=lambda e: list(e.absolute_path))
    if not errors:
        return None
    return f"{errors[0].json_path}: {errors[0].message}"


def warm_up() -> Dict[str, Draft202012Validator]:
    """Load the spec at startup instead of on the first request."""
    return {name: _validator(name) for name in ("Service_FVO", "Service")}
