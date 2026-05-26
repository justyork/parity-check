import os
import re
from pathlib import Path
from typing import Any

from parity_check.config.random_builtin import is_random_expression, resolve_random_expression
from parity_check.errors import ConfigError

_EXPR_PATTERN = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_.]*)\}")


def load_dotenv_file(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}

    variables: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("export "):
            stripped = stripped[7:].strip()
        if "=" not in stripped:
            continue
        key, _, value = stripped.partition("=")
        key = key.strip()
        value = value.strip()
        if not key:
            continue
        if (value.startswith('"') and value.endswith('"')) or (
            value.startswith("'") and value.endswith("'")
        ):
            value = value[1:-1]
        variables[key] = value
    return variables


def list_env_names(project_dir: Path) -> list[str]:
    env_dir = project_dir / "env"
    if not env_dir.exists():
        return []
    return sorted(path.stem for path in env_dir.glob("*.yaml"))


def resolve_env_name(
    project_dir: Path,
    env_name: str | None,
    env_from_os: bool = True,
) -> str | None:
    if env_name is not None:
        return env_name
    if env_from_os:
        from_os = os.environ.get("PARITY_ENV")
        if from_os:
            return from_os
    env_names = list_env_names(project_dir)
    if "dev" in env_names:
        return "dev"
    if len(env_names) == 1:
        return env_names[0]
    return None


def build_variable_context(
    project_dir: Path,
    env_name: str | None,
    cli_vars: dict[str, str] | None = None,
) -> dict[str, str]:
    """Merge variables: root .env < project .env < env vars < env .env < CLI (--var)."""
    repo_root = project_dir.parent.parent
    context: dict[str, str] = {}

    context.update(load_dotenv_file(repo_root / ".env"))
    context.update(load_dotenv_file(project_dir / ".env"))

    if env_name is not None:
        env_path = project_dir / "env" / f"{env_name}.yaml"
        if not env_path.exists():
            available = ", ".join(list_env_names(project_dir)) or "(none)"
            raise ConfigError(
                f"Environment '{env_name}' not found for project '{project_dir.name}'. "
                f"Available: {available}"
            )
        env_data = _load_env_yaml(env_path)
        context.update(env_data.get("vars") or {})

        env_dotenv = project_dir / "env" / f"{env_name}.env"
        context.update(load_dotenv_file(env_dotenv))

    if cli_vars:
        context.update(cli_vars)

    return context


def _load_env_yaml(path: Path) -> dict:
    import yaml

    with path.open(encoding="utf-8") as file:
        data = yaml.safe_load(file)
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ConfigError(f"Expected YAML mapping in {path}")
    return data


def load_env_overlay(project_dir: Path, env_name: str | None) -> dict:
    if env_name is None:
        return {}
    env_path = project_dir / "env" / f"{env_name}.yaml"
    if not env_path.exists():
        available = ", ".join(list_env_names(project_dir)) or "(none)"
        raise ConfigError(
            f"Environment '{env_name}' not found. Available: {available}"
        )
    return _load_env_yaml(env_path)


def substitute_value(
    value: Any,
    variables: dict[str, str],
    random_cache: dict[str, str] | None = None,
) -> Any:
    cache = random_cache if random_cache is not None else {}
    if isinstance(value, str):
        return _substitute_string(value, variables, cache)
    if isinstance(value, dict):
        return {
            key: substitute_value(item, variables, cache) for key, item in value.items()
        }
    if isinstance(value, list):
        return [substitute_value(item, variables, cache) for item in value]
    return value


def substitute_data(
    data: dict,
    variables: dict[str, str],
    random_cache: dict[str, str] | None = None,
) -> dict:
    return substitute_value(data, variables, random_cache)


def _substitute_string(text: str, variables: dict[str, str], random_cache: dict[str, str]) -> str:
    def replace(match: re.Match[str]) -> str:
        name = match.group(1)
        if is_random_expression(name):
            return resolve_random_expression(name, random_cache)
        if name not in variables:
            raise ConfigError(f"Undefined variable: ${{{name}}}")
        return variables[name]

    return _EXPR_PATTERN.sub(replace, text)
