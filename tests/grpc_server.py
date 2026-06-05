from collections.abc import Callable
from concurrent import futures
from contextlib import contextmanager

import grpc
from google.protobuf import descriptor_pool

from parity_check.grpc.runner import _message_class

SERVICE = "parity.example.v1.Greeter"
METHOD = "SayHello"


@contextmanager
def run_greeter_server(
    pool: descriptor_pool.DescriptorPool,
    behavior: Callable,
):
    request_cls = _message_class(pool, "parity.example.v1.HelloRequest")
    reply_cls = _message_class(pool, "parity.example.v1.HelloReply")

    handler = grpc.unary_unary_rpc_method_handler(
        behavior,
        request_deserializer=request_cls.FromString,
        response_serializer=reply_cls.SerializeToString,
    )
    generic = grpc.method_handlers_generic_handler(SERVICE, {METHOD: handler})

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=2))
    server.add_generic_rpc_handlers((generic,))
    port = server.add_insecure_port("127.0.0.1:0")
    server.start()
    try:
        yield f"127.0.0.1:{port}", reply_cls
    finally:
        server.stop(None)
