---
name: parity-check-run
description: >-
  Installs and runs the parity-check CLI to compare HTTP responses (left vs right),
  debug a single service, manage env/variables, and inspect run artifacts. Use when
  working with parity-check, API parity, legacy vs new implementation regression,
  list/run commands, --env, --side, --output-dir.
---

# parity-check: run and debug

The CLI compares HTTP responses from two APIs (**left** — usually legacy, **right** — new implementation). One yaml file = one HTTP request; expected responses are not defined in yaml — the tool compares actual responses.

## Installation

Requires Python 3.11+.

```bash
cd <parity-check repository root>
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

The `parity-check` command is available after install (`pyproject.toml` → entry point).

Verify: `parity-check --help`.

## Data layout (what the CLI reads)

```
projects/
  <project-name>/
    project.yaml       # base.left / base.right, defaults
    .env               # local secrets (gitignore)
    env/
      dev.yaml         # base + vars for an environment
      dev.env          # optional dotenv for env
    requests/
      <request-id>.yaml
```

Run from the repository root (or pass `--projects-dir`).

## Commands

### List projects and requests

```bash
parity-check list
parity-check list --project consent-metrics
```

For a project, environments (`env/*.yaml`) and request ids are listed (tags in brackets when set).

### Comparison (main workflow)

All requests in a project:

```bash
parity-check run --project consent-metrics --env dev
```

Single request:

```bash
parity-check run --project consent-metrics --env dev --request post-session-android-form
```

By tag (OR if multiple `-t`; only requests that define matching tags):

```bash
parity-check run --project consent-metrics --env dev --tag smoke
parity-check run -p consent-metrics -e dev -t smoke -t android
```

Override base URLs (on top of `project.yaml` / `env/*.yaml`):

```bash
parity-check run --project example \
  --left https://legacy.example.com \
  --right https://new.example.com
```

Print URLs before execution:

```bash
parity-check run -p consent-metrics -e dev -v
```

### Variables and environments

| Source | When |
|--------|------|
| `--env`, `-e` | File `projects/<p>/env/<name>.yaml` |
| `PARITY_ENV` | Same when `--env` is omitted |
| `--var KEY=VALUE` | Overrides everything below |
| `.env` | repo → `projects/<p>/.env` → `env/<name>.env` |
| `vars` in `env/<name>.yaml` | With `--env` |

Env selection without a flag: `PARITY_ENV` → else `dev` if `env/dev.yaml` exists → else the only `env/*.yaml`.

Examples:

```bash
parity-check run --project consent-metrics --env dev --var USER_ID=other-uuid
export PARITY_ENV=local
parity-check run --project consent-metrics
```

In yaml, use `${VAR_NAME}`; built-ins: `${random.uuid}`, `${random.uuid.2}`, `${random.hex16}`, `${random.hex32}` (one slot = one value for the whole request and both sides).

### Debug one side (no comparison)

```bash
parity-check run -p consent-metrics -e dev -r post-session-android-form --side left
parity-check run -p consent-metrics -e dev -r post-session-android-form --side right --show-headers
```

Prints URL, method, request headers, request body, status, and response body.

### Save run artifacts

```bash
parity-check run -p consent-metrics -e dev -o ./output
```

Layout: `output/<project>/<timestamp>_<env>/summary.json`, `meta.json`, `requests/<id>.json`.

`outcome` in per-request json: `ok`, `fail`, `error`, `skipped`, `debug`.

## Exit codes

| Code | Meaning |
|------|---------|
| 0 | All comparisons matched (or debug with no errors) |
| 1 | Response mismatches |
| 2 | Configuration error, HTTP error, or project not found |

In CI: `pip install -e .` and `parity-check run ...`; interpret the exit code.

## Common workflows

**New request — right first, then compare:**

```bash
parity-check run -p my-api -e dev -r my-request --side right
parity-check run -p my-api -e dev -r my-request
```

**Skip on full project run:** set `skip: true` and `skip_reason` in yaml; with explicit `-r <id>` the request still runs.

**Document a known gap:** `projects/<p>/parity-gaps/<request-id>.md` (template `_template.md`) plus a reproduce command with `-r`.

**Request chains:** `flows.yaml` in a project is reference-only (shared `user_id` across steps); the CLI does not run flows automatically yet — run steps individually or via an external script.

## Comparison rules (what to expect in output)

- HTTP status and body are compared; response headers are not.
- JSON: object key order does not matter; array element order does.
- `ignore_paths` — JSONPath fields excluded from body comparison.
- On JSON parse failure — compare as text.

## Local package development

```bash
pytest
ruff check src tests
```

## See also

- Request yaml format: skill `parity-check-author-requests`
- Full schema in this repo: [docs/request-schema.md](../../docs/request-schema.md)
