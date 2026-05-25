# parity-check

CLI to compare HTTP responses from two APIs (left vs right). Requests are defined in YAML per project.

Requires Python 3.11+.

## Installation

```bash
cd parity-check
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

See [docs/deployment.md](docs/deployment.md) for local setup details.

## Quick start

```bash
# list projects
parity-check list

# list requests in a project
parity-check list --project example

# run all requests in a project
parity-check run --project example \
  --left http://localhost:8080 \
  --right http://localhost:8081

# run a single request
parity-check run --project example --request get-health \
  --left http://localhost:8080 \
  --right http://localhost:8081
```

Exit codes: `0` — match, `1` — differences found, `2` — configuration or network error.

## Project layout

```
projects/
  <project-name>/
    project.yaml          # base URLs, defaults
    .env                  # optional local variables
    env/
      dev.yaml            # base + vars for an environment
    requests/
      <request-id>.yaml   # one HTTP request (${VAR} in fields)
```

### project.yaml

| Field | Description |
|-------|-------------|
| `name` | Project name (matches the directory name) |
| `base.left` / `base.right` | Base URLs for each side |
| `defaults.timeout_sec` | HTTP timeout |
| `defaults.headers` | Shared headers |

### requests/*.yaml

| Field | Description |
|-------|-------------|
| `id` | Identifier for `--request` (defaults to the filename without `.yaml`) |
| `method` | GET, POST, PUT, PATCH, DELETE, HEAD |
| `path` | Path relative to the base URL |
| `body` | JSON body (for POST/PUT/PATCH) |
| `query` | Query parameters |
| `headers` | Additional headers |
| `left` / `right` | Per-side overrides: `url`, `path`, `headers`, `body`, `query` |
| `ignore_paths` | JSONPath fields excluded from comparison |
| `skip` | Skip on full project run (`skip_reason` is shown in output) |

JSON object key order in responses is ignored during comparison. Array element order is significant.

## CLI

| Command | Description |
|---------|-------------|
| `parity-check list` | List projects |
| `parity-check list -p <name>` | List requests in a project |
| `parity-check run -p <name>` | Run all requests |
| `parity-check run -p <name> -r <id>` | Run one request |

Global flags: `--projects-dir` (default `./projects`).

`run` flags:

| Flag | Description |
|------|-------------|
| `--left` | Override left base URL from `project.yaml` |
| `--right` | Override right base URL from `project.yaml` |
| `--verbose`, `-v` | Print URL and method for each request before execution |
| `--env`, `-e` | Environment: `projects/<p>/env/<name>.yaml` (or `PARITY_ENV`) |
| `--var` | Variable `KEY=VALUE` (overrides `.env` and `env/*.yaml`) |
| `--side` | `left` or `right` — single service only, no comparison (debug) |
| `--show-headers` | With `--side`: also print response headers (request headers always shown) |
| `-o`, `--output-dir` | Save run results to a directory (console-only without the flag) |

### Saving results

With `-o ./output`, a run is stored under `output/<project>/<timestamp>_<env>/`:

```
output/my-api/20260525_143022_dev/
  summary.json       # counters, endpoints, exit code
  meta.json
  requests/
    get-health.json   # left/right responses, diff, outcome
```

`outcome`: `ok`, `fail`, `error`, `skipped`, `debug`.

### Variables and environments

```bash
# dev: base from env/dev.yaml + vars, ${VAR} substitution in requests
parity-check run --project example --env dev

# override one variable
parity-check run --project example --env dev --var USER_ID=other-uuid

# debug: left side only
parity-check run --project example --env dev -r get-health --side left
parity-check run --project example --env dev -r get-health --side right --show-headers

# save run artifacts
parity-check run --project example --env dev -o ./output

# list environment files for a project
parity-check list --project example
```

Variable precedence: repo `.env` → `projects/<p>/.env` → `vars` in `env/<env>.yaml` → `env/<env>.env` → `--var`.

Environment name when `--env` is omitted: `PARITY_ENV`, else `dev` if `env/dev.yaml` exists, else the only `env/*.yaml` when there is exactly one.

More detail: [docs/architecture.md](docs/architecture.md), [docs/deployment.md](docs/deployment.md).

YAML request schema (for LLM-assisted authoring): [docs/request-schema.md](docs/request-schema.md).

## Tests

```bash
pytest
```

## License

MIT — see [LICENSE](LICENSE).
