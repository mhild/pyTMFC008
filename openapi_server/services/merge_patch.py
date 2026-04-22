# openapi_server/services/merge_patch.py

from typing import Any, Dict

def apply_merge_patch(target: Any, patch: Any) -> Any:
    # If patch is not an object, replace target entirely
    if not isinstance(patch, dict):
        return patch

    if not isinstance(target, dict):
        target = {}

    result = target.copy()
    for key, value in patch.items():
        if value is None:
            # null removes the key
            result.pop(key, None)
        else:
            if isinstance(value, dict):
                result[key] = apply_merge_patch(result.get(key, {}), value)
            else:
                result[key] = value

    return result