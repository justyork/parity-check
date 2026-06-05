from pathlib import Path

from parity_check.config.models import ProjectConfig, Protocol, RequestConfig
from parity_check.http.client import resolve_side_request
from parity_check.http.runner import HttpRunner
from parity_check.transport.response import RequestPairResult, SideRequest, SideResponse


def resolve_side_protocol(
    side: str,
    project: ProjectConfig,
    request: RequestConfig,
) -> Protocol:
    override = request.left if side == "left" else request.right
    if override and override.protocol is not None:
        return override.protocol
    if project.defaults.sides is not None:
        side_default = (
            project.defaults.sides.left if side == "left" else project.defaults.sides.right
        )
        if side_default is not None:
            return side_default
    return Protocol.HTTP


def _grpc_proto_dir(project: ProjectConfig, project_dir: Path | None) -> Path:
    if project_dir is None:
        raise ValueError("project_dir is required for gRPC requests")
    proto_dir = project.grpc.proto_dir if project.grpc else "proto"
    return project_dir / proto_dir


def _run_grpc_side(
    side: str,
    project: ProjectConfig,
    request: RequestConfig,
    project_dir: Path | None,
) -> tuple[SideRequest, SideResponse]:
    from parity_check.grpc.client import resolve_grpc_request, to_side_request
    from parity_check.grpc.proto_loader import get_descriptor_pool
    from parity_check.grpc.runner import GrpcRunner

    resolved = resolve_grpc_request(side, project, request)
    pool = get_descriptor_pool(_grpc_proto_dir(project, project_dir))
    preserving = project.grpc.json_preserving_proto_field_name if project.grpc else True
    runner = GrpcRunner(pool, project.defaults.timeout_sec, preserving)
    response = runner.execute(resolved)
    return to_side_request(resolved), response


def _run_http_side(
    side: str,
    project: ProjectConfig,
    request: RequestConfig,
) -> tuple[SideRequest, SideResponse]:
    url, method, headers, _, body = resolve_side_request(side, project, request)
    runner = HttpRunner(timeout_sec=project.defaults.timeout_sec)
    response = runner.execute(url, method, headers, body)
    side_request = SideRequest(
        protocol="http",
        endpoint=url,
        operation=method.value,
        headers=headers,
        body=body,
    )
    return side_request, response


def run_request_side(
    project: ProjectConfig,
    request: RequestConfig,
    side: str,
    project_dir: Path | None = None,
) -> tuple[SideRequest, SideResponse]:
    if side not in ("left", "right"):
        raise ValueError(f"side must be 'left' or 'right', got: {side}")

    if resolve_side_protocol(side, project, request) == Protocol.GRPC:
        return _run_grpc_side(side, project, request, project_dir)
    return _run_http_side(side, project, request)


def run_request_pair(
    project: ProjectConfig,
    request: RequestConfig,
    project_dir: Path | None = None,
) -> RequestPairResult:
    left_request, left = run_request_side(project, request, "left", project_dir)
    right_request, right = run_request_side(project, request, "right", project_dir)
    return RequestPairResult(
        left=left,
        right=right,
        left_request=left_request,
        right_request=right_request,
    )
