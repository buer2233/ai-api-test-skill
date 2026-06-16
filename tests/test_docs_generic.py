from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_skill_scope_is_generic_pytest_requests():
    text = read("SKILL.md")

    assert "\\test-automation\\E10自动化\\接口自动化测试" not in text
    assert "当任务涉及在 `E10自动化/接口自动化测试/` 内" not in text
    assert "面向 `python + pytest + requests`" in text


def test_pytest_workdir_docs_are_config_driven():
    core = read("doc/core_principles.md")
    maintenance = read("doc/mode_maintenance_pytest_driven.md")

    assert "\\test-automation\\E10自动化\\接口自动化测试\\test_case" not in core
    assert "<project>/E10自动化/接口自动化测试/test_case" not in maintenance
    assert "config.json" in core
    assert "pytest.command_template" in maintenance


def test_preflight_docs_do_not_require_e10_marker():
    new_gate = read("doc/preflight_gates_new.md")
    maintenance_gate = read("doc/preflight_gates_maintenance.md")

    assert "项目根由 `skill_utils/project_root.py` 直接从 skill 自身位置推导" not in new_gate
    assert "项目根由 `skill_utils/project_root.py` 直接从 skill 自身位置推导" not in maintenance_gate
    assert "E10自动化` 子目录" not in new_gate
    assert "E10自动化` 子目录" not in maintenance_gate
