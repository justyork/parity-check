from parity_check.config.models import (
    BaseUrls,
    DefaultsConfig,
    HttpMethod,
    ProjectConfig,
    RequestConfig,
    SideOverride,
)
from parity_check.http.client import build_url, resolve_side_request


def _project() -> ProjectConfig:
    return ProjectConfig(
        name="test",
        base=BaseUrls(left="http://left.local", right="http://right.local"),
        defaults=DefaultsConfig(headers={"Authorization": "Bearer token"}),
    )


def test_build_url_with_query():
    url = build_url("http://api.local", "/users", {"page": "1"}, None)
    assert url == "http://api.local/users?page=1"


def test_resolve_side_request_merges_headers_and_overrides():
    project = _project()
    request = RequestConfig(
        id="create",
        method=HttpMethod.POST,
        path="/items",
        headers={"X-Custom": "1"},
        body={"name": "item"},
        right=SideOverride(path="/v2/items", body={"name": "v2-item"}),
    )

    left_url, method, left_headers, _, left_body = resolve_side_request("left", project, request)
    right_url, _, right_headers, _, right_body = resolve_side_request("right", project, request)

    assert left_url == "http://left.local/items"
    assert right_url == "http://right.local/v2/items"
    assert method == HttpMethod.POST
    assert left_headers["Authorization"] == "Bearer token"
    assert left_headers["X-Custom"] == "1"
    assert left_body == {"name": "item"}
    assert right_body == {"name": "v2-item"}
