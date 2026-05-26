# parity-check request schema

This document describes the YAML format under `projects/`. Use it as the single source of truth when generating request configuration to compare two HTTP APIs (**left** and **right**).

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
| `defaults.timeout_sec` | no | number | HTTP timeout in seconds (default 30) |
| `defaults.headers` | no | map[string]string | Headers shared by all requests |

`base.left` / `base.right` are environment placeholders (localhost, staging). They do not need to be final production URLs in committed yaml.

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
| `method` | yes | enum | `GET`, `POST`, `PUT`, `PATCH`, `DELETE`, `HEAD` |
| `path` | yes | string | Path relative to `base`; must start with `/` |
| `body` | no | any | Request body; for JSON — YAML object or array |
| `query` | no | map[string]string | Query parameters; **all values are strings** |
| `headers` | no | map[string]string | Request headers (merged over `defaults.headers`) |
| `left` | no | SideOverride | Overrides for left only |
| `right` | no | SideOverride | Overrides for right only |
| `ignore_paths` | no | list[string] | JSONPath fields excluded from response body comparison |
| `skip` | no | bool | `true` — skip on full project run (default: `false`) |
| `skip_reason` | no | string | Skip reason shown in console output |

With explicit `--request <id>`, the request runs even when `skip: true`.

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
| `url` | string | Full request URL |
| `path` | string | Path instead of shared `path` |
| `headers` | map[string]string | Additional side headers |
| `body` | any | Body instead of shared `body` |
| `query` | map[string]string | Additional side query parameters |

Use overrides only when left and right actually differ. Shared values belong in top-level `path`, `body`, `query`, `headers`.

| Situation | Fields |
|-----------|--------|
| Different API paths | `left.path`, `right.path` |
| Different bodies | `left.body`, `right.body` |
| Different query | `left.query`, `right.query` |
| URL cannot be built from base + path | `left.url` or `right.url` |

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
