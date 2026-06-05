# Concepts

This page explains how parity-check thinks about your APIs. No Python knowledge required.

## Left and right

Every comparison has two sides:

| Side | Typical role |
|------|----------------|
| **left** | Legacy / reference implementation (the baseline) |
| **right** | New implementation (what you are validating) |

Both sides receive the **same logical request** (or side-specific overrides when paths or payloads differ). The tool compares **status** and **response body** — headers and gRPC metadata are shown in debug mode but not compared.

## Project

A **project** is a folder under `projects/<name>/` with:

- `project.yaml` — base addresses and defaults
- `requests/*.yaml` — one file per scenario
- optional `env/<environment>.yaml` — URLs and variables per environment
- optional `proto/` — gRPC contract files

You can keep several projects in one repository (e.g. `billing-api`, `user-service`).

## Request

One **request** = one scenario (one call on the left and one on the right).

Example: `get-health` sends GET `/health/legacy` to the left and GET `/health/v2` to the right.

Fields you configure:

- **HTTP**: `method`, `path`, `query`, `headers`, `body`
- **gRPC**: `grpc.service`, `grpc.method`, `grpc.message`, `grpc.metadata`
- **Per side**: `left` / `right` overrides when the two APIs differ
- **ignore_paths**: JSON fields to skip when comparing bodies (timestamps, trace ids, …)

## Environment

An **environment** (`--env dev`, `--env staging`, …) selects `projects/<name>/env/<env>.yaml`. That file can override `base.left` / `base.right` and define **variables** (`vars`) substituted as `${VAR_NAME}` in requests.

Secrets stay in `.env` files (not committed); shared team values go in `env/*.yaml`.

## Protocol per side

Each side is either **http** or **grpc**:

1. `left.protocol` / `right.protocol` on the request
2. else `defaults.sides.left` / `defaults.sides.right` in `project.yaml`
3. else **http** (existing HTTP-only projects unchanged)

Mixed mode (HTTP left + gRPC right) is the common migration pattern.

## Comparison rules (what “match” means)

1. **Status** must match. gRPC codes are mapped to HTTP equivalents (`OK` → 200, `NOT_FOUND` → 404, …).
2. **Body** is compared as JSON when possible. Object key order does not matter; array order does.
3. Fields listed in **ignore_paths** are removed before comparison.
4. Empty HTTP body and empty gRPC message `{}` are treated as equal.

When something differs, the CLI prints a **unified diff** of the normalized JSON.

## Exit codes

| Code | Meaning |
|------|---------|
| `0` | All requests matched |
| `1` | At least one mismatch (status or body) |
| `2` | Config error, connection failure, or invalid YAML |

Use exit codes in CI: `parity-check run ... && deploy` or fail the pipeline on non-zero.

## Artifacts

With `-o ./output` each run is saved under `output/<project>/<timestamp>_<env>/`:

- `summary.json` — counts and exit code
- `requests/<id>.json` — left/right responses, diff, outcome (`ok` / `fail` / `error` / `skipped`)

Useful for CI logs, sharing failures, and debugging without re-running against production.
