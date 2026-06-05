from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, field_validator

from parity_check.config.tags import normalize_tags


class HttpMethod(StrEnum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"
    HEAD = "HEAD"


class Protocol(StrEnum):
    HTTP = "http"
    GRPC = "grpc"


class BaseUrls(BaseModel):
    left: str
    right: str

    @field_validator("left", "right")
    @classmethod
    def strip_trailing_slash(cls, value: str) -> str:
        return value.rstrip("/")


class SidesConfig(BaseModel):
    left: Protocol | None = None
    right: Protocol | None = None


class GrpcRequest(BaseModel):
    service: str | None = None
    method: str | None = None
    message: Any | None = None
    metadata: dict[str, str] = Field(default_factory=dict)


class GrpcProjectConfig(BaseModel):
    proto_dir: str = "proto"
    json_preserving_proto_field_name: bool = True


class DefaultsConfig(BaseModel):
    timeout_sec: float = 30.0
    headers: dict[str, str] = Field(default_factory=dict)
    sides: SidesConfig | None = None


class SideOverride(BaseModel):
    url: str | None = None
    path: str | None = None
    headers: dict[str, str] | None = None
    body: Any | None = None
    query: dict[str, str] | None = None
    protocol: Protocol | None = None
    grpc: GrpcRequest | None = None


class ProjectConfig(BaseModel):
    name: str
    base: BaseUrls
    defaults: DefaultsConfig = Field(default_factory=DefaultsConfig)
    grpc: GrpcProjectConfig | None = None

    def with_base_overrides(self, left: str | None, right: str | None) -> "ProjectConfig":
        data = self.model_dump()
        if left is not None:
            data["base"]["left"] = left.rstrip("/")
        if right is not None:
            data["base"]["right"] = right.rstrip("/")
        return ProjectConfig.model_validate(data)


class RequestConfig(BaseModel):
    id: str
    method: HttpMethod | None = None
    path: str | None = None
    body: Any | None = None
    query: dict[str, str] = Field(default_factory=dict)
    headers: dict[str, str] = Field(default_factory=dict)
    grpc: GrpcRequest | None = None
    left: SideOverride | None = None
    right: SideOverride | None = None
    ignore_paths: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    skip: bool = False
    skip_reason: str | None = None

    @field_validator("tags", mode="before")
    @classmethod
    def parse_tags(cls, value: object) -> list[str]:
        return normalize_tags(value)

    @field_validator("path")
    @classmethod
    def path_must_start_with_slash(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if not value.startswith("/"):
            return f"/{value}"
        return value


class LoadedProject(BaseModel):
    config: ProjectConfig
    requests: list[RequestConfig]
