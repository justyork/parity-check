# example — HTTP vs HTTP demo

Bundled demo project: **left** and **right** both use HTTP on `127.0.0.1:8080`, but different paths (`/health/legacy` vs `/health/v2`).

```bash
# from repository root
python projects/example/demo_servers.py
parity-check run --project example --env local --verbose
```

Documentation: [docs/examples.md](../../docs/examples.md) · Screenshots: [docs/getting-started.md](../../docs/getting-started.md)
