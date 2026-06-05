from pathlib import Path

import pytest
from grpc_server import run_greeter_server

from parity_check.compare.diff import compare_responses
from parity_check.config.models import (
    BaseUrls,
    DefaultsConfig,
    GrpcProjectConfig,
    GrpcRequest,
    HttpMethod,
    ProjectConfig,
    Protocol,
    RequestConfig,
    SidesConfig,
)
from parity_check.grpc.proto_loader import get_descriptor_pool
from parity_check.transport.run_pair import resolve_side_protocol, run_request_pair

FIXTURES_DIR = Path(__file__).parent / "fixtures"
PROTO_DIR = FIXTURES_DIR / "proto"


def _reply(pool, request):
    from parity_check.grpc.runner import _message_class

    reply_cls = _message_class(pool, "parity.example.v1.HelloReply")
    reply = reply_cls()
    reply.message = "hello world"
    reply.code = 7
    return reply


def test_resolve_side_protocol_defaults_and_override():
    project = ProjectConfig(
        name="p",
        base=BaseUrls(left="http://l", right="http://r"),
        defaults=DefaultsConfig(sides=SidesConfig(left=Protocol.HTTP, right=Protocol.GRPC)),
    )
    request = RequestConfig(id="r")

    assert resolve_side_protocol("left", project, request) == Protocol.HTTP
    assert resolve_side_protocol("right", project, request) == Protocol.GRPC


def test_resolve_side_protocol_defaults_http_when_unset():
    project = ProjectConfig(name="p", base=BaseUrls(left="http://l", right="http://r"))
    request = RequestConfig(id="r", method=HttpMethod.GET, path="/x")
    assert resolve_side_protocol("left", project, request) == Protocol.HTTP


@pytest.mark.httpx_mock(assert_all_responses_were_requested=False)
def test_mixed_http_left_grpc_right_equal(httpx_mock):
    httpx_mock.add_response(
        url="http://legacy.local/hello?name=world",
        json={"message": "hello world", "code": 7},
    )
    pool = get_descriptor_pool(PROTO_DIR)

    with run_greeter_server(pool, lambda req, ctx: _reply(pool, req)) as (target, _cls):
        project = ProjectConfig(
            name="example-grpc",
            base=BaseUrls(left="http://legacy.local", right=target),
            defaults=DefaultsConfig(
                timeout_sec=5,
                sides=SidesConfig(left=Protocol.HTTP, right=Protocol.GRPC),
            ),
            grpc=GrpcProjectConfig(proto_dir="proto"),
        )
        request = RequestConfig(
            id="say-hello",
            method=HttpMethod.GET,
            path="/hello",
            query={"name": "world"},
            grpc=GrpcRequest(
                service="parity.example.v1.Greeter",
                method="SayHello",
                message={"name": "world"},
            ),
        )

        pair = run_request_pair(project, request, project_dir=FIXTURES_DIR)

    assert pair.left.protocol == "http"
    assert pair.right.protocol == "grpc"
    result = compare_responses(pair.left, pair.right)
    assert result.equal
    assert result.body_equal
    assert result.status_equal
