import re

from parity_check.errors import ConfigError

_TAG_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


def normalize_tags(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        items = [value]
    elif isinstance(value, list):
        items = value
    else:
        raise ValueError("tags must be a string or a list of strings")

    normalized: list[str] = []
    seen: set[str] = set()
    for item in items:
        if not isinstance(item, str):
            raise ValueError("each tag must be a string")
        tag = item.strip()
        if not tag:
            raise ValueError("tag must be non-empty")
        if not _TAG_PATTERN.match(tag):
            raise ValueError(
                f"invalid tag '{tag}': use letters, digits, '.', '-', '_' "
                "(must start with a letter or digit)"
            )
        if tag not in seen:
            seen.add(tag)
            normalized.append(tag)
    return normalized


def request_matches_tags(request_tags: list[str], filter_tags: list[str]) -> bool:
    if not filter_tags:
        return True
    if not request_tags:
        return False
    request_set = set(request_tags)
    return any(tag in request_set for tag in filter_tags)


def collect_tags(requests: list) -> set[str]:
    tags: set[str] = set()
    for request in requests:
        tags.update(request.tags)
    return tags


def raise_no_matching_tags(
    request_id: str | None,
    filter_tags: list[str],
    project_requests: list,
) -> None:
    available = collect_tags(project_requests)
    raise ConfigError(_no_match_message(request_id, filter_tags, available))


def _no_match_message(
    request_id: str | None,
    filter_tags: list[str],
    available: set[str],
) -> str:
    tag_list = ", ".join(filter_tags)
    if request_id is not None:
        prefix = f"No request '{request_id}'"
    else:
        prefix = "No requests"
    message = f"{prefix} with tag(s) {tag_list} in this project."
    if available:
        sorted_tags = ", ".join(sorted(available))
        message += f" Available tags: {sorted_tags}."
    else:
        message += " No tags defined on any request."
    return message
