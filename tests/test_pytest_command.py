import json
import sys
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
if str(SKILL_ROOT) not in sys.path:
    sys.path.insert(0, str(SKILL_ROOT))


def test_build_pytest_command_from_config(tmp_path):
    from skill_utils.pytest_command import build_pytest_command

    project = tmp_path / "project"
    workdir = project / "tests"
    api_dir = project / "api"
    workdir.mkdir(parents=True)
    api_dir.mkdir()
    config_path = tmp_path / "config.json"
    config_path.write_text(
        json.dumps(
            {
                "project_root": str(project),
                "paths": {
                    "api_method_dirs": ["api"],
                    "pytest_workdir": "tests",
                },
                "api_index": {"scan_dirs": ["api"]},
                "pytest": {
                    "pythonpath": ".;../common",
                    "command_template": "pytest {target} -q --tb=short",
                },
            }
        ),
        encoding="utf-8",
    )

    command = build_pytest_command(
        target="cases/test_user.py::TestUser::test_create",
        config_path=str(config_path),
        shell="bash",
    )

    assert str(workdir.resolve()) in command
    assert "PYTHONPATH=\".;../common\"" in command
    assert "pytest cases/test_user.py::TestUser::test_create -q --tb=short" in command


def test_build_pytest_command_for_powershell(tmp_path):
    from skill_utils.pytest_command import build_pytest_command

    project = tmp_path / "project"
    workdir = project / "tests"
    api_dir = project / "api"
    workdir.mkdir(parents=True)
    api_dir.mkdir()
    config_path = tmp_path / "config.json"
    config_path.write_text(
        json.dumps(
            {
                "project_root": str(project),
                "paths": {
                    "api_method_dirs": ["api"],
                    "pytest_workdir": "tests",
                },
                "api_index": {"scan_dirs": ["api"]},
                "pytest": {
                    "pythonpath": ".;../common",
                    "command_template": "pytest {target} -q --tb=short",
                },
            }
        ),
        encoding="utf-8",
    )

    command = build_pytest_command(
        target="cases/test_user.py::TestUser::test_create",
        config_path=str(config_path),
        shell="powershell",
    )

    assert f'Set-Location -LiteralPath "{workdir.resolve()}"' in command
    assert '$env:PYTHONPATH=".;../common"' in command
    assert "pytest cases/test_user.py::TestUser::test_create -q --tb=short" in command
