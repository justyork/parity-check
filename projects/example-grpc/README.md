# example-grpc — HTTP vs gRPC demo

Bundled demo project: **left** is HTTP (`127.0.0.1:8080`), **right** is gRPC (`127.0.0.1:50051`) — typical API migration parity.

```bash
# from repository root
python projects/example-grpc/demo_servers.py
parity-check run --project example-grpc --env local --verbose
```

Documentation: [docs/examples.md](../../docs/examples.md) · Screenshots: [docs/getting-started.md](../../docs/getting-started.md)
