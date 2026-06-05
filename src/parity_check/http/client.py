from typing import Any
from urllib.parse import urlencode, urljoin

from parity_check.config.models import HttpMethod, ProjectConfig, RequestConfig, SideOverride
from parity_check.errors import ConfigError


def _merge_headers(
    defaults: dict[str, str],
    request_headers: dict[str, str],
    side_headers: dict[str, str] | None,
) -> dict[str, str]:
    merged = dict(defaults)
    merged.update(request_headers)
    if side_headers:
        merged.update(side_headers)
    return merged


def _merge_query(
    request_query: dict[str, str],
    side_query: dict[str, str] | None,
) -> dict[str, str]:
    merged = dict(request_query)
    if side_query:
        merged.update(side_query)
    return merged


def build_url(
    base_url: str,
    path: str,
    query: dict[str, str],
    override: SideOverride | None,
) -> str:
    if override and override.url:
        url = override.url
    else:
        effective_path = override.path if override and override.path else path
        url = urljoin(f"{base_url}/", effective_path.lstrip("/"))

    if not query:
        return url

    separator = "&" if "?" in url else "?"
    return f"{url}{separator}{urlencode(query)}"


def resolve_side_request(
    side: str,
    project: ProjectConfig,
    request: RequestConfig,
) -> tuple[str, HttpMethod, dict[str, str], dict[str, str], Any | None]:
    base_url = project.base.left if side == "left" else project.base.right
    override = request.left if side == "left" else request.right

    if request.method is None:
        raise ConfigError(
            f"Request '{request.id}' uses HTTP on side '{side}' but has no 'method'"
        )
    has_path = request.path is not None or (override and (override.path or override.url))
    if not has_path:
        raise ConfigError(
            f"Request '{request.id}' uses HTTP on side '{side}' but has no 'path'"
        )

    query = _merge_query(request.query, override.query if override else None)
    headers = _merge_headers(
        project.defaults.headers,
        request.headers,
        override.headers if override else None,
    )
    body = override.body if override and override.body is not None else request.body
    url = build_url(base_url, request.path, query, override)

    return url, request.method, headers, query, body
