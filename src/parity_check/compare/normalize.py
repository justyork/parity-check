from typing import Any
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

_HTTP_SCHEMES = frozenset({"http", "https"})


def normalize_url_query(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme not in _HTTP_SCHEMES or not parsed.netloc:
        return url
    if not parsed.query:
        return url

    query_pairs = parse_qsl(parsed.query, keep_blank_values=True)
    if not query_pairs:
        return url

    sorted_pairs = sorted(query_pairs, key=lambda pair: (pair[0], pair[1]))
    canonical_query = urlencode(sorted_pairs, doseq=True)
    return urlunparse(
        (
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            parsed.params,
            canonical_query,
            parsed.fragment,
        )
    )


def normalize_json(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: normalize_json(item) for key, item in sorted(value.items())}
    if isinstance(value, list):
        return [normalize_json(item) for item in value]
    if isinstance(value, str):
        return normalize_url_query(value)
    return value
