from typing import Any


def normalize_json(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: normalize_json(item) for key, item in sorted(value.items())}
    if isinstance(value, list):
        return [normalize_json(item) for item in value]
    return value
