from pathlib import Path

import pytest

from parity_check.config.loader import list_projects, list_requests, load_project
from parity_check.errors import ConfigError

PROJECTS_DIR = Path(__file__).resolve().parent.parent / "projects"


def test_list_projects():
    projects = list_projects(PROJECTS_DIR)
    assert "example" in projects


def test_list_requests():
    requests = list_requests(PROJECTS_DIR, "example")
    assert "get-health" in requests


def test_load_project_all_requests():
    loaded = load_project(PROJECTS_DIR, "example")
    assert loaded.config.name == "example"
    assert len(loaded.requests) >= 1


def test_load_project_single_request():
    loaded = load_project(PROJECTS_DIR, "example", request_id="get-health")
    assert len(loaded.requests) == 1
    assert loaded.requests[0].id == "get-health"


def test_load_project_missing_request():
    with pytest.raises(ConfigError, match="not found"):
        load_project(PROJECTS_DIR, "example", request_id="missing")
