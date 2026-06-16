import json
import importlib
import sys
import types
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
if str(SKILL_ROOT) not in sys.path:
    sys.path.insert(0, str(SKILL_ROOT))


def test_match_captures_temp_dir_uses_config(tmp_path, monkeypatch):
    import skill_utils.config_loader as config_loader
    import tools.match_captures as match_captures

    project = tmp_path / "project"
    api_dir = project / "api"
    api_dir.mkdir(parents=True)
    config_path = tmp_path / "config.json"
    config_path.write_text(
        json.dumps(
            {
                "project_root": str(project),
                "paths": {
                    "api_method_dirs": ["api"],
                    "pytest_workdir": ".",
                    "runtime_temp_dir": "runtime/api_temp",
                },
                "api_index": {"scan_dirs": ["api"]},
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(config_loader, "DEFAULT_CONFIG_PATH", config_path)

    temp_dir = match_captures._get_temp_dir()

    assert temp_dir == str((project / "runtime" / "api_temp").resolve())
    assert Path(temp_dir).is_dir()


def test_capture_addon_loads_baseurl_from_config(tmp_path, monkeypatch):
    import skill_utils.config_loader as config_loader

    project = tmp_path / "project"
    api_dir = project / "api"
    api_dir.mkdir(parents=True)
    config_path = tmp_path / "config.json"
    config_path.write_text(
        json.dumps(
            {
                "project_root": str(project),
                "baseurl": "api.example.test",
                "paths": {
                    "api_method_dirs": ["api"],
                    "pytest_workdir": ".",
                    "runtime_temp_dir": "runtime",
                },
                "api_index": {"scan_dirs": ["api"]},
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(config_loader, "DEFAULT_CONFIG_PATH", config_path)

    fake_log = types.SimpleNamespace(warn=lambda _msg: None, info=lambda _msg: None)
    fake_mitmproxy = types.SimpleNamespace(
        ctx=types.SimpleNamespace(log=fake_log),
        http=types.SimpleNamespace(HTTPFlow=object),
    )
    monkeypatch.setitem(sys.modules, "mitmproxy", fake_mitmproxy)
    monkeypatch.setitem(sys.modules, "mitmproxy.ctx", fake_mitmproxy.ctx)
    monkeypatch.setitem(sys.modules, "mitmproxy.http", fake_mitmproxy.http)
    sys.modules.pop("capture.capture_addon", None)

    capture_addon = importlib.import_module("capture.capture_addon")

    assert capture_addon._load_baseurl() == "api.example.test"
