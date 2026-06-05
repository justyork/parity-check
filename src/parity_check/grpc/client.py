from dataclasses import dataclass, field
from typing import Any

from parity_check.config.models import GrpcRequest, ProjectConfig, RequestConfig
from parity_check.errors import ConfigError
from parity_check.transport.response import SideRequest


@dataclass(frozen=True)
class ResolvedGrpcRequest:
    target: str
    service: str
    method: str
    message: Any | None
    metadata: dict[str, str] = field(default_factory=dict)

    @property
    def full_method(self) -> str:
        return f"/{self.service}/{self.method}"


def _normalize_target(base: str) -> str:
    for scheme in ("grpc://", "grpcs://"):
        if base.startswith(scheme):
            return base[len(scheme) :]
    return base


def _merge_grpc(base: GrpcRequest | None, override: GrpcRequest | None) -> GrpcRequest:
    service = None
    method = None
    message: Any | None = None
    metadata: dict[str, str] = {}

    if base is not None:
        service = base.service
        method = base.method
        message = base.message
        metadata.update(base.metadata)
    if override is not None:
        if override.service is not None:
            service = override.service
        if override.method is not None:
            method = override.method
        if override.message is not None:
            message = override.message
        metadata.update(override.metadata)

    return GrpcRequest(service=service, method=method, message=message, metadata=metadata)


def resolve_grpc_request(
    side: str,
    project: ProjectConfig,
    request: RequestConfig,
) -> ResolvedGrpcRequest:
    if side not in ("left", "right"):
        raise ValueError(f"side must be 'left' or 'right', got: {side}")

    override = request.left if side == "left" else request.right
    side_grpc = override.grpc if override else None
    merged = _merge_grpc(request.grpc, side_grpc)

    if not merged.service or not merged.method:
        raise ConfigError(
            f"Request '{request.id}' uses gRPC on side '{side}' but is missing "
            "'grpc.service' or 'grpc.method'"
        )

    base = project.base.left if side == "left" else project.base.right
    target = _normalize_target(base)

    return ResolvedGrpcRequest(
        target=target,
        service=merged.service,
        method=merged.method,
        message=merged.message,
        metadata=merged.metadata,
    )


def to_side_request(resolved: ResolvedGrpcRequest) -> SideRequest:
    return SideRequest(
        protocol="grpc",
        endpoint=f"{resolved.target}{resolved.full_method}",
        operation=f"{resolved.service}/{resolved.method}",
        headers=resolved.metadata,
        body=resolved.message,
    )
