import grpc

from parity_check.grpc.status import grpc_status_to_http, is_transport_error


def test_status_mapping_known_codes():
    assert grpc_status_to_http(grpc.StatusCode.OK) == 200
    assert grpc_status_to_http(grpc.StatusCode.NOT_FOUND) == 404
    assert grpc_status_to_http(grpc.StatusCode.INVALID_ARGUMENT) == 400
    assert grpc_status_to_http(grpc.StatusCode.PERMISSION_DENIED) == 403
    assert grpc_status_to_http(grpc.StatusCode.UNAUTHENTICATED) == 401


def test_transport_errors():
    assert is_transport_error(grpc.StatusCode.UNAVAILABLE)
    assert is_transport_error(grpc.StatusCode.DEADLINE_EXCEEDED)
    assert not is_transport_error(grpc.StatusCode.NOT_FOUND)
