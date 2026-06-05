import tempfile
from pathlib import Path

from google.protobuf import descriptor_pb2, descriptor_pool

from parity_check.errors import ConfigError


def _proto_files(proto_dir: Path) -> list[Path]:
    return sorted(proto_dir.rglob("*.proto"))


def _signature(proto_dir: Path, files: list[Path]) -> tuple:
    return (str(proto_dir.resolve()), tuple((str(path), path.stat().st_mtime) for path in files))


_pool_cache: dict[tuple, descriptor_pool.DescriptorPool] = {}


def get_descriptor_pool(proto_dir: Path) -> descriptor_pool.DescriptorPool:
    if not proto_dir.exists():
        raise ConfigError(f"proto directory not found: {proto_dir}")

    files = _proto_files(proto_dir)
    if not files:
        raise ConfigError(f"No .proto files found in {proto_dir}")

    cache_key = _signature(proto_dir, files)
    cached = _pool_cache.get(cache_key)
    if cached is not None:
        return cached

    file_set = _compile_descriptor_set(proto_dir, files)
    pool = descriptor_pool.DescriptorPool()
    for file_proto in file_set.file:
        pool.Add(file_proto)

    _pool_cache[cache_key] = pool
    return pool


def _compile_descriptor_set(
    proto_dir: Path, files: list[Path]
) -> descriptor_pb2.FileDescriptorSet:
    from grpc_tools import protoc

    well_known = Path(protoc.__file__).parent / "_proto"

    with tempfile.NamedTemporaryFile(suffix=".pb", delete=False) as tmp:
        out_path = Path(tmp.name)

    try:
        args = [
            "grpc_tools.protoc",
            f"-I{proto_dir}",
            f"-I{well_known}",
            f"--descriptor_set_out={out_path}",
            "--include_imports",
            *[str(path) for path in files],
        ]
        result = protoc.main(args)
        if result != 0:
            raise ConfigError(f"protoc failed to compile proto files in {proto_dir}")

        file_set = descriptor_pb2.FileDescriptorSet()
        file_set.ParseFromString(out_path.read_bytes())
        return file_set
    finally:
        out_path.unlink(missing_ok=True)
