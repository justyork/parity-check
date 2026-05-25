from pathlib import Path

import pytest

from parity_check.config.loader import load_project
from parity_check.config.variables import (
    load_dotenv_file,
    substitute_data,
)
from parity_check.errors import ConfigError


def test_load_dotenv_file(tmp_path: Path) -> None:
    dotenv = tmp_path / ".env"
    dotenv.write_text(
        'FOO=bar\n# comment\nexport BAZ="qux"\nEMPTY=\n',
        encoding="utf-8",
    )
    assert load_dotenv_file(dotenv) == {"FOO": "bar", "BAZ": "qux", "EMPTY": ""}


def test_substitute_nested() -> None:
    data = {
        "path": "/users/${USER_ID}",
        "headers": {"X-Tenant-ID": "${TENANT_ID}"},
        "body": "id=${USER_ID}&name=test",
    }
    result = substitute_data(data, {"USER_ID": "42", "TENANT_ID": "t1"})
    assert result["path"] == "/users/42"
    assert result["headers"]["X-Tenant-ID"] == "t1"
    assert "id=42" in result["body"]


def test_substitute_missing_var() -> None:
    with pytest.raises(ConfigError, match="Undefined variable"):
        substitute_data({"path": "/${MISSING}"}, {})


def test_load_project_with_env_and_vars(tmp_path: Path) -> None:
    project_dir = tmp_path / "demo"
    (project_dir / "requests").mkdir(parents=True)
    (project_dir / "env").mkdir()
    (project_dir / "project.yaml").write_text(
        "name: demo\nbase:\n  left: http://left.local\n  right: http://right.local\n",
        encoding="utf-8",
    )
    (project_dir / "env" / "dev.yaml").write_text(
        "base:\n  left: http://dev-left.local\nvars:\n  TOKEN: secret\n",
        encoding="utf-8",
    )
    (project_dir / "requests" / "ping.yaml").write_text(
        "id: ping\nmethod: GET\npath: /ping/${TOKEN}\n",
        encoding="utf-8",
    )

    loaded = load_project(tmp_path, "demo", env_name="dev")
    assert loaded.config.base.left == "http://dev-left.local"
    assert loaded.requests[0].path == "/ping/secret"
