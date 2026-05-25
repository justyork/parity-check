import copy
from typing import Any

from jsonpath_ng import parse
from jsonpath_ng.exceptions import JsonPathParserError
from jsonpath_ng.jsonpath import Fields, Index

from parity_check.errors import ConfigError


def _remove_match(parent: Any, path_node: Any) -> None:
    if isinstance(path_node, Fields) and isinstance(parent, dict):
        for field_name in path_node.fields:
            parent.pop(field_name, None)
    elif isinstance(path_node, Index) and isinstance(parent, list):
        index = path_node.index
        if 0 <= index < len(parent):
            parent.pop(index)


def apply_ignore_paths(value: Any, ignore_paths: list[str]) -> Any:
    if not ignore_paths or value is None:
        return value

    result = copy.deepcopy(value)
    for path_expr in ignore_paths:
        try:
            jsonpath_expr = parse(path_expr)
        except JsonPathParserError as exc:
            raise ConfigError(f"Invalid JSONPath expression '{path_expr}': {exc}") from exc

        for match in jsonpath_expr.find(result):
            if match.context is not None:
                _remove_match(match.context.value, match.path)

    return result
