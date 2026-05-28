from pathlib import Path
from typing import Annotated

import typer

from parity_check.compare.diff import compare_responses
from parity_check.config.loader import (
    list_environments,
    list_projects,
    list_request_tags,
    list_requests,
    load_project,
)
from parity_check.config.tags import normalize_tags
from parity_check.config.variables import resolve_env_name
from parity_check.errors import ConfigError, ParityCheckError, RequestError
from parity_check.http.client import resolve_side_request
from parity_check.http.runner import run_request_pair, run_request_side
from parity_check.report.artifacts import RunArtifactsWriter
from parity_check.report.console import (
    console,
    exit_code,
    print_comparison,
    print_comparison_endpoints,
    print_side_response,
    print_skipped_request,
    terminate,
)
from parity_check.report.labels import endpoint_domain

app = typer.Typer(
    name="parity-check",
    help="Compare HTTP responses from two API services.",
    no_args_is_help=True,
)

def _default_projects_dir() -> Path:
    return Path.cwd() / "projects"


def _parse_cli_vars(values: list[str] | None) -> dict[str, str]:
    parsed: dict[str, str] = {}
    for item in values or []:
        if "=" not in item:
            raise ConfigError(f"Invalid --var '{item}', expected KEY=VALUE")
        key, _, value = item.partition("=")
        key = key.strip()
        if not key:
            raise ConfigError(f"Invalid --var '{item}', empty key")
        parsed[key] = value
    return parsed


@app.command("list")
def list_cmd(
    project: Annotated[
        str | None,
        typer.Option("--project", "-p", help="Show requests for a specific project"),
    ] = None,
    projects_dir: Annotated[
        Path,
        typer.Option("--projects-dir", help="Directory containing project definitions"),
    ] = None,
) -> None:
    directory = projects_dir or _default_projects_dir()
    projects = list_projects(directory)

    if not projects:
        console.print(f"No projects found in {directory}")
        raise typer.Exit(code=0)

    if project is None:
        console.print("Projects:")
        for project_name in projects:
            request_ids = list_requests(directory, project_name)
            console.print(f"  {project_name} ({len(request_ids)} requests)")
        return

    if project not in projects:
        console.print(f"[red]Project not found: {project}[/red]")
        raise typer.Exit(code=2)

    request_ids = list_requests(directory, project)
    env_names = list_environments(directory, project)
    console.print(f"Project: {project}")
    if env_names:
        console.print("Environments:")
        for env_name in env_names:
            console.print(f"  {env_name}")
    request_tags = list_request_tags(directory, project)
    console.print("Requests:")
    for request_id in request_ids:
        tags = request_tags.get(request_id, [])
        if tags:
            tag_suffix = " [" + ", ".join(tags) + "]"
        else:
            tag_suffix = ""
        console.print(f"  {request_id}{tag_suffix}")


@app.command("run")
def run_cmd(
    project: Annotated[str, typer.Option("--project", "-p", help="Project name")],
    request: Annotated[
        str | None,
        typer.Option("--request", "-r", help="Run a single request by id"),
    ] = None,
    tag: Annotated[
        list[str] | None,
        typer.Option(
            "--tag",
            "-t",
            help="Run requests that have this tag (repeatable; OR semantics)",
        ),
    ] = None,
    left: Annotated[
        str | None,
        typer.Option("--left", help="Override left base URL"),
    ] = None,
    right: Annotated[
        str | None,
        typer.Option("--right", help="Override right base URL"),
    ] = None,
    projects_dir: Annotated[
        Path | None,
        typer.Option("--projects-dir", help="Directory containing project definitions"),
    ] = None,
    verbose: Annotated[
        bool,
        typer.Option("--verbose", "-v", help="Print request URLs"),
    ] = False,
    env: Annotated[
        str | None,
        typer.Option(
            "--env",
            "-e",
            help="Environment (projects/<project>/env/<name>.yaml). Default: PARITY_ENV",
        ),
    ] = None,
    var: Annotated[
        list[str] | None,
        typer.Option("--var", help="Variable KEY=VALUE (overrides .env and env yaml)"),
    ] = None,
    side: Annotated[
        str | None,
        typer.Option(
            "--side",
            help="Debug: run and print response for left or right only (no comparison)",
        ),
    ] = None,
    show_headers: Annotated[
        bool,
        typer.Option("--show-headers", help="With --side: also print response headers"),
    ] = False,
    output_dir: Annotated[
        Path | None,
        typer.Option(
            "--output-dir",
            "-o",
            help="Save run results to a directory (e.g. ./output)",
        ),
    ] = None,
) -> None:
    directory = projects_dir or _default_projects_dir()
    passed = 0
    failed = 0
    errors = 0
    skipped = 0
    run_all_requests = request is None

    try:
        cli_vars = _parse_cli_vars(var)
        filter_tags: list[str] | None = None
        if tag:
            filter_tags = normalize_tags(tag)
        loaded = load_project(
            directory,
            project,
            request_id=request,
            env_name=env,
            cli_vars=cli_vars or None,
            tags=filter_tags,
        )
    except (ConfigError, ValueError) as exc:
        console.print(f"[red]Config error:[/red] {exc}")
        raise typer.Exit(code=2) from exc

    if side is not None and side not in ("left", "right"):
        console.print(f"[red]Invalid --side '{side}', use 'left' or 'right'[/red]")
        raise typer.Exit(code=2)

    project_config = loaded.config.with_base_overrides(left, right)
    left_label = endpoint_domain(project_config.base.left)
    right_label = endpoint_domain(project_config.base.right)

    project_dir = directory / project
    resolved_env = resolve_env_name(project_dir, env)
    mode = "debug" if side else "compare"

    artifacts: RunArtifactsWriter | None = None
    if output_dir is not None:
        artifacts = RunArtifactsWriter(
            output_dir=output_dir.resolve(),
            project=project,
            env_name=resolved_env,
            left_base=project_config.base.left,
            right_base=project_config.base.right,
            left_domain=left_label,
            right_domain=right_label,
            mode=mode,
            request_filter=request,
            tag_filter=filter_tags,
        )

    print_comparison_endpoints(project_config.base.left, project_config.base.right)

    for request_config in loaded.requests:
        label = f"{project}/{request_config.id}"
        if run_all_requests and request_config.skip:
            print_skipped_request(project, request_config.id, request_config.skip_reason)
            skipped += 1
            if artifacts is not None:
                artifacts.record_skipped(request_config.id, request_config.skip_reason)
            continue

        try:
            if side is not None:
                url, method, request_headers, request_body, response = run_request_side(
                    project_config, request_config, side
                )
                print_side_response(
                    project,
                    request_config.id,
                    side,
                    url,
                    method,
                    request_headers,
                    request_body,
                    response,
                    show_headers=show_headers,
                )
                if artifacts is not None:
                    artifacts.record_debug_side(
                        request_config.id, side, method, url, response
                    )
                passed += 1
                continue

            left_url, method, _, _, _ = resolve_side_request(
                "left", project_config, request_config
            )
            right_url, _, _, _, _ = resolve_side_request(
                "right", project_config, request_config
            )

            if verbose:
                console.print(f"[dim]{label}: {method.value} {left_url} | {right_url}[/dim]")

            pair_result = run_request_pair(project_config, request_config)
            comparison = compare_responses(
                pair_result.left,
                pair_result.right,
                ignore_paths=request_config.ignore_paths,
            )
            print_comparison(
                project, request_config.id, comparison, left_label, right_label
            )
            if artifacts is not None:
                artifacts.record_comparison(
                    request_config.id,
                    method,
                    left_url,
                    right_url,
                    pair_result.left,
                    pair_result.right,
                    comparison,
                )
            if comparison.equal:
                passed += 1
            else:
                failed += 1
        except (RequestError, ParityCheckError) as exc:
            console.print(f"[red][ERROR][/red] {label}: {exc}")
            errors += 1
            if artifacts is not None:
                artifacts.record_error(request_config.id, str(exc))

    code = exit_code(passed, failed, errors)
    saved_path: Path | None = None
    if artifacts is not None:
        saved_path = artifacts.finalize(code)

    if side is not None:
        console.print()
        console.print(
            f"[cyan]Debug mode:[/cyan] side={side}, completed={passed}, "
            f"skipped={skipped}, errors={errors}"
        )
        if saved_path is not None:
            console.print(f"[dim]Results saved to {saved_path}[/dim]")
        raise typer.Exit(code=2 if errors else 0)

    terminate(passed, failed, errors, skipped, output_dir=saved_path)
