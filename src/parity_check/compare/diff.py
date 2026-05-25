import json
from dataclasses import dataclass, field
from typing import Any

from deepdiff import DeepDiff

from parity_check.compare.jsonpath_ignore import apply_ignore_paths
from parity_check.compare.normalize import normalize_json
from parity_check.http.runner import HttpResponse


@dataclass(frozen=True)
class ComparisonResult:
    equal: bool
    status_equal: bool
    body_equal: bool
    left_status: int
    right_status: int
    body_diff_text: str | None = None
    body_format: str = "json"
    details: list[str] = field(default_factory=list)


def _parse_body(body_text: str) -> tuple[Any | None, str]:
    if not body_text.strip():
        return None, "empty"

    try:
        return json.loads(body_text), "json"
    except json.JSONDecodeError:
        return body_text, "text"


def _format_for_diff(value: Any, body_format: str) -> str:
    if body_format == "json" and value is not None:
        return json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True)
    if value is None:
        return ""
    return str(value)


def _build_unified_style_diff(
    left_text: str,
    right_text: str,
    fromfile: str = "left",
    tofile: str = "right",
) -> str:
    import difflib

    left_lines = left_text.splitlines(keepends=True)
    right_lines = right_text.splitlines(keepends=True)
    if not left_lines and left_text:
        left_lines = [left_text]
    if not right_lines and right_text:
        right_lines = [right_text]

    diff_lines = list(
        difflib.unified_diff(
            left_lines,
            right_lines,
            fromfile=fromfile,
            tofile=tofile,
            lineterm="\n",
        )
    )
    if not diff_lines:
        return ""
    return "".join(diff_lines)


def compare_responses(
    left: HttpResponse,
    right: HttpResponse,
    ignore_paths: list[str] | None = None,
) -> ComparisonResult:
    ignore_paths = ignore_paths or []
    status_equal = left.status_code == right.status_code

    left_parsed, left_format = _parse_body(left.body_text)
    right_parsed, right_format = _parse_body(right.body_text)

    if left_format != right_format:
        body_equal = left.body_text == right.body_text
        body_diff_text = _build_unified_style_diff(left.body_text, right.body_text)
        details = [f"body format mismatch: {left_format} vs {right_format}"]
        return ComparisonResult(
            equal=status_equal and body_equal,
            status_equal=status_equal,
            body_equal=body_equal,
            left_status=left.status_code,
            right_status=right.status_code,
            body_diff_text=body_diff_text if not body_equal else None,
            body_format="mixed",
            details=details,
        )

    if left_format == "text":
        body_equal = left.body_text == right.body_text
        body_diff_text = (
            _build_unified_style_diff(left.body_text, right.body_text) if not body_equal else None
        )
        return ComparisonResult(
            equal=status_equal and body_equal,
            status_equal=status_equal,
            body_equal=body_equal,
            left_status=left.status_code,
            right_status=right.status_code,
            body_diff_text=body_diff_text,
            body_format="text",
        )

    left_filtered = apply_ignore_paths(left_parsed, ignore_paths)
    right_filtered = apply_ignore_paths(right_parsed, ignore_paths)

    left_normalized = normalize_json(left_filtered)
    right_normalized = normalize_json(right_filtered)

    structural_diff = DeepDiff(left_normalized, right_normalized, ignore_order=False)
    body_equal = not structural_diff

    body_diff_text = None
    if not body_equal:
        left_text = _format_for_diff(left_normalized, "json")
        right_text = _format_for_diff(right_normalized, "json")
        body_diff_text = _build_unified_style_diff(left_text, right_text)
        if not body_diff_text.strip():
            body_diff_text = str(structural_diff)

    return ComparisonResult(
        equal=status_equal and body_equal,
        status_equal=status_equal,
        body_equal=body_equal,
        left_status=left.status_code,
        right_status=right.status_code,
        body_diff_text=body_diff_text,
        body_format="json",
    )
