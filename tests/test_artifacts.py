import json
from pathlib import Path

from parity_check.compare.diff import compare_responses
from parity_check.config.models import HttpMethod
from parity_check.http.runner import HttpResponse
from parity_check.report.artifacts import RunArtifactsWriter


def test_run_artifacts_writer(tmp_path: Path) -> None:
    writer = RunArtifactsWriter(
        output_dir=tmp_path,
        project="demo",
        env_name="dev",
        left_base="http://left.local",
        right_base="http://right.local",
        left_domain="left.local",
        right_domain="right.local",
        mode="compare",
    )

    writer.record_skipped("skipped-one", "not applicable")
    writer.record_comparison(
        "check-one",
        HttpMethod.GET,
        "http://left.local/health",
        "http://right.local/health",
        HttpResponse(200, '{"ok":true}', {}),
        HttpResponse(200, '{"ok":false}', {}),
        compare_responses(
            HttpResponse(200, '{"ok":true}', {}),
            HttpResponse(200, '{"ok":false}', {}),
        ),
    )
    writer.record_error("broken", "connection refused")

    run_dir = writer.finalize(exit_code=1)

    summary = json.loads((run_dir / "summary.json").read_text(encoding="utf-8"))
    assert summary["passed"] == 0
    assert summary["failed"] == 1
    assert summary["errors"] == 1
    assert summary["skipped"] == 1
    assert summary["exit_code"] == 1

    request_file = run_dir / "requests" / "check-one.json"
    assert request_file.exists()
    request_data = json.loads(request_file.read_text(encoding="utf-8"))
    assert request_data["outcome"] == "fail"
    assert request_data["comparison"]["equal"] is False
