from dataclasses import dataclass, field
from typing import Any, Literal

Protocol = Literal["http", "grpc"]


@dataclass(frozen=True)
class SideResponse:
    status_code: int
    body_text: str
    headers: dict[str, str] = field(default_factory=dict)
    protocol: Protocol = "http"
    endpoint: str = ""
    raw_status: str = ""

    @property
    def display_status(self) -> str:
        return self.raw_status or str(self.status_code)


@dataclass(frozen=True)
class SideRequest:
    protocol: Protocol
    endpoint: str
    operation: str
    headers: dict[str, str] = field(default_factory=dict)
    body: Any | None = None


@dataclass(frozen=True)
class RequestPairResult:
    left: SideResponse
    right: SideResponse
    left_request: SideRequest | None = None
    right_request: SideRequest | None = None
