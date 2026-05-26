import re
import uuid

import pytest

from parity_check.config.variables import substitute_data
from parity_check.errors import ConfigError

_UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.IGNORECASE,
)


def test_random_uuid_same_within_request() -> None:
    data = {
        "path": "/users/${random.uuid}/session",
        "headers": {"X-Request-Id": "${random.uuid}"},
        "body": {"user_id": "${random.uuid}"},
    }
    result = substitute_data(data, {}, random_cache={})
    path_uuid = result["path"].split("/")[2]
    header_uuid = result["headers"]["X-Request-Id"]
    body_uuid = result["body"]["user_id"]

    assert path_uuid == header_uuid == body_uuid
    assert _UUID_RE.match(path_uuid)


def test_random_uuid_diff_between_requests() -> None:
    first = substitute_data({"path": "/${random.uuid}"}, {}, random_cache={})
    second = substitute_data({"path": "/${random.uuid}"}, {}, random_cache={})
    assert first["path"] != second["path"]


def test_random_uuid_valid_format() -> None:
    result = substitute_data({"id": "${random.uuid}"}, {}, random_cache={})
    uuid.UUID(result["id"])


def test_random_hex16() -> None:
    result = substitute_data({"token": "${random.hex16}"}, {}, random_cache={})
    assert len(result["token"]) == 16
    assert all(ch in "0123456789abcdef" for ch in result["token"])


def test_random_uuid_two_slots_in_one_request() -> None:
    result = substitute_data(
        {
            "path": "/users/${random.uuid}/friends/${random.uuid.2}",
            "body": {"owner_id": "${random.uuid}", "friend_id": "${random.uuid.2}"},
        },
        {},
        random_cache={},
    )
    owner = result["body"]["owner_id"]
    friend = result["body"]["friend_id"]
    assert owner != friend
    assert owner in result["path"]
    assert friend in result["path"]


def test_unknown_random_expression() -> None:
    with pytest.raises(ConfigError, match="Unknown random expression"):
        substitute_data({"path": "/${random.unknown}"}, {}, random_cache={})
