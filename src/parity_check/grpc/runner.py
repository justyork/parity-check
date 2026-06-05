import grpc
from google.protobuf import descriptor_pool, json_format, message_factory
from google.protobuf.message import Message

from parity_check.errors import ConfigError, RequestError
from parity_check.grpc.client import ResolvedGrpcRequest
from parity_check.grpc.status import grpc_status_to_http, is_transport_error
from parity_check.transport.response import SideResponse


def _message_class(pool: descriptor_pool.DescriptorPool, full_name: str) -> type[Message]:
    descriptor = pool.FindMessageTypeByName(full_name)
    get_class = getattr(message_factory, "GetMessageClass", None)
    if get_class is not None:
        return get_class(descriptor)
    return message_factory.MessageFactory(pool).GetPrototype(descriptor)


class GrpcRunner:
    def __init__(
        self,
        pool: descriptor_pool.DescriptorPool,
        timeout_sec: float,
        json_preserving_proto_field_name: bool = True,
    ) -> None:
        self._pool = pool
        self._timeout_sec = timeout_sec
        self._preserving = json_preserving_proto_field_name

    def execute(self, resolved: ResolvedGrpcRequest) -> SideResponse:
        try:
            service = self._pool.FindServiceByName(resolved.service)
        except KeyError as exc:
            raise ConfigError(f"gRPC service not found in proto: {resolved.service}") from exc

        method = service.methods_by_name.get(resolved.method)
        if method is None:
            raise ConfigError(
                f"gRPC method '{resolved.method}' not found on service '{resolved.service}'"
            )
        if method.client_streaming or method.server_streaming:
            raise ConfigError(
                f"Streaming RPCs are not supported: {resolved.service}/{resolved.method}"
            )

        request_cls = _message_class(self._pool, method.input_type.full_name)
        response_cls = _message_class(self._pool, method.output_type.full_name)

        request_message = request_cls()
        if resolved.message is not None:
            try:
                json_format.ParseDict(resolved.message, request_message)
            except (json_format.ParseError, TypeError) as exc:
                raise ConfigError(
                    f"Invalid gRPC message for {resolved.service}/{resolved.method}: {exc}"
                ) from exc

        metadata = [(key.lower(), value) for key, value in resolved.metadata.items()]
        endpoint = f"{resolved.target}{resolved.full_method}"

        try:
            with grpc.insecure_channel(resolved.target) as channel:
                rpc = channel.unary_unary(
                    resolved.full_method,
                    request_serializer=request_cls.SerializeToString,
                    response_deserializer=response_cls.FromString,
                )
                response_message = rpc(
                    request_message,
                    timeout=self._timeout_sec,
                    metadata=metadata,
                )
        except grpc.RpcError as exc:
            code = exc.code()
            if is_transport_error(code):
                raise RequestError(
                    f"gRPC call failed for {endpoint}: {code.name} {exc.details()}"
                ) from exc
            return SideResponse(
                status_code=grpc_status_to_http(code),
                body_text="",
                headers={},
                protocol="grpc",
                endpoint=endpoint,
                raw_status=code.name,
            )

        body_text = json_format.MessageToJson(
            response_message,
            preserving_proto_field_name=self._preserving,
        )
        return SideResponse(
            status_code=200,
            body_text=body_text,
            headers={},
            protocol="grpc",
            endpoint=endpoint,
            raw_status=grpc.StatusCode.OK.name,
        )
