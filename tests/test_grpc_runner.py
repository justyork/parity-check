import json
from pathlib import Path

import grpc
from grpc_server import run_greeter_server

from parity_check.grpc.client import ResolvedGrpcRequest
from parity_check.grpc.proto_loader import get_descriptor_pool
from parity_check.grpc.runner import GrpcRunner

PROTO_DIR = Path(__file__).parent / "fixtures" / "proto"


def _resolved(target: str, message: dict | None) -> ResolvedGrpcRequest:
    return ResolvedGrpcRequest(
        target=target,
        service="parity.example.v1.Greeter",
        method="SayHello",
        message=message,
    )


def test_grpc_runner_success():
    pool = get_descriptor_pool(PROTO_DIR)

    with run_greeter_server(pool, lambda req, ctx: _reply(pool, req)) as (target, _reply_cls):
        runner = GrpcRunner(pool, timeout_sec=5)
        response = runner.execute(_resolved(target, {"name": "world"}))

    assert response.status_code == 200
    assert response.protocol == "grpc"
    assert response.raw_status == "OK"
    body = json.loads(response.body_text)
    assert body["message"] == "hello world"
    assert body["code"] == 7


def test_grpc_runner_maps_not_found():
    pool = get_descriptor_pool(PROTO_DIR)

    def deny(request, context):
        context.abort(grpc.StatusCode.NOT_FOUND, "missing")

    with run_greeter_server(pool, deny) as (target, _reply_cls):
        runner = GrpcRunner(pool, timeout_sec=5)
        response = runner.execute(_resolved(target, {"name": "x"}))

    assert response.status_code == 404
    assert response.raw_status == "NOT_FOUND"
    assert response.body_text == ""


def _reply(pool, request):
    from parity_check.grpc.runner import _message_class

    reply_cls = _message_class(pool, "parity.example.v1.HelloReply")
    reply = reply_cls()
    reply.message = f"hello {request.name}"
    reply.code = 7
    return reply
