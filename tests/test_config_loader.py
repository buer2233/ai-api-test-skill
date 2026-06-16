import json
import sys
from pathlib import Path

import pytest


SKILL_ROOT = Path(__file__).resolve().parents[1]
if str(SKILL_ROOT) not in sys.path:
    sys.path.insert(0, str(SKILL_ROOT))


def write_config(path: Path, data: dict) -> Path:
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return path


def test_load_config_requires_project_root(tmp_path):
    from skill_utils.config_loader import ConfigError, load_config

    config_path = write_config(tmp_path / "config.json", {"framework": "pytest_requests"})

    with pytest.raises(ConfigError) as exc:
        load_config(str(config_path))

    assert "project_root" in str(exc.value)


def test_load_config_resolves_project_relative_paths(tmp_path):
    from skill_utils.config_loader import load_config

    project_root = tmp_path / "demo_project"
    api_dir = project_root / "tests" / "api"
    case_dir = project_root / "tests" / "cases"
    api_dir.mkdir(parents=True)
    case_dir.mkdir(parents=True)
    config_path = write_config(
        tmp_path / "config.json",
        {
            "framework": "pytest_requests",
            "project_root": str(project_root),
            "paths": {
                "api_method_dirs": ["tests/api"],
                "test_case_dirs": ["tests/cases"],
                "pytest_workdir": "tests",
                "runtime_temp_dir": "tmp/api_skill",
            },
            "api_index": {
                "db_path": "tools/page_api_index.sqlite3",
                "scan_dirs": ["tests/api"],
                "extract_rules_path": "tools/api_extract_rules.json",
            },
            "pytest": {"pythonpath": ".", "command_template": "pytest {target} -v --tb=short"},
        },
    )

    config = load_config(str(config_path))

    assert config.project_root == project_root.resolve()
    assert config.api_method_dirs == [api_dir.resolve()]
    assert config.test_case_dirs == [case_dir.resolve()]
    assert config.pytest_workdir == (project_root / "tests").resolve()
    assert config.runtime_temp_dir == (project_root / "tmp" / "api_skill").resolve()
    assert config.api_scan_dirs == [api_dir.resolve()]
    assert config.api_index_db_path == (SKILL_ROOT / "tools" / "page_api_index.sqlite3").resolve()
    assert config.extract_rules_path == (SKILL_ROOT / "tools" / "api_extract_rules.json").resolve()


def test_load_config_rejects_missing_scan_dir(tmp_path):
    from skill_utils.config_loader import ConfigError, load_config

    project_root = tmp_path / "demo_project"
    project_root.mkdir()
    config_path = write_config(
        tmp_path / "config.json",
        {
            "project_root": str(project_root),
            "api_index": {"scan_dirs": ["missing/api"]},
        },
    )

    with pytest.raises(ConfigError) as exc:
        load_config(str(config_path))

    assert "api_index.scan_dirs" in str(exc.value)
