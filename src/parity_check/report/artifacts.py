import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from parity_check.compare.diff import ComparisonResult
from parity_check.config.models import HttpMethod
from parity_check.http.runner import HttpResponse


@dataclass
class ResponseSnapshot:
    url: str
    status_code: int
    headers: dict[str, str]
    body_text: str


@dataclass
class RequestRunRecord:
    request_id: str
    outcome: str
    method: str | None = None
    left: ResponseSnapshot | None = None
    right: ResponseSnapshot | None = None
    side: str | None = None
    comparison: dict[str, Any] | None = None
    skip_reason: str | None = None
    error: str | None = None


@dataclass
class RunSummary:
    project: str
    env: str | None
    mode: str
    left_base: str
    right_base: str
    left_domain: str
    right_domain: str
    started_at: str
    finished_at: str | None = None
    passed: int = 0
    failed: int = 0
    errors: int = 0
    skipped: int = 0
    exit_code: int = 0
    request_filter: str | None = None


def _snapshot(url: str, response: HttpResponse) -> ResponseSnapshot:
    return ResponseSnapshot(
        url=url,
        status_code=response.status_code,
        headers=response.headers,
        body_text=response.body_text,
    )


def _comparison_to_dict(comparison: ComparisonResult) -> dict[str, Any]:
    return {
        "equal": comparison.equal,
        "status_equal": comparison.status_equal,
        "body_equal": comparison.body_equal,
        "left_status": comparison.left_status,
        "right_status": comparison.right_status,
        "body_format": comparison.body_format,
        "details": comparison.details,
        "body_diff": comparison.body_diff_text,
    }


def build_run_directory_name(env_name: str | None) -> str:
    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    if env_name:
        return f"{timestamp}_{env_name}"
    return timestamp


class RunArtifactsWriter:
    def __init__(
        self,
        output_dir: Path,
        project: str,
        env_name: str | None,
        left_base: str,
        right_base: str,
        left_domain: str,
        right_domain: str,
        mode: str,
        request_filter: str | None = None,
    ) -> None:
        run_name = build_run_directory_name(env_name)
        self.run_dir = output_dir / project / run_name
        self.requests_dir = self.run_dir / "requests"
        self.requests_dir.mkdir(parents=True, exist_ok=True)

        self._summary = RunSummary(
            project=project,
            env=env_name,
            mode=mode,
            left_base=left_base,
            right_base=right_base,
            left_domain=left_domain,
            right_domain=right_domain,
            started_at=datetime.now(UTC).isoformat(),
            request_filter=request_filter,
        )

    @property
    def path(self) -> Path:
        return self.run_dir

    def record_skipped(self, request_id: str, skip_reason: str | None) -> None:
        self._summary.skipped += 1
        self._write_request(
            RequestRunRecord(
                request_id=request_id,
                outcome="skipped",
                skip_reason=skip_reason,
            )
        )

    def record_comparison(
        self,
        request_id: str,
        method: HttpMethod,
        left_url: str,
        right_url: str,
        left_response: HttpResponse,
        right_response: HttpResponse,
        comparison: ComparisonResult,
    ) -> None:
        if comparison.equal:
            self._summary.passed += 1
            outcome = "ok"
        else:
            self._summary.failed += 1
            outcome = "fail"

        self._write_request(
            RequestRunRecord(
                request_id=request_id,
                outcome=outcome,
                method=method.value,
                left=_snapshot(left_url, left_response),
                right=_snapshot(right_url, right_response),
                comparison=_comparison_to_dict(comparison),
            )
        )

    def record_error(self, request_id: str, error: str) -> None:
        self._summary.errors += 1
        self._write_request(
            RequestRunRecord(
                request_id=request_id,
                outcome="error",
                error=error,
            )
        )

    def record_debug_side(
        self,
        request_id: str,
        side: str,
        method: HttpMethod,
        url: str,
        response: HttpResponse,
    ) -> None:
        self._summary.passed += 1
        snapshot = _snapshot(url, response)
        record = RequestRunRecord(
            request_id=request_id,
            outcome="debug",
            method=method.value,
            side=side,
        )
        if side == "left":
            record.left = snapshot
        else:
            record.right = snapshot
        self._write_request(record)

    def finalize(self, exit_code: int) -> Path:
        self._summary.finished_at = datetime.now(UTC).isoformat()
        self._summary.exit_code = exit_code

        summary_path = self.run_dir / "summary.json"
        meta_path = self.run_dir / "meta.json"

        summary_path.write_text(
            json.dumps(asdict(self._summary), indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        meta = {
            "run_dir": str(self.run_dir),
            "requests_dir": str(self.requests_dir),
            "request_count": len(list(self.requests_dir.glob("*.json"))),
        }
        meta_path.write_text(
            json.dumps(meta, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        return self.run_dir

    def _write_request(self, record: RequestRunRecord) -> None:
        path = self.requests_dir / f"{record.request_id}.json"
        path.write_text(
            json.dumps(asdict(record), indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
