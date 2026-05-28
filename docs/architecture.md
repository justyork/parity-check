# Architecture

## Overview

`parity-check` is a CLI tool for regression comparison of HTTP responses from two APIs (for example, a legacy service and a new implementation).

For Cursor agents authoring request YAML aligned with `config/` and `requests/`, see [`.cursor/skills/parity-check-author-requests/SKILL.md`](../.cursor/skills/parity-check-author-requests/SKILL.md).

## Flow

```
CLI (Typer, cli.py)
  → config/loader (YAML + env/*.yaml + .env + ${VAR} → Pydantic)
  → http/client (resolve URL, headers, body per side)
  → http/runner (httpx, left + right)
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
| `config/models.py` | Pydantic configuration models |
| `http/client.py` | Build URL, merge headers/query/body, side overrides |
| `http/runner.py` | Execute HTTP requests via httpx |
| `compare/jsonpath_ignore.py` | Remove fields by JSONPath before comparison |
| `compare/normalize.py` | Recursively sort JSON object keys |
| `compare/diff.py` | Compare status/body, DeepDiff, unified diff for output |
| `report/console.py` | Print OK/FAIL, diff, and summary |
| `report/artifacts.py` | Persist run output (`summary.json`, per-request JSON) |
| `report/labels.py` | Endpoint labels for console output |
| `errors.py` | `ConfigError`, `RequestError` |
| `cli.py` | `list` and `run` commands, exit codes |

## Comparison rules

1. HTTP status and response body are compared. Response headers are not compared.
2. Body is parsed as JSON; on parse failure, text comparison is used. Empty body is handled separately.
3. If body formats differ (JSON vs text), a direct text comparison is performed.
4. `ignore_paths` removes fields by JSONPath before comparison; invalid expressions raise `ConfigError`.
5. For JSON, object keys are sorted recursively (`normalize_json`); array element order is preserved (`DeepDiff` with `ignore_order=False`).
6. On body mismatch, a unified diff of normalized JSON is printed.

## Exit codes

| Code | Meaning |
|------|---------|
| 0 | All requests matched |
| 1 | At least one mismatch |
| 2 | Configuration error, HTTP error, or project not found (`list --project`) |

## Extension points (not in v1)

- Parallel request execution
- Response header comparison
- OpenAPI import
- OAuth / dynamic auth
