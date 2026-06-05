# Bundled examples

The repository ships two ready-to-run projects. Use them as templates for your own APIs.

## `example` — HTTP vs HTTP (one port, two paths)

**Goal:** Show that left and right can share the same host but hit different URL paths — common when legacy and new HTTP APIs live behind one gateway or during path renames.

### Layout

```
projects/example/
  project.yaml
  env/local.yaml
  requests/get-health.yaml
  demo_servers.py
```

### Configuration highlights

`env/local.yaml` — both sides on port 8080:

```yaml
base:
  left: http://127.0.0.1:8080
  right: http://127.0.0.1:8080
```

`requests/get-health.yaml` — path overrides:

```yaml
id: get-health
method: GET
path: /health
left:
  path: /health/legacy
right:
  path: /health/v2
query:
  verbose: "true"
ignore_paths:
  - $.generated_at
```

### Run

```bash
python projects/example/demo_servers.py          # terminal 1
parity-check run --project example --env local   # terminal 2
```

Screenshot: [getting-started — Demo 1](getting-started.md#demo-1--http-vs-http-example)

---

## `example-grpc` — HTTP vs gRPC (migration)

**Goal:** Compare a legacy HTTP endpoint with a new gRPC implementation of the same operation.

### Layout

```
projects/example-grpc/
  project.yaml
  env/local.yaml
  proto/greeter.proto
  requests/say-hello.yaml
  demo_servers.py
```

### Configuration highlights

`project.yaml` — protocols per side:

```yaml
defaults:
  sides:
    left: http
    right: grpc
grpc:
  proto_dir: proto
```

`requests/say-hello.yaml` — HTTP on top, gRPC under `right`:

```yaml
id: say-hello
method: GET
path: /hello
query:
  name: ${NAME}
right:
  grpc:
    service: parity.example.v1.Greeter
    method: SayHello
    message:
      name: ${NAME}
ignore_paths:
  - $.code
```

`env/local.yaml` sets `NAME: world` and targets `127.0.0.1`.

### Run

```bash
python projects/example-grpc/demo_servers.py              # terminal 1
parity-check run --project example-grpc --env local -v    # terminal 2
```

Screenshot: [getting-started — Demo 2](getting-started.md#demo-2--http-vs-grpc-example-grpc)

---

## Creating your own project

1. Copy one of the example folders:

   ```bash
   cp -r projects/example projects/my-api
   ```

2. Edit `project.yaml` — set `name` and `base.left` / `base.right` to your service URLs.

3. Add `requests/<scenario>.yaml` — one file per endpoint you want to compare.

4. Optional: `env/staging.yaml` with environment-specific bases and `vars`.

5. For gRPC: add `proto/*.proto` and set `defaults.sides` / `grpc` block as in `example-grpc`.

6. Run:

   ```bash
   parity-check list --project my-api
   parity-check run --project my-api --env staging
   ```

Full field reference: [request-schema.md](request-schema.md).
