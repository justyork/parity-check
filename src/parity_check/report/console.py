import json
import sys
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule
from rich.syntax import Syntax

from parity_check.compare.diff import ComparisonResult
from parity_check.report.labels import endpoint_domain
from parity_check.transport.response import SideRequest, SideResponse

console = Console(stderr=True)


def print_comparison_endpoints(
    left_base: str,
    right_base: str,
    left_protocol: str | None = None,
    right_protocol: str | None = None,
) -> None:
    left_suffix = f" [dim]({left_protocol})[/dim]" if left_protocol else ""
    right_suffix = f" [dim]({right_protocol})[/dim]" if right_protocol else ""
    console.print()
    console.print("[bold]Endpoints[/bold]")
    console.print(f"  [blue]left[/blue]   {endpoint_domain(left_base)}{left_suffix}")
    console.print(f"          [dim]{left_base}[/dim]")
    console.print(f"  [magenta]right[/magenta]  {endpoint_domain(right_base)}{right_suffix}")
    console.print(f"          [dim]{right_base}[/dim]")
    console.print(Rule(style="dim"))
    console.print()


def _format_body(body_text: str) -> str:
    if not body_text.strip():
        return "(empty)"
    try:
        parsed = json.loads(body_text)
        return json.dumps(parsed, indent=2, ensure_ascii=False)
    except json.JSONDecodeError:
        return body_text


def _annotate_diff_labels(diff_text: str, left_label: str, right_label: str) -> str:
    if not diff_text.strip():
        return diff_text

    annotated: list[str] = []
    for line in diff_text.splitlines():
        if line.startswith("--- left"):
            annotated.append(f"--- left ({left_label})")
        elif line.startswith("+++ right"):
            annotated.append(f"+++ right ({right_label})")
        else:
            annotated.append(line)
    return "\n".join(annotated) + "\n"


def _print_headers_block(title: str, headers: dict[str, str]) -> None:
    console.print(f"  {title}:")
    if not headers:
        console.print("    (none)")
        return
    for key, value in sorted(headers.items()):
        console.print(f"    {key}: {value}")


def _format_request_body(body: Any | None) -> str:
    if body is None:
        return "(none)"
    if isinstance(body, (dict, list)):
        return json.dumps(body, indent=2, ensure_ascii=False)
    return str(body)


def print_side_response(
    project_name: str,
    request_id: str,
    side: str,
    side_request: SideRequest,
    response: SideResponse,
    show_headers: bool = False,
) -> None:
    is_grpc = side_request.protocol == "grpc"
    headers_label = "request metadata" if is_grpc else "request headers"
    response_headers_label = "response metadata" if is_grpc else "response headers"
    body_label = "request message" if is_grpc else "request body"

    label = f"{project_name}/{request_id}"
    console.print()
    console.print(f"[cyan][{side.upper()}][/cyan] [bold]{label}[/bold]")
    console.print(f"  [dim]{side_request.protocol}[/dim] {side_request.operation}")
    console.print(f"  {side_request.endpoint}")
    _print_headers_block(headers_label, side_request.headers)
    if side_request.body is not None:
        request_body_formatted = _format_request_body(side_request.body)
        if request_body_formatted.startswith("{") or request_body_formatted.startswith("["):
            console.print(f"  {body_label}:")
            console.print(
                Syntax(request_body_formatted, "json", theme="monokai", line_numbers=False)
            )
        else:
            console.print(f"  {body_label}:")
            for line in request_body_formatted.splitlines():
                console.print(f"    {line}")
    console.print(f"  status: {response.display_status}")
    if show_headers:
        _print_headers_block(response_headers_label, response.headers)
    body_formatted = _format_body(response.body_text)
    if body_formatted.startswith("{") or body_formatted.startswith("["):
        console.print("  response body:")
        console.print(Syntax(body_formatted, "json", theme="monokai", line_numbers=False))
    else:
        console.print("  response body:")
        for line in body_formatted.splitlines():
            console.print(f"    {line}")
    console.print()


def print_comparison(
    project_name: str,
    request_id: str,
    result: ComparisonResult,
    left_label: str,
    right_label: str,
) -> None:
    label = f"{project_name}/{request_id}"

    if result.equal:
        console.print(
            f"[green]OK[/green]  {label}  [dim]{left_label} · {right_label}[/dim]"
        )
        return

    console.print()
    console.print(f"[red]FAIL[/red]  [bold]{label}[/bold]")

    meta_lines: list[str] = []
    if not result.status_equal:
        meta_lines.append(
            f"[bold]status[/bold]  {result.left_status} [blue]({left_label})[/blue]"
            f"  →  {result.right_status} [magenta]({right_label})[/magenta]"
        )
    for detail in result.details:
        meta_lines.append(detail)

    if meta_lines:
        console.print(Panel("\n".join(meta_lines), border_style="red", padding=(0, 1)))

    if not result.body_equal and result.body_diff_text:
        diff_text = _annotate_diff_labels(result.body_diff_text, left_label, right_label)
        console.print(
            Panel(
                Syntax(diff_text, "diff", theme="monokai", line_numbers=False),
                title="body diff",
                border_style="dim",
                padding=(0, 1),
            )
        )

    console.print(Rule(style="dim"))


def print_skipped_request(project_name: str, request_id: str, reason: str | None) -> None:
    label = f"{project_name}/{request_id}"
    suffix = f" — {reason}" if reason else ""
    console.print(f"[yellow]SKIP[/yellow]  {label}[dim]{suffix}[/dim]")


def print_run_summary(passed: int, failed: int, errors: int, skipped: int = 0) -> None:
    console.print()
    console.print(Rule(style="bold"))
    parts = [f"Passed: {passed}", f"Failed: {failed}", f"Errors: {errors}"]
    if skipped > 0:
        parts.append(f"Skipped: {skipped}")
    console.print(", ".join(parts))
    if errors > 0:
        console.print("[red]Completed with errors[/red]")
    elif failed > 0:
        console.print("[red]Completed with differences[/red]")
    else:
        console.print("[green]All requests matched[/green]")


def exit_code(passed: int, failed: int, errors: int) -> int:
    if errors > 0:
        return 2
    if failed > 0:
        return 1
    return 0


def terminate(
    passed: int,
    failed: int,
    errors: int,
    skipped: int = 0,
    output_dir: Path | None = None,
) -> None:
    code = exit_code(passed, failed, errors)
    print_run_summary(passed, failed, errors, skipped)
    if output_dir is not None:
        console.print(f"[dim]Results saved to {output_dir}[/dim]")
    sys.exit(code)
