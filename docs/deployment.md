# Deployment

`parity-check` is a local CLI with no server component. Deployment is limited to installing it in a virtual environment.

For Cursor agents installing and running the CLI, see [`.cursor/skills/parity-check-run/SKILL.md`](../.cursor/skills/parity-check-run/SKILL.md).

## Local installation

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

After installation, the `parity-check` command is available (entry point from `pyproject.toml`).

## CI usage

1. Create a venv and install the package: `pip install -e .` (omit `[dev]` if you do not run tests).
2. Run comparison with the required base URLs:

```bash
parity-check run --project example \
  --left "$LEFT_BASE_URL" \
  --right "$RIGHT_BASE_URL"
```

3. Interpret the exit code: `0` — match, `1` — differences, `2` — configuration or HTTP error.

## GitHub Actions CI

The repository includes [`.github/workflows/ci.yml`](../.github/workflows/ci.yml). On push and pull requests to `main` it:

- installs the package with `pip install -e ".[dev]"`
- runs `pytest` on Python 3.11, 3.12, and 3.13
- runs `ruff check src tests`

Forks and downstream pipelines can reuse the same steps for release gates.

## Environment variables

| Variable | When set | Effect |
|----------|----------|--------|
| `PARITY_ENV` | `--env` / `-e` omitted on `run` | Selects `projects/<project>/env/<name>.yaml` (same as passing `--env <name>`) |

If neither `--env` nor `PARITY_ENV` is set, the CLI picks `dev` when `env/dev.yaml` exists; otherwise the sole `env/*.yaml` file if there is exactly one; otherwise no environment overlay is applied.

Variable substitution precedence (later wins): repo `.env` → `projects/<p>/.env` → `vars` in `env/<env>.yaml` → `env/<env>.env` → `--var`. See [request-schema.md](request-schema.md) for the YAML layout.

## Pre-release checks

```bash
pip install -e ".[dev]"
pytest
ruff check src tests
```
