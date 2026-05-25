from typing import Any


def deep_merge(base: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
    result = dict(base)
    for key, value in overlay.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def apply_env_to_project_data(
    project_data: dict[str, Any],
    env_data: dict[str, Any],
) -> dict[str, Any]:
    overlay = {key: value for key, value in env_data.items() if key != "vars"}
    if not overlay:
        return project_data
    return deep_merge(project_data, overlay)
