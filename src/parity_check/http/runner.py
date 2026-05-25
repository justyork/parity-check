from dataclasses import dataclass
from typing import Any

import httpx

from parity_check.config.models import HttpMethod, ProjectConfig, RequestConfig
from parity_check.errors import RequestError
from parity_check.http.client import resolve_side_request


@dataclass(frozen=True)
class HttpResponse:
    status_code: int
    body_text: str
    headers: dict[str, str]


@dataclass(frozen=True)
class RequestPairResult:
    left: HttpResponse
    right: HttpResponse


class HttpRunner:
    def __init__(self, timeout_sec: float) -> None:
        self._timeout_sec = timeout_sec

    def execute(
        self,
        url: str,
        method: HttpMethod,
        headers: dict[str, str],
        body: Any | None,
    ) -> HttpResponse:
        request_kwargs: dict[str, Any] = {
            "method": method.value,
            "url": url,
            "headers": headers,
            "timeout": self._timeout_sec,
        }
        if body is not None and method not in (HttpMethod.GET, HttpMethod.HEAD):
            if isinstance(body, (dict, list)):
                request_kwargs["json"] = body
            else:
                request_kwargs["content"] = str(body).encode("utf-8")

        try:
            with httpx.Client() as client:
                response = client.request(**request_kwargs)
        except httpx.HTTPError as exc:
            raise RequestError(f"Request failed for {url}: {exc}") from exc

        return HttpResponse(
            status_code=response.status_code,
            body_text=response.text,
            headers=dict(response.headers),
        )


def run_request_side(
    project: ProjectConfig,
    request: RequestConfig,
    side: str,
) -> tuple[str, HttpMethod, dict[str, str], Any | None, HttpResponse]:
    if side not in ("left", "right"):
        raise ValueError(f"side must be 'left' or 'right', got: {side}")

    runner = HttpRunner(timeout_sec=project.defaults.timeout_sec)
    url, method, headers, _, body = resolve_side_request(side, project, request)
    response = runner.execute(url, method, headers, body)
    return url, method, headers, body, response


def run_request_pair(
    project: ProjectConfig,
    request: RequestConfig,
) -> RequestPairResult:
    runner = HttpRunner(timeout_sec=project.defaults.timeout_sec)

    left_url, method, left_headers, _, left_body = resolve_side_request("left", project, request)
    right_url, _, right_headers, _, right_body = resolve_side_request("right", project, request)

    left = runner.execute(left_url, method, left_headers, left_body)
    right = runner.execute(right_url, method, right_headers, right_body)

    return RequestPairResult(left=left, right=right)
