"""Demo HTTP server for the example project (left vs right on one port).

Serves two paths with the same business payload; `generated_at` differs and is
ignored via ignore_paths in requests/get-health.yaml.

Usage:
    python projects/example/demo_servers.py
    # in another terminal:
    parity-check run --project example --env local --verbose
"""

import json
import threading
from datetime import UTC, datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

ADDR = ("127.0.0.1", 8080)
ROUTES = {
    "/health/legacy": "legacy",
    "/health/v2": "v2",
}


class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        route = parsed.path

        if route not in ROUTES:
            self.send_error(404, f"unknown path: {route}")
            return

        query = parse_qs(parsed.query)
        if query.get("verbose", [""])[0] != "true":
            self.send_error(400, "expected query verbose=true")
            return

        body = json.dumps(
            {
                "status": "ok",
                "generated_at": datetime.now(UTC).isoformat(),
            }
        ).encode()

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args) -> None:
        pass


def main() -> None:
    server = HTTPServer(ADDR, HealthHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()

    print(f"HTTP  http://{ADDR[0]}:{ADDR[1]}")
    for path in ROUTES:
        print(f"  {path}")
    print("Ready. Run: parity-check run --project example --env local --verbose")
    print("Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()


if __name__ == "__main__":
    main()
