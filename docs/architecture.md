# Architecture

> **Audience:** contributors and maintainers. If you only want to *use* parity-check, see [Concepts](concepts.md) and [Getting started](getting-started.md).

## Overview

`parity-check` is a CLI tool for regression comparison of responses from two APIs (for example, a legacy service and a new implementation). Each side speaks HTTP or gRPC, so a single request can compare HTTP against HTTP, gRPC against gRPC, or HTTP against gRPC (the typical migration case).

For Cursor agents authoring request YAML aligned with `config/` and `requests/`, see [`.cursor/skills/parity-check-author-requests/SKILL.md`](../.cursor/skills/parity-check-author-requests/SKILL.md).

## Flow

```
CLI (Typer, cli.py)
  → config/loader (YAML + env/*.yaml + .env + ${VAR} → Pydantic)
  → transport/run_pair (resolve protocol per side: http | grpc)
      → http/client + http/runner (httpx)
      → grpc/client + grpc/proto_loader + grpc/runner (grpcio)
  → both sides → transport/SideResponse (status normalized to HTTP, body as JSON)
  → compare/diff (ignore_paths → normalize_json → DeepDiff → unified diff)
  → report/console (rich)
  → report/artifacts (optional, with `-o/--output-dir`)
```

## Modules

| Module | Responsibility |
|--------|----------------|
| `config/loader.py` | Discover projects, merge `env/<name>.yaml`, load requests |
| `config/variables.py` | `.env`, `vars` from env yaml, `${VAR}` substitution, `PARITY_ENV` |
| `config/env_merge.py` | Deep-merge `base` from env over `project.yaml` |
| `config/models.py` | Pydantic configuration models (HTTP + gRPC, per-side protocol) |
| `transport/response.py` | `SideResponse` / `SideRequest` — protocol-neutral request/response |
| `transport/run_pair.py` | Resolve protocol per side, dispatch to http/grpc, build the pair |
| `http/client.py` | Build URL, merge headers/query/body, side overrides |
| `http/runner.py` | Execute HTTP requests via httpx |
| `grpc/client.py` | Resolve target, service/method, message, metadata per side |
| `grpc/proto_loader.py` | Compile `proto/` into a descriptor pool (cached by mtime) |
| `grpc/runner.py` | Execute a unary RPC, JSON in/out |
| `grpc/status.py` | Map `grpc.StatusCode` to an HTTP status for comparison |
| `compare/jsonpath_ignore.py` | Remove fields by JSONPath before comparison |
| `compare/normalize.py` | Recursively sort JSON object keys |
| `compare/diff.py` | Compare status/body, DeepDiff, unified diff for output |
| `report/console.py` | Print OK/FAIL, diff, and summary |
| `report/artifacts.py` | Persist run output (`summary.json`, per-request JSON) |
| `report/labels.py` | Endpoint labels for console output |
| `errors.py` | `ConfigError`, `RequestError` |
| `cli.py` | `list` and `run` commands, exit codes |

## Comparison rules

1. Status and response body are compared. Response headers / gRPC metadata are not compared.
2. For gRPC, the status code is normalized to an HTTP code (`grpc/status.py`) and the response message is rendered to JSON before comparison.
3. Body is parsed as JSON; on parse failure, text comparison is used. Empty body (including an empty gRPC message) is handled separately and an empty body on both sides is equal.
4. If body formats differ (JSON vs text), a direct text comparison is performed.
5. `ignore_paths` removes fields by JSONPath before comparison; invalid expressions raise `ConfigError`.
6. For JSON, object keys are sorted recursively (`normalize_json`); array element order is preserved (`DeepDiff` with `ignore_order=False`).
7. On body mismatch, a unified diff of normalized JSON is printed.

## Exit codes

| Code | Meaning |
|------|---------|
| 0 | All requests matched |
| 1 | At least one mismatch |
| 2 | Configuration error, HTTP error, or project not found (`list --project`) |

## Extension points (not in v1)

- Parallel request execution
- Response header / gRPC metadata comparison
- Streaming gRPC (only unary RPC is supported)
- gRPC TLS / mTLS (channels are insecure)
- gRPC server reflection (proto files are required)
- Automatic HTTP-JSON to protobuf field mapping
- OpenAPI / proto import
- OAuth / dynamic auth
