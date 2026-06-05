"""Demo servers for the example-grpc project.

Starts an HTTP server (left) and a gRPC Greeter server (right) that return the
same logical payload, so `parity-check run -p example-grpc -e local` reports OK.

Usage:
    python projects/example-grpc/demo_servers.py
    # in another terminal:
    parity-check run --project example-grpc --env local --verbose
"""

import json
import threading
from concurrent import futures
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import grpc

from parity_check.grpc.proto_loader import get_descriptor_pool
from parity_check.grpc.runner import _message_class

PROTO_DIR = Path(__file__).parent / "proto"
HTTP_ADDR = ("127.0.0.1", 8080)
GRPC_ADDR = "127.0.0.1:50051"

POOL = get_descriptor_pool(PROTO_DIR)


class HelloHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        # The "code" field differs from gRPC on purpose; it is dropped via
        # ignore_paths ($.code) in requests/say-hello.yaml.
        body = json.dumps({"message": "hello world", "code": 99}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args) -> None:  # silence access logs
        pass


def _say_hello(request, context):
    reply_cls = _message_class(POOL, "parity.example.v1.HelloReply")
    reply = reply_cls()
    reply.message = f"hello {request.name}"
    reply.code = 7
    return reply


def _start_grpc() -> grpc.Server:
    request_cls = _message_class(POOL, "parity.example.v1.HelloRequest")
    reply_cls = _message_class(POOL, "parity.example.v1.HelloReply")
    handler = grpc.unary_unary_rpc_method_handler(
        _say_hello,
        request_deserializer=request_cls.FromString,
        response_serializer=reply_cls.SerializeToString,
    )
    generic = grpc.method_handlers_generic_handler(
        "parity.example.v1.Greeter", {"SayHello": handler}
    )
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=4))
    server.add_generic_rpc_handlers((generic,))
    server.add_insecure_port(GRPC_ADDR)
    server.start()
    return server


def main() -> None:
    http_server = HTTPServer(HTTP_ADDR, HelloHandler)
    threading.Thread(target=http_server.serve_forever, daemon=True).start()
    grpc_server = _start_grpc()

    print(f"HTTP  (left)  http://{HTTP_ADDR[0]}:{HTTP_ADDR[1]}")
    print(f"gRPC  (right) {GRPC_ADDR}")
    print("Ready. Run: parity-check run --project example-grpc --env local --verbose")
    print("Ctrl+C to stop.")
    try:
        grpc_server.wait_for_termination()
    except KeyboardInterrupt:
        http_server.shutdown()
        grpc_server.stop(None)


if __name__ == "__main__":
    main()
