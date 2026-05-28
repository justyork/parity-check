---
name: parity-check-author-requests
description: >-
  Generates parity-check HTTP request YAML (project.yaml, env/*.yaml,
  requests/*.yaml) from OpenAPI, curl, code, or API descriptions. Use when creating
  parity tests, request yaml to compare two services, ignore_paths, or left/right
  overrides — including from another repository without knowing the parity-check tool.
---

# parity-check: request authoring (YAML)

Output **valid YAML only**. Start each file block with a path comment:

```yaml
# file: projects/<project_name>/project.yaml
```

```yaml
# file: projects/<project_name>/requests/<request-id>.yaml
```

No explanatory text between blocks.

## Format purpose

- One `requests/<request-id>.yaml` file = **one** HTTP scenario.
- Expected response is **not** described — only the request (method, path, headers, query, body) and fields excluded from comparison (`ignore_paths`).
- The request runs on **left** and **right** with shared fields; side differences go in `left` / `right`.

## Naming

| Rule | Value |
|------|-------|
| Project directory name | = `name` in `project.yaml` |
| `request-id` | kebab-case: `get-health`, `put-session-gdpr-first-launch` |
| File name | `<request-id>.yaml` |
| `id` field | = `request-id` (if omitted, taken from the file name) |

## `project.yaml`

```yaml
# file: projects/<project_name>/project.yaml
name: <project_name>
base:
  left: https://legacy.example.com
  right: https://new.example.com
defaults:
  timeout_sec: 30
  headers:
    Accept: application/json
    Content-Type: application/json
```

| Field | Required | Description |
|-------|----------|-------------|
| `name` | yes | Project name = directory name |
| `base.left`, `base.right` | yes | Base URL with no trailing `/` |
| `defaults.timeout_sec` | no | HTTP timeout (default 30) |
| `defaults.headers` | no | Headers shared by all requests |

## `env/<environment>.yaml`

```yaml
# file: projects/<project_name>/env/dev.yaml
base:
  left: https://api-old.dev.example.com
  right: https://api-new.dev.example.com
vars:
  TENANT_ID: my-tenant
  USER_ID: "00000000-b492-4dd3-bd0f-1852bbb6b003"
  PACKAGE_NAME: com.example.app
```

Secrets go in `.env` (do not commit); team-shared values go in `vars`.

## `requests/<request-id>.yaml`

### Request fields

| Field | Required | Description |
|-------|----------|-------------|
| `id` | yes* | Request id (*or from file name) |
| `method` | yes | `GET`, `POST`, `PUT`, `PATCH`, `DELETE`, `HEAD` |
| `path` | yes | Path relative to base; must start with `/` |
| `body` | no | Body; for JSON — YAML object or array |
| `query` | no | All values must be **strings** |
| `headers` | no | Extra headers (merged over `defaults.headers`) |
| `left`, `right` | no | `SideOverride` only when sides differ |
| `ignore_paths` | no | JSONPath excluded from body comparison |
| `tags` | no | String or list of tags for `parity-check run --tag` |
| `skip` | no | `true` — skip on full project `run` |
| `skip_reason` | no | Skip reason shown in output |

### `SideOverride` (`left` / `right`)

| Field | Purpose |
|-------|---------|
| `url` | Full URL instead of `base + path` |
| `path` | Side-specific path |
| `headers` | Extra side headers |
| `body` | Side-specific body |
| `query` | Extra query parameters |

Shared values at the top level; overrides only where left ≠ right.

### Building the final request

- URL: `base.<side>` + `path`, or `left.url` / `right.url`.
- Headers: `defaults.headers` → `headers` → `left.headers` / `right.headers`.
- Query: `query` → `left.query` / `right.query`.
- Body: shared `body`, else `left.body` / `right.body`.

### `body` by method

| method | body |
|--------|------|
| GET, HEAD, DELETE | `null` or omit |
| POST, PUT, PATCH | YAML object/array → JSON |

Form-urlencoded: string in `body` + `Content-Type: application/x-www-form-urlencoded`.

### Substitution

- `${VAR}` — from `vars` / `.env` / `--var`; name `[A-Za-z_][A-Za-z0-9_]*`.
- Works in `path`, `url`, `headers`, `query`, `body` (including form strings).

| Expression | Example |
|------------|---------|
| `${random.uuid}` | UUID v4 |
| `${random.uuid.2}` | second independent UUID in the same request |
| `${random.hex16}` / `${random.hex32}` | hex |

Repeating `${random.uuid}` in a file = one value on left and right. A new random set per request file per run.

### `tags`

Optional label(s) for selective runs. Tag format: `[A-Za-z0-9][A-Za-z0-9._-]*`.

```yaml
tags: smoke
```

```yaml
tags:
  - smoke
  - android
```

CLI: `--tag smoke` runs requests that have tag `smoke`; multiple `-t` flags use OR (any match).

### `ignore_paths`

JSONPath ([jsonpath-ng](https://github.com/h2non/jsonpath-ng)). Typical:

- `$.created_at`, `$.updated_at`, `$.generated_at`
- `$.meta.request_id`, `$.trace_id`, `$.instance`
- `$.id` after create
- `$.items[*].updated_at`

Add when a field is unstable but business meaning should match.

## Rules for generating request sets

1. **One file — one scenario** (do not combine multiple endpoints in one yaml).
2. **Meaningful `id`**: `get-health`, `put-session-invalid-body-400`.
3. **Coverage**: happy path, typical query params, important POST/PUT/PATCH, separate negative cases when needed for parity.
4. **No duplicates** with the same effective method + path + body + query.
5. **Stable data** in vars; use `${random.*}` only when unique ids are needed in one request.
6. **Endpoint source** — only from context (OpenAPI, code, user curl); do not invent paths.
7. **Auth** — static headers in `defaults.headers` or `headers`.
8. Methods only: GET, POST, PUT, PATCH, DELETE, HEAD.

## Pre-output checklist

- [ ] `path` starts with `/`
- [ ] All `query` values are strings (quote numbers: `"1"`)
- [ ] `left`/`right` only when sides actually differ
- [ ] `ignore_paths` for timestamp/id/trace when they will differ
- [ ] `# file: projects/...` on every block
- [ ] `id` matches the file name
- [ ] `tags` use valid names when grouping scenarios for `--tag` runs

## Examples

### GET

```yaml
# file: projects/example/requests/get-health.yaml
id: get-health
method: GET
path: /health
query:
  verbose: "true"
ignore_paths:
  - $.generated_at
```

### Different paths per side

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

### POST JSON

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

### POST form + vars + random

```yaml
# file: projects/example/requests/post-session.yaml
id: post-session
method: POST
path: /session
headers:
  Content-Type: application/x-www-form-urlencoded
body: >-
  package_name=${PACKAGE_NAME}&user_id=${random.uuid}&os_version=${OS_VERSION}
right:
  headers:
    X-Tenant-ID: ${TENANT_ID}
ignore_paths:
  - $.install_date
```

### Skip until parity is fixed

```yaml
# file: projects/my-api/requests/put-invalid-body-400.yaml
id: put-invalid-body-400
method: PUT
path: /api/v1/users/${USER_ID}/session
body:
  language: en
skip: true
skip_reason: right returns 200 until validation fixed; left returns 400
ignore_paths:
  - $.traceId
  - $.detail
```

## Working from another repository

The parity-check project may live separately. Agent output:

1. Place files under `projects/<name>/` **in the parity-check repository** (or give the user blocks with `# file:` to copy).
2. Create or update `project.yaml` and `env/*.yaml` together with the first requests.
3. Do not put foreign-repo internal paths in `path` — only real API paths.
4. Put ids, tenant, package in env `vars`; do not hardcode secrets in request yaml.

After generation, the user runs (skill `parity-check-run`):

```bash
parity-check run --project <name> --env dev --request <request-id>
```

## More

Extended examples and edge cases: [examples.md](examples.md)

Full schema in the parity-check repo: `docs/request-schema.md`.
