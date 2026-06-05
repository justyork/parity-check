# ADR-0001: gRPC and mixed HTTP/gRPC parity

- Status: Accepted
- Date: 2026-06-04

## Context

`parity-check` originally compared only HTTP responses between two services: a single `RequestConfig` held shared `method` / `path`, both sides were executed by `http/runner.py`, and `compare/diff.py` compared HTTP status and body. See [docs/architecture.md](../architecture.md).

The driving need is API migration, where the legacy service answers over HTTP and the new service answers over gRPC. The tool had to compare a request across two different transports while keeping every existing HTTP-only project working unchanged. Constraints: backward compatibility for current `project.yaml` / `requests/*.yaml`, a stable comparison model (status + JSON body), and no reliance on network features that are unavailable in CI (such as server reflection).

## Decision

Introduce a transport-neutral layer and a gRPC stack, with protocol selected per side.

- Add `transport/response.py` with `SideResponse` (and `SideRequest`) as the protocol-neutral result. `http/runner.py` keeps `HttpResponse` as an alias of `SideResponse`, so existing code and tests are unaffected.
- Add `transport/run_pair.py`. `resolve_side_protocol` chooses the protocol for each side in this order: request `left.protocol` / `right.protocol`, then `defaults.sides.left` / `defaults.sides.right`, then `http`. The orchestrator dispatches each side to the HTTP or gRPC runner and returns one `RequestPairResult`.
- Add the `grpc/` package: `proto_loader.py` compiles `projects/<name>/proto/` into a cached descriptor pool, `client.py` resolves target / service / method / message / metadata, `runner.py` performs a unary RPC with JSON in/out, and `status.py` maps `grpc.StatusCode` to an HTTP status for the status check.
- Extend `config/models.py`: `Protocol`, `GrpcRequest`, `SidesConfig`, `GrpcProjectConfig`; `method` and `path` become optional and are required only for an HTTP side (validated in `http/client.py`); gRPC requires `service` and `method` (validated in `grpc/client.py`).
- Comparison stays status + JSON body. A gRPC response is rendered with `MessageToJson`; an empty gRPC message and an empty HTTP body are treated as equal; `UNAVAILABLE` and `DEADLINE_EXCEEDED` are transport errors, not differences.

Invariants after this decision: comparison is always expressed through `SideResponse` with an HTTP-normalized status; gRPC sides require proto files in the project; only unary RPCs are supported; channels are insecure; there is no automatic HTTP-JSON to protobuf field mapping (payloads are aligned in YAML and via `ignore_paths`).

## Consequences

Positive: HTTP-only projects are unchanged; a single request can mix HTTP and gRPC; the transport split keeps `cli.py` and `compare/diff.py` protocol-agnostic and leaves room for more transports.

Negative / limits: gRPC needs committed proto files and the `grpcio`, `grpcio-tools`, and `protobuf` runtime; streaming, TLS/mTLS, metadata comparison, and server reflection are out of scope; status equivalence depends on a fixed gRPC-to-HTTP mapping table in `grpc/status.py`.

Operational: new runtime dependencies `grpcio`, `grpcio-tools` (proto files are compiled at run time by `grpc/proto_loader.py`), and `protobuf` are added in [pyproject.toml](../../pyproject.toml). Exit codes are unchanged. gRPC artifacts in `-o/--output-dir` carry `protocol` and `raw_status` in each snapshot.

## Alternatives Considered

- gRPC server reflection instead of committed proto files: rejected for v1 because reflection is often disabled on services and is unreliable in CI; proto-in-repo is reproducible and reviewable.
- One protocol per whole request instead of per side: rejected because the primary case is HTTP on one side and gRPC on the other within the same request.
- Comparing only via an HTTP gateway (grpc-gateway / Envoy transcoding) and not adding gRPC at all: rejected because a gateway is not always present and native gRPC parity is the requirement; this remains a valid no-code alternative when a gateway exists.
- Automatic HTTP-JSON to protobuf field mapping: rejected for v1 due to ambiguity (field naming, `json_name`); authors align payloads explicitly and use `ignore_paths`.

## References

- [docs/architecture.md](../architecture.md)
- [docs/request-schema.md](../request-schema.md)
- [src/parity_check/transport/run_pair.py](../../src/parity_check/transport/run_pair.py)
- [src/parity_check/grpc/runner.py](../../src/parity_check/grpc/runner.py)
- [src/parity_check/grpc/status.py](../../src/parity_check/grpc/status.py)
- [src/parity_check/config/models.py](../../src/parity_check/config/models.py)
- [projects/example-grpc/project.yaml](../../projects/example-grpc/project.yaml)
- [pyproject.toml](../../pyproject.toml)
