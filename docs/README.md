# parity-check documentation

**parity-check** is a command-line tool that sends the same logical request to two API endpoints and compares the responses. You describe requests in YAML — no Python code required to write tests.

Typical uses:

- Regression check: legacy service vs new implementation
- API migration: HTTP (old) vs gRPC (new) in one request
- Smoke tests in CI with clear pass/fail exit codes

## Start here

| Document | Who it is for |
|----------|----------------|
| [Getting started](getting-started.md) | First install and first successful run (with screenshots) |
| [Concepts](concepts.md) | How projects, requests, left/right, and comparison work |
| [Examples](examples.md) | Bundled `example` and `example-grpc` projects step by step |
| [Request schema](request-schema.md) | Full YAML reference for authoring requests |
| [Deployment & CI](deployment.md) | Install options, pipelines, environment variables |
| [Architecture](architecture.md) | Internal modules and comparison rules (contributors) |

## What you need

- **Python 3.11+** on your machine (runtime only — you do not write Python to use the tool)
- Network access to the APIs you compare
- For gRPC: `.proto` files in your project directory

## Documentation map

```
docs/
  README.md           ← you are here
  getting-started.md  ← install + demo runs
  concepts.md         ← mental model
  examples.md         ← example / example-grpc
  request-schema.md   ← YAML reference
  deployment.md       ← CI / install
  architecture.md     ← internals
  adr/                ← architecture decision records
  images/             ← terminal screenshots
```

## Quick links from the repository root

- [README](../README.md) — project overview
- [projects/example](../projects/example/) — HTTP vs HTTP (same host, different paths)
- [projects/example-grpc](../projects/example-grpc/) — HTTP vs gRPC migration demo
