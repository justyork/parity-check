import httpx
import pytest

from parity_check.config.models import (
    BaseUrls,
    DefaultsConfig,
    HttpMethod,
    ProjectConfig,
    RequestConfig,
)
from parity_check.http.runner import run_request_pair, run_request_side


@pytest.mark.httpx_mock(assert_all_responses_were_requested=False)
def test_run_request_pair(httpx_mock) -> None:
    httpx_mock.add_response(url="http://left.local/health", json={"status": "ok"})
    httpx_mock.add_response(url="http://right.local/health", json={"status": "ok"})

    project = ProjectConfig(
        name="test",
        base=BaseUrls(left="http://left.local", right="http://right.local"),
        defaults=DefaultsConfig(timeout_sec=5),
    )
    request = RequestConfig(id="health", method=HttpMethod.GET, path="/health")

    result = run_request_pair(project, request)
    assert result.left.status_code == 200
    assert result.right.status_code == 200


@pytest.mark.httpx_mock(assert_all_responses_were_requested=False)
def test_run_request_side_left_only(httpx_mock) -> None:
    httpx_mock.add_response(url="http://left.local/health", json={"side": "left"})

    project = ProjectConfig(
        name="test",
        base=BaseUrls(left="http://left.local", right="http://right.local"),
        defaults=DefaultsConfig(timeout_sec=5),
    )
    request = RequestConfig(id="health", method=HttpMethod.GET, path="/health")

    url, method, request_headers, request_body, response = run_request_side(
        project, request, "left"
    )
    assert url == "http://left.local/health"
    assert method == HttpMethod.GET
    assert request_body is None
    assert response.status_code == 200
    assert "left" in response.body_text


@pytest.mark.httpx_mock(assert_all_responses_were_requested=False)
def test_run_request_pair_sends_form_body_as_content(httpx_mock) -> None:
    def check_request(request: httpx.Request) -> httpx.Response:
        assert request.content == b"key=value"
        assert "application/x-www-form-urlencoded" in request.headers.get("content-type", "")
        return httpx.Response(200, json={"ok": True})

    httpx_mock.add_callback(check_request, url="http://left.local/install")
    httpx_mock.add_callback(check_request, url="http://right.local/install")

    project = ProjectConfig(
        name="test",
        base=BaseUrls(left="http://left.local", right="http://right.local"),
        defaults=DefaultsConfig(timeout_sec=5),
    )
    request = RequestConfig(
        id="install",
        method=HttpMethod.POST,
        path="/install",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        body="key=value",
    )

    result = run_request_pair(project, request)
    assert result.left.status_code == 200
    assert result.right.status_code == 200
