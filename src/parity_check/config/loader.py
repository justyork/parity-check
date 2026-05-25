from pathlib import Path

import yaml

from parity_check.config.env_merge import apply_env_to_project_data
from parity_check.config.models import LoadedProject, ProjectConfig, RequestConfig
from parity_check.config.variables import (
    build_variable_context,
    list_env_names,
    load_env_overlay,
    resolve_env_name,
    substitute_data,
)
from parity_check.errors import ConfigError


def _load_yaml(path: Path) -> dict:
    if not path.exists():
        raise ConfigError(f"File not found: {path}")
    with path.open(encoding="utf-8") as file:
        data = yaml.safe_load(file)
    if not isinstance(data, dict):
        raise ConfigError(f"Expected YAML mapping in {path}")
    return data


def list_projects(projects_dir: Path) -> list[str]:
    if not projects_dir.exists():
        return []
    return sorted(
        entry.name
        for entry in projects_dir.iterdir()
        if entry.is_dir() and (entry / "project.yaml").exists()
    )


def list_environments(projects_dir: Path, project_name: str) -> list[str]:
    project_dir = projects_dir / project_name
    if not project_dir.exists():
        return []
    return list_env_names(project_dir)


def list_requests(projects_dir: Path, project_name: str) -> list[str]:
    requests_dir = projects_dir / project_name / "requests"
    if not requests_dir.exists():
        return []
    return sorted(path.stem for path in requests_dir.glob("*.yaml"))


def load_project(
    projects_dir: Path,
    project_name: str,
    request_id: str | None = None,
    env_name: str | None = None,
    cli_vars: dict[str, str] | None = None,
) -> LoadedProject:
    project_dir = projects_dir / project_name
    if not project_dir.exists():
        raise ConfigError(f"Project not found: {project_name}")

    resolved_env = resolve_env_name(project_dir, env_name)
    variables = build_variable_context(project_dir, resolved_env, cli_vars=cli_vars)

    project_data = _load_yaml(project_dir / "project.yaml")
    if project_data.get("name") != project_name:
        project_data["name"] = project_name

    if resolved_env is not None:
        env_data = load_env_overlay(project_dir, resolved_env)
        project_data = apply_env_to_project_data(project_data, env_data)
        project_data = substitute_data(project_data, variables)

    try:
        config = ProjectConfig.model_validate(project_data)
    except Exception as exc:
        raise ConfigError(f"Invalid project config: {exc}") from exc

    requests_dir = project_dir / "requests"
    if not requests_dir.exists():
        raise ConfigError(f"Requests directory not found: {requests_dir}")

    request_files = sorted(requests_dir.glob("*.yaml"))
    if not request_files:
        raise ConfigError(f"No request definitions in {requests_dir}")

    if request_id is not None:
        request_files = [path for path in request_files if path.stem == request_id]
        if not request_files:
            available = ", ".join(path.stem for path in sorted(requests_dir.glob("*.yaml")))
            raise ConfigError(
                f"Request '{request_id}' not found in project '{project_name}'. "
                f"Available: {available}"
            )

    requests: list[RequestConfig] = []
    for request_file in request_files:
        request_data = _load_yaml(request_file)
        if "id" not in request_data:
            request_data["id"] = request_file.stem
        request_data = substitute_data(request_data, variables)
        try:
            request_config = RequestConfig.model_validate(request_data)
        except Exception as exc:
            raise ConfigError(f"Invalid request config {request_file.name}: {exc}") from exc
        requests.append(request_config)

    if request_id is not None:
        matched = [request for request in requests if request.id == request_id]
        if not matched:
            available = ", ".join(request.id for request in requests)
            raise ConfigError(
                f"Request '{request_id}' not found in project '{project_name}'. "
                f"Available: {available}"
            )
        requests = matched

    return LoadedProject(config=config, requests=requests)
