# parity-check request schema

This document describes the YAML format under `projects/`. Use it as the single source of truth when generating request configuration to compare two APIs (**left** and **right**), including mixed HTTP and gRPC.

**New here?** Read [Concepts](concepts.md) first, then try the [Getting started](getting-started.md) demos. This file is the complete field reference.

## Purpose

Each **request** is one HTTP call executed against both services with shared (or separately overridden) parameters. A request definition does not include the expected response — only method, URL, headers, query, body, and fields to exclude from subsequent body comparison.

## Directory layout

```
projects/
  <project_name>/
    project.yaml
    .env                    # optional secrets and overrides
    env/
      <environment>.yaml    # base URL + vars for an environment (dev, local, …)
      <environment>.env     # optional dotenv for an environment
    requests/
      <request-id>.yaml
```

| Rule | Requirement |
|------|-------------|
| Directory name | Matches `name` in `project.yaml` |
| `request-id` | kebab-case: `get-user`, `create-order` |
| File name | `<request-id>.yaml` |
| `id` field | Matches `<request-id>` (if omitted, taken from the file name) |

## Output format

Generate **valid YAML only**. Start each file block with a path comment:

```yaml
# file: projects/<project_name>/project.yaml
```

```yaml
# file: projects/<project_name>/requests/<request-id>.yaml
```

No explanatory text between file blocks.

---

## Environments and variables

### `env/<environment>.yaml`

Overrides `base` from `project.yaml` and defines variables for substitution in requests.

```yaml
base:
  left: https://api-old.example.com
  right: https://api-new.example.com
vars:
  TENANT_ID: my-tenant
  USER_ID: "00000000-b492-4dd3-bd0f-1852bbb6b003"
  PACKAGE_NAME: com.example.app
```

| Field | Description |
|-------|-------------|
| `base` | Same as in `project.yaml`, overrides base URLs |
| `vars` | Map of `KEY: value` for substitution in requests |

### `.env`

Dotenv format (`KEY=value`, quotes optional). Load order (later wins):

1. `<repo>/.env`
2. `projects/<project_name>/.env`
3. `vars` from `env/<environment>.yaml` (with `--env`)
4. `projects/<project_name>/env/<environment>.env` (with `--env`)

Secrets and local values belong in `.env` (gitignored); team-shared values belong in `env/<environment>.yaml`.

**Selecting an environment on `run`:** pass `--env <name>` or set `PARITY_ENV`. If both are omitted, the CLI uses `dev` when `env/dev.yaml` exists, otherwise the only `env/*.yaml` when there is exactly one file.

### Substitution in requests

Syntax: `${VAR_NAME}` (`VAR_NAME` matches `[A-Za-z_][A-Za-z0-9_]*`).

Substituted in: `path`, `url`, `headers`, `query`, `body` (including form-urlencoded strings), nested `body` objects.

```yaml
path: /users/${USER_ID}/session
headers:
  X-Tenant-ID: ${TENANT_ID}
body: >-
  user_id=${USER_ID}&package_name=${PACKAGE_NAME}
right:
  headers:
    X-Tenant-ID: ${TENANT_ID}
```

A missing variable is a configuration error.

### Random values (per request)

Built-in expressions generate values per request definition (shared across all fields and both **left** / **right** sides).

| Expression | Example value |
|------------|----------------|
| `${random.uuid}` | `550e8400-e29b-41d4-a716-446655440000` |
| `${random.uuid4}` | same as `random.uuid` |
| `${random.hex16}` | 16 hex chars |
| `${random.hex32}` | 32 hex chars |

**One value** — repeat the same expression (all `${random.uuid}` in a file share one value):

```yaml
path: /users/${random.uuid}/session
headers:
  X-Request-Id: ${random.uuid}
body:
  user_id: ${random.uuid}
```

**Two different values** — add a numeric suffix (each suffix is its own slot):

```yaml
path: /users/${random.uuid}/friends/${random.uuid.2}
body:
  owner_id: ${random.uuid}
  friend_id: ${random.uuid.2}
```

`${random.uuid}` and `${random.uuid.2}` are independent; `${random.uuid.2}` and `${random.uuid.3}` are independent as well. A new set of values is generated for each request file in a run.

---

## `project.yaml`

Shared project settings: base URLs and defaults for all requests.

```yaml
name: <project_name>
base:
  left: http://...
  right: http://...
defaults:
  timeout_sec: 30
  headers:
    Accept: application/json
    Content-Type: application/json
```

### Fields

| Field | Required | Type | Description |
|-------|----------|------|-------------|
| `name` | yes | string | Project name, equals `projects/<project_name>/` directory name |
| `base.left` | yes | string | Left service base URL, no trailing `/` |
| `base.right` | yes | string | Right service base URL, no trailing `/` |
| `defaults.timeout_sec` | no | number | Request timeout in seconds (default 30); also gRPC deadline |
| `defaults.headers` | no | map[string]string | Headers shared by all HTTP requests |
| `defaults.sides.left` | no | enum | Default protocol for the left side: `http` (default) or `grpc` |
| `defaults.sides.right` | no | enum | Default protocol for the right side: `http` (default) or `grpc` |
| `grpc.proto_dir` | no | string | Directory with `.proto` files, relative to the project (default `proto`) |
| `grpc.json_preserving_proto_field_name` | no | bool | Keep snake_case proto field names in JSON (default `true`) |

`base.left` / `base.right` are environment placeholders (localhost, staging). They do not need to be final production URLs in committed yaml. For a gRPC side, the base is a target (`host:port`, optionally `grpc://host:port`) instead of a URL.

---

## `requests/<request-id>.yaml`

One HTTP request.

```yaml
id: <request-id>
method: GET
path: /api/v1/resource
body: null
query:
  page: "1"
headers:
  X-Request-Id: example
left:
  path: /api/v1/resource
right:
  path: /api/v2/resource
ignore_paths:
  - $.timestamp
```

### Request fields

| Field | Required | Type | Description |
|-------|----------|------|-------------|
| `id` | yes* | string | Request identifier (*if omitted, from file name) |
| `method` | HTTP only | enum | `GET`, `POST`, `PUT`, `PATCH`, `DELETE`, `HEAD` (required for an HTTP side) |
| `path` | HTTP only | string | Path relative to `base`; must start with `/` (required for an HTTP side) |
| `body` | no | any | Request body; for JSON — YAML object or array |
| `query` | no | map[string]string | Query parameters; **all values are strings** |
| `headers` | no | map[string]string | Request headers (merged over `defaults.headers`) |
| `grpc` | gRPC only | GrpcRequest | Shared gRPC call definition (see below) |
| `left` | no | SideOverride | Overrides for left only |
| `right` | no | SideOverride | Overrides for right only |
| `ignore_paths` | no | list[string] | JSONPath fields excluded from response body comparison |
| `tags` | no | string or list[string] | Labels for selective runs (`--tag` / `-t` on CLI) |
| `skip` | no | bool | `true` — skip on full project run (default: `false`) |
| `skip_reason` | no | string | Skip reason shown in console output |

With explicit `--request <id>`, the request runs even when `skip: true`.

### `tags`

Optional string or list of strings. Tag names must match `[A-Za-z0-9][A-Za-z0-9._-]*` (letters, digits, `.`, `-`, `_`).

```yaml
tags: smoke
```

```yaml
tags:
  - smoke
  - android
```

On `parity-check run`, `--tag` / `-t` may be repeated. A request runs if it has **any** of the tags passed on the CLI (OR). Requests without `tags` are not included when filtering. Combine with `--request` only when that request carries a matching tag.

```bash
parity-check run --project example --tag smoke
parity-check run --project example -t smoke -t android
```

### `body`

| method | `body` |
|--------|--------|
| `GET`, `HEAD`, `DELETE` | `null` or omitted |
| `POST`, `PUT`, `PATCH` | YAML object or array → serialized as JSON |

### Building the final request

**URL (without `url` override):**

```
<base.left or base.right> + <path>
```

If `left.path` / `right.path` is set, it replaces the shared `path` for that side.

**Full URL:** `left.url` / `right.url` replaces the entire `base + path` assembly.

**Headers (merge order, later wins):**

```
defaults.headers → request.headers → left.headers / right.headers
```

**Query:**

```
request.query → left.query / right.query
```

**Body:**

Shared `body`; if a side defines `left.body` / `right.body`, that value is used.

---

## `SideOverride` (`left` / `right`)

| Field | Type | Description |
|-------|------|-------------|
| `url` | string | Full request URL (HTTP) |
| `path` | string | Path instead of shared `path` (HTTP) |
| `headers` | map[string]string | Additional side headers (HTTP) |
| `body` | any | Body instead of shared `body` (HTTP) |
| `query` | map[string]string | Additional side query parameters (HTTP) |
| `protocol` | enum | `http` or `grpc` for this side; overrides `defaults.sides` |
| `grpc` | GrpcRequest | gRPC call definition or overrides for this side |

Use overrides only when left and right actually differ. Shared values belong in top-level `path`, `body`, `query`, `headers`.

| Situation | Fields |
|-----------|--------|
| Different API paths | `left.path`, `right.path` |
| Different bodies | `left.body`, `right.body` |
| Different query | `left.query`, `right.query` |
| URL cannot be built from base + path | `left.url` or `right.url` |

---

## gRPC and mixed HTTP↔gRPC

A request compares two sides. Each side has a protocol — `http` or `grpc` — resolved in this order:

1. `left.protocol` / `right.protocol` in the request;
2. `defaults.sides.left` / `defaults.sides.right` in `project.yaml`;
3. `http` if nothing is set (so existing HTTP-only projects are unchanged).

The main scenario is an API migration: the legacy service answers over HTTP (`left`) and the new service over gRPC (`right`). Both sides may also be gRPC for a symmetric comparison.

### Proto contract

gRPC requires the message contract. Put `.proto` files under `projects/<name>/proto/` (or set `grpc.proto_dir`). They are compiled when the run starts and used to build request messages and decode responses. Server reflection is not used.

### `GrpcRequest`

| Field | Required | Type | Description |
|-------|----------|------|-------------|
| `service` | yes | string | Fully-qualified service name, e.g. `myapi.v1.UserService` |
| `method` | yes | string | RPC method name, e.g. `GetUser` |
| `message` | no | any | Request message as a JSON object (mapped to protobuf); `${VAR}` substitution applies |
| `metadata` | no | map[string]string | gRPC metadata (the equivalent of HTTP headers) |

`grpc` may be set at the request level (shared by both sides) and refined per side under `left.grpc` / `right.grpc`. Per-side `service`, `method`, and `message` replace the shared values; `metadata` is merged.

### How sides are compared

- The gRPC status is normalized to an HTTP code for the status check (`OK` -> 200, `NOT_FOUND` -> 404, `INVALID_ARGUMENT` -> 400, and so on). A mismatch shows both raw values, e.g. `status: http 200 vs grpc NOT_FOUND`.
- The gRPC response is rendered to JSON (`MessageToJson`) and compared with the HTTP JSON body using the same rules and `ignore_paths`.
- An empty gRPC message (`{}`) and an empty HTTP body (for example `204`) are treated as equal.
- `UNAVAILABLE` and `DEADLINE_EXCEEDED` are connection-level failures (like an HTTP connection error) and are reported as errors, not differences.

There is no automatic HTTP-JSON to protobuf field mapping. Align the two payloads in YAML (`body` for HTTP, `grpc.message` for gRPC) and use `ignore_paths` to drop fields that legitimately differ (for example `id` vs `user_id`). Field name style is controlled by `grpc.json_preserving_proto_field_name`.

### Mixed example

```yaml
# file: projects/example-grpc/project.yaml
name: example-grpc
base:
  left: http://localhost:8080
  right: localhost:50051
defaults:
  timeout_sec: 30
  sides:
    left: http
    right: grpc
grpc:
  proto_dir: proto
```

```yaml
# file: projects/example-grpc/requests/say-hello.yaml
id: say-hello
method: GET
path: /hello
query:
  name: world
right:
  grpc:
    service: parity.example.v1.Greeter
    method: SayHello
    message:
      name: world
ignore_paths:
  - $.code
```

### Symmetric gRPC example

```yaml
# file: projects/grpc-only/requests/get-user.yaml
id: get-user
grpc:
  service: myapi.v1.UserService
  method: GetUser
  message:
    user_id: "42"
```

With `defaults.sides.left: grpc` and `defaults.sides.right: grpc`, both sides issue the same call against `base.left` and `base.right`.

---

## `ignore_paths`

List of [JSONPath](https://goessner.net/articles/JsonPath/) expressions (`jsonpath-ng` syntax). Listed fields **do not participate in response body comparison**.

Typical candidates:

- timestamps: `$.created_at`, `$.updated_at`, `$.generated_at`
- request/trace identifiers: `$.meta.request_id`, `$.trace_id`
- auto-generated ids on create: `$.id`
- nested collections: `$.items[*].updated_at`

Add `ignore_paths` when a field is known to differ between runs or services but does not affect the business logic under test.

For body comparison (outside this file): JSON object key order is insignificant; array element order is significant.

---

## Rules for generating request sets

| Rule | Description |
|------|-------------|
| One file — one scenario | Do not combine multiple endpoints in one yaml |
| Meaningful `id` | `get-health`, `list-orders-page-1`, `create-user-valid` |
| Coverage | Happy path, typical path/query params, important POST/PUT/PATCH |
| No duplicates | No two files with the same effective method + path + body + query |
| Stable data | Fixed ids in paths; no random uuids in requests |
| Source | Endpoints only from project context (OpenAPI, code, curl) — do not invent |
| Auth | Static headers only in `defaults.headers` or `headers` |

### Allowed methods

`GET`, `POST`, `PUT`, `PATCH`, `DELETE`, `HEAD` — no other values.

---

## Examples

### `project.yaml`

```yaml
# file: projects/example/project.yaml
name: example
base:
  left: http://localhost:8080
  right: http://localhost:8081
defaults:
  timeout_sec: 30
  headers:
    Accept: application/json
    Content-Type: application/json
```

### GET

```yaml
# file: projects/example/requests/get-health.yaml
id: get-health
method: GET
path: /health
query:
  verbose: "true"
headers:
  X-Request-Id: test-1
ignore_paths:
  - $.generated_at
```

### Different paths

```yaml
# file: projects/example/requests/get-user.yaml
id: get-user
method: GET
path: /users/42
left:
  path: /api/v1/users/42
right:
  path: /api/v2/users/42
ignore_paths:
  - $.updated_at
```

### POST

```yaml
# file: projects/example/requests/create-item.yaml
id: create-item
method: POST
path: /items
body:
  name: parity-test-item
  quantity: 1
headers:
  Idempotency-Key: parity-check-create-item
ignore_paths:
  - $.id
  - $.created_at
```
