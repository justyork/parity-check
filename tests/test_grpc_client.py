import pytest

from parity_check.config.models import (
    BaseUrls,
    GrpcRequest,
    ProjectConfig,
    RequestConfig,
    SideOverride,
)
from parity_check.errors import ConfigError
from parity_check.grpc.client import resolve_grpc_request, to_side_request


def _project() -> ProjectConfig:
    return ProjectConfig(
        name="test",
        base=BaseUrls(left="http://legacy.local", right="grpc://new.local:50051"),
    )


def test_resolve_grpc_merges_request_and_side_override():
    project = _project()
    request = RequestConfig(
        id="get-user",
        grpc=GrpcRequest(service="api.v1.UserService", method="GetUser", message={"id": "1"}),
        right=SideOverride(grpc=GrpcRequest(message={"id": "2"}, metadata={"x-tenant": "t1"})),
    )

    resolved = resolve_grpc_request("right", project, request)

    assert resolved.target == "new.local:50051"
    assert resolved.service == "api.v1.UserService"
    assert resolved.method == "GetUser"
    assert resolved.message == {"id": "2"}
    assert resolved.metadata == {"x-tenant": "t1"}
    assert resolved.full_method == "/api.v1.UserService/GetUser"


def test_resolve_grpc_missing_service_raises():
    project = _project()
    request = RequestConfig(id="bad", right=SideOverride(grpc=GrpcRequest(method="GetUser")))

    with pytest.raises(ConfigError):
        resolve_grpc_request("right", project, request)


def test_to_side_request_shape():
    project = _project()
    request = RequestConfig(
        id="get-user",
        grpc=GrpcRequest(service="api.v1.UserService", method="GetUser"),
    )
    side_request = to_side_request(resolve_grpc_request("right", project, request))

    assert side_request.protocol == "grpc"
    assert side_request.operation == "api.v1.UserService/GetUser"
    assert side_request.endpoint == "new.local:50051/api.v1.UserService/GetUser"
