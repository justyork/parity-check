from pathlib import Path

from parity_check.config.loader import load_project
from parity_check.config.models import RequestConfig


def test_load_request_with_skip_flag(tmp_path: Path) -> None:
    project_dir = tmp_path / "demo"
    (project_dir / "requests").mkdir(parents=True)
    (project_dir / "project.yaml").write_text(
        "name: demo\nbase:\n  left: http://left.local\n  right: http://right.local\n",
        encoding="utf-8",
    )
    (project_dir / "requests" / "always.yaml").write_text(
        "id: always\nmethod: GET\npath: /ok\n",
        encoding="utf-8",
    )
    (project_dir / "requests" / "skipped.yaml").write_text(
        "id: skipped\nmethod: GET\npath: /skip\nskip: true\nskip_reason: not ready\n",
        encoding="utf-8",
    )

    loaded = load_project(tmp_path, "demo")
    skipped = next(item for item in loaded.requests if item.id == "skipped")
    assert skipped.skip is True
    assert skipped.skip_reason == "not ready"


def test_skip_defaults_false(tmp_path: Path) -> None:
    request = RequestConfig(id="x", method="GET", path="/x")
    assert request.skip is False
    assert request.skip_reason is None
