from pathlib import Path

import pytest

from parity_check.errors import ConfigError
from parity_check.grpc.proto_loader import get_descriptor_pool

PROTO_DIR = Path(__file__).parent / "fixtures" / "proto"


def test_descriptor_pool_finds_service():
    pool = get_descriptor_pool(PROTO_DIR)
    service = pool.FindServiceByName("parity.example.v1.Greeter")
    assert service.methods_by_name["SayHello"].input_type.full_name == (
        "parity.example.v1.HelloRequest"
    )


def test_missing_proto_dir_raises(tmp_path: Path):
    with pytest.raises(ConfigError):
        get_descriptor_pool(tmp_path / "nope")


def test_empty_proto_dir_raises(tmp_path: Path):
    (tmp_path / "empty").mkdir()
    with pytest.raises(ConfigError):
        get_descriptor_pool(tmp_path / "empty")
