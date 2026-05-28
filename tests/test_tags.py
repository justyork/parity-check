from pathlib import Path

import pytest

from parity_check.config.loader import list_request_tags, load_project
from parity_check.config.models import RequestConfig
from parity_check.config.tags import (
    normalize_tags,
    request_matches_tags,
)
from parity_check.errors import ConfigError


def test_normalize_tags_from_string():
    assert normalize_tags("smoke") == ["smoke"]


def test_normalize_tags_dedupes():
    assert normalize_tags(["smoke", "smoke", "android"]) == ["smoke", "android"]


def test_normalize_tags_rejects_invalid():
    with pytest.raises(ValueError, match="invalid tag"):
        normalize_tags(["bad tag"])


def test_request_matches_tags_or_semantics():
    assert request_matches_tags(["smoke", "android"], ["smoke"])
    assert request_matches_tags(["smoke"], ["smoke", "missing"])
    assert not request_matches_tags(["smoke"], ["android"])
    assert not request_matches_tags([], ["smoke"])


def test_request_config_tags_field():
    request = RequestConfig(
        id="x",
        method="GET",
        path="/x",
        tags=["smoke"],
    )
    assert request.tags == ["smoke"]


def _write_demo_project(project_dir: Path) -> None:
    (project_dir / "requests").mkdir(parents=True)
    (project_dir / "project.yaml").write_text(
        "name: demo\nbase:\n  left: http://left.local\n  right: http://right.local\n",
        encoding="utf-8",
    )
    (project_dir / "requests" / "smoke.yaml").write_text(
        "id: smoke\nmethod: GET\npath: /smoke\ntags: smoke\n",
        encoding="utf-8",
    )
    (project_dir / "requests" / "android.yaml").write_text(
        "id: android\nmethod: GET\npath: /android\ntags:\n  - smoke\n  - android\n",
        encoding="utf-8",
    )
    (project_dir / "requests" / "plain.yaml").write_text(
        "id: plain\nmethod: GET\npath: /plain\n",
        encoding="utf-8",
    )


def test_load_project_filter_by_tag(tmp_path: Path) -> None:
    project_dir = tmp_path / "demo"
    _write_demo_project(project_dir)

    loaded = load_project(tmp_path, "demo", tags=["smoke"])
    assert {item.id for item in loaded.requests} == {"smoke", "android"}


def test_load_project_filter_by_tag_no_match(tmp_path: Path) -> None:
    project_dir = tmp_path / "demo"
    _write_demo_project(project_dir)

    with pytest.raises(ConfigError, match="No requests with tag"):
        load_project(tmp_path, "demo", tags=["gdpr"])


def test_load_project_request_and_tag_mismatch(tmp_path: Path) -> None:
    project_dir = tmp_path / "demo"
    _write_demo_project(project_dir)

    with pytest.raises(ConfigError, match="does not match --tag"):
        load_project(tmp_path, "demo", request_id="plain", tags=["smoke"])


def test_list_request_tags(tmp_path: Path) -> None:
    project_dir = tmp_path / "demo"
    _write_demo_project(project_dir)

    tags = list_request_tags(tmp_path, "demo")
    assert tags["smoke"] == ["smoke"]
    assert tags["android"] == ["smoke", "android"]
    assert tags["plain"] == []
