"""The Oracle `search` column: a JSON_TRANSFORM of the payload without object values (see migration c5d7e9f1a2b4)."""

# characteristic arrays of the service and of services embedded by value in a reference:
# index name -> (path for the index, JSON path of the characteristics)
CHARACTERISTICS = {
    "ix_service_char_value": ("serviceCharacteristic", "$.serviceCharacteristic[*]"),
    "ix_svc_rel_char_value": (
        "serviceRelationship.service.serviceCharacteristic",
        "$.serviceRelationship[*].service.serviceCharacteristic[*]",
    ),
    "ix_svc_sup_char_value": ("supportingService.serviceCharacteristic", "$.supportingService[*].serviceCharacteristic[*]"),
}


def search_document(column: str) -> str:
    """JSON_TRANSFORM of `column` into the search document."""
    paths = [json_path for _, json_path in CHARACTERISTICS.values()]
    keep = ", ".join(f"'{p}.{key}'" for p in paths for key in ("name", "value"))
    removes = []
    for p in paths:
        # objects and nested arrays inside an array value; the filter on the array type is needed,
        # in lax mode `value[*]` also addresses a scalar value itself
        removes.append(f"""REMOVE '{p}?(@.value.type() == "array").value[*]?(@.type() == "object" || @.type() == "array")' IGNORE ON MISSING""")
        removes.append(f"""REMOVE '{p}?(@.value.type() == "object").value' IGNORE ON MISSING""")
    return f"JSON_TRANSFORM({column}, KEEP {keep}, {', '.join(removes)} RETURNING JSON)"
