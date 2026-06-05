# Deployment and CI

`parity-check` is a **local CLI** — there is no server to deploy. You install the command on a developer machine or in a CI runner and point it at your APIs.

New to the tool? Start with [Getting started](getting-started.md).

## Prerequisites

| Requirement | Notes |
|-------------|--------|
| Python **3.11+** | Runtime only; test authors use YAML, not Python |
| Network access | To `base.left` / `base.right` targets |
| gRPC projects | `.proto` files under `projects/<name>/proto/` |

## Installation

### Local development

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

The `parity-check` command is registered via `pyproject.toml` entry point.

### CI / production gate (runtime only)

```bash
pip install -e .
parity-check run --project my-api --env staging
```

Omit `[dev]` when you do not run `pytest` / `ruff` in the same job.

### pipx (optional)

For a user-wide install without activating a venv:

```bash
pipx install .
parity-check --help
```

Run from the repository root so `projects/` is found, or pass `--projects-dir`.

## CI usage

1. Install: `pip install -e .`
2. Set bases (if not in committed `env/*.yaml`):

   ```bash
   parity-check run --project my-api \
     --left "$LEFT_BASE_URL" \
     --right "$RIGHT_BASE_URL"
   ```

3. Fail the job on non-zero exit:

   | Code | Action |
   |------|--------|
   | `0` | Continue pipeline |
   | `1` | Mismatch — investigate diff |
   | `2` | Config or connection error |

### Save artifacts in CI

```bash
parity-check run --project my-api --env staging -o ./parity-output
```

Upload `parity-output/` as a build artifact. Each request file contains left/right bodies and the diff.

## GitHub Actions

The repository includes [`.github/workflows/ci.yml`](../.github/workflows/ci.yml). On push and PR to `main`:

- `pip install -e ".[dev]"`
- `pytest` on Python 3.11, 3.12, 3.13
- `ruff check src tests`

Reuse the same steps in downstream pipelines.

## Environment variables

| Variable | When set | Effect |
|----------|----------|--------|
| `PARITY_ENV` | `--env` omitted on `run` | Same as `--env <name>` — selects `projects/<p>/env/<name>.yaml` |

If neither `--env` nor `PARITY_ENV` is set: use `dev` when `env/dev.yaml` exists; else the only `env/*.yaml` when there is exactly one; else no overlay.

**Variable precedence** (later wins): repo `.env` → `projects/<p>/.env` → `vars` in `env/<env>.yaml` → `env/<env>.env` → `--var KEY=VALUE`.

Details: [request-schema.md](request-schema.md#environments-and-variables).

## Pre-release checks

```bash
pip install -e ".[dev]"
pytest
ruff check src tests
```

## Cursor agents

For agent-driven install and run workflows, see [`.cursor/skills/parity-check-run/SKILL.md`](../.cursor/skills/parity-check-run/SKILL.md).
