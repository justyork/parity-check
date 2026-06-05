# parity-check

**Compare two API implementations side by side** — legacy vs new, HTTP vs HTTP, or HTTP vs gRPC — from the terminal. Define scenarios in YAML; no application code required to write tests.

```
  left (reference)          right (candidate)
        │                          │
        ▼                          ▼
   HTTP or gRPC              HTTP or gRPC
        │                          │
        └──────── compare ─────────┘
                 status + JSON body
```

| | |
|---|---|
| **Use cases** | Regression after refactor, API migration (HTTP → gRPC), smoke tests in CI |
| **Config** | YAML projects under `projects/` |
| **Runtime** | Python 3.11+ (CLI tool — you do not write Python to use it) |
| **License** | MIT |

## See it work

### HTTP vs HTTP — same host, different paths

```bash
python projects/example/demo_servers.py          # terminal 1
parity-check run --project example --env local   # terminal 2
```

![HTTP comparison](docs/images/parity_example_http.png)

### HTTP vs gRPC — migration parity

```bash
python projects/example-grpc/demo_servers.py
parity-check run --project example-grpc --env local --verbose
```

![HTTP vs gRPC comparison](docs/images/parity_example_grpc.png)

More screenshots and step-by-step setup: **[Getting started](docs/getting-started.md)**

## Install

```bash
git clone <repository-url> parity-check && cd parity-check
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
parity-check --help
```

Other install paths (pipx, CI): [docs/deployment.md](docs/deployment.md)

## Quick reference

```bash
parity-check list                              # all projects
parity-check list --project example            # requests + environments
parity-check run --project example --env local # compare left vs right
parity-check run -p example -r get-health      # single request
parity-check run -p example --side right       # debug one side only
```

**Exit codes:** `0` match · `1` differences · `2` config or connection error

## How it is organized

```
projects/
  <your-api>/
    project.yaml       # base URLs, defaults, protocol per side
    env/
      staging.yaml     # environment overrides + ${VAR} values
    requests/
      get-user.yaml    # one scenario = one comparison
    proto/             # gRPC only: .proto contract files
```

- **left** — usually the reference (legacy) service  
- **right** — the implementation under test  
- **ignore_paths** — JSON fields excluded from body diff (timestamps, ids, …)

Concepts in plain language: [docs/concepts.md](docs/concepts.md)  
Full YAML reference: [docs/request-schema.md](docs/request-schema.md)  
Bundled demos: [docs/examples.md](docs/examples.md)

## gRPC and mixed HTTP↔gRPC

Mark a side as gRPC via `defaults.sides` or `left.protocol` / `right.protocol`. Put `.proto` files in `projects/<name>/proto/`. gRPC status is normalized to HTTP codes for comparison; response messages are compared as JSON. See `projects/example-grpc/` and [ADR-0001](docs/adr/0001-grpc-and-mixed-protocol-parity.md).

## Documentation

| Doc | Description |
|-----|-------------|
| [docs/README.md](docs/README.md) | Documentation index |
| [Getting started](docs/getting-started.md) | Install + demos with screenshots |
| [Concepts](docs/concepts.md) | Projects, requests, left/right, comparison rules |
| [Examples](docs/examples.md) | `example` and `example-grpc` walkthrough |
| [Request schema](docs/request-schema.md) | Complete YAML specification |
| [Deployment](docs/deployment.md) | CI, env vars, pre-release checks |
| [Architecture](docs/architecture.md) | Modules and internals (contributors) |

## Development

```bash
pytest
ruff check src tests
```

## Cursor skills

Agent skills for authoring and running tests live in [.cursor/skills/](.cursor/skills/).

## License

MIT — see [LICENSE](LICENSE).
