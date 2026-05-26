import secrets
import uuid
from collections.abc import Callable

from parity_check.errors import ConfigError

RandomGenerator = Callable[[], str]

_GENERATORS: dict[str, RandomGenerator] = {
    "random.uuid": lambda: str(uuid.uuid4()),
    "random.uuid4": lambda: str(uuid.uuid4()),
    "random.hex16": lambda: secrets.token_hex(8),
    "random.hex32": lambda: secrets.token_hex(16),
}


def is_random_expression(name: str) -> bool:
    return name.startswith("random.")


def _lookup_generator(name: str) -> RandomGenerator:
    for generator_name in sorted(_GENERATORS, key=len, reverse=True):
        if name == generator_name or name.startswith(f"{generator_name}."):
            return _GENERATORS[generator_name]

    known = ", ".join(f"${{{item}}}" for item in sorted(_GENERATORS))
    raise ConfigError(
        f"Unknown random expression: ${{{name}}}. "
        f"Supported base forms: {known}. "
        f"Use a suffix for a second value, e.g. ${{{list(_GENERATORS)[0]}.2}}"
    )


def resolve_random_expression(name: str, cache: dict[str, str]) -> str:
    if name in cache:
        return cache[name]

    value = _lookup_generator(name)()
    cache[name] = value
    return value
