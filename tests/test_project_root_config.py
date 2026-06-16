import json
import sys
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
if str(SKILL_ROOT) not in sys.path:
    sys.path.insert(0, str(SKILL_ROOT))


def test_resolve_project_root_uses_config_project_root(tmp_path, monkeypatch):
    import skill_utils.config_loader as config_loader
    import skill_utils.project_root as project_root

    project = tmp_path / "generic_pytest_project"
    api_dir = project / "api"
    api_dir.mkdir(parents=True)
    config_path = tmp_path / "config.json"
    config_path.write_text(
        json.dumps(
            {
                "project_root": str(project),
                "paths": {"api_method_dirs": ["api"], "pytest_workdir": "."},
                "api_index": {"scan_dirs": ["api"]},
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(config_loader, "DEFAULT_CONFIG_PATH", config_path)

    assert project_root.resolve_project_root() == str(project.resolve())


def test_resolve_project_root_does_not_fallback_to_e10_marker(tmp_path, monkeypatch):
    import skill_utils.config_loader as config_loader
    import skill_utils.project_root as project_root

    fallback_like_project = tmp_path / "fallback_like_project"
    (fallback_like_project / "E10自动化").mkdir(parents=True)
    config_path = tmp_path / "config.json"
    config_path.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(config_loader, "DEFAULT_CONFIG_PATH", config_path)
    warnings = []

    assert project_root.resolve_project_root(on_warn=warnings.append) is None
    assert any("project_root" in msg for msg in warnings)
