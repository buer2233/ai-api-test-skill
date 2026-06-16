import json
import sqlite3
import sys
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
if str(SKILL_ROOT) not in sys.path:
    sys.path.insert(0, str(SKILL_ROOT))


def test_init_project_scan_generates_draft_rules_and_index(tmp_path):
    from tools.init_project_scan import init_project_scan

    project = tmp_path / "project"
    api_dir = project / "api"
    case_dir = project / "cases"
    api_dir.mkdir(parents=True)
    case_dir.mkdir(parents=True)
    api_template = api_dir / "user_api.py"
    case_template = case_dir / "test_user.py"
    api_template.write_text(
        '''
import requests


class UserApi:
    def create_user(self):
        """创建用户"""
        # Author: tester
        # Create Date: 2026-06-03
        url = "https://example.com/api/users/create"
        return requests.post(url, json={})
'''.strip(),
        encoding="utf-8",
    )
    case_template.write_text(
        '''
class TestUser:
    def test_create_user(self):
        """创建用户成功"""
        assert True
'''.strip(),
        encoding="utf-8",
    )
    db_path = tmp_path / "page_api_index.sqlite3"
    rules_path = tmp_path / "api_extract_rules.json"
    draft_path = tmp_path / "coding_style_guide_draft.md"
    config_path = tmp_path / "config.json"
    config_path.write_text(
        json.dumps(
            {
                "project_root": str(project),
                "paths": {
                    "api_method_dirs": ["api"],
                    "test_case_dirs": ["cases"],
                    "pytest_workdir": ".",
                    "runtime_temp_dir": "tmp",
                },
                "api_index": {
                    "db_path": str(db_path),
                    "scan_dirs": ["api"],
                    "extract_rules_path": str(rules_path),
                },
            }
        ),
        encoding="utf-8",
    )

    result = init_project_scan(
        config_path=str(config_path),
        api_template=str(api_template),
        case_template=str(case_template),
        draft_path=str(draft_path),
    )

    assert result["records"] == 1
    assert draft_path.read_text(encoding="utf-8").startswith("# 接口编码风格指南草稿")
    rules_data = json.loads(rules_path.read_text(encoding="utf-8"))
    assert "url_extract_rules" in rules_data
    assert "method_extract_rules" in rules_data
    with sqlite3.connect(db_path) as conn:
        rows = conn.execute("SELECT api_url, method, api_name FROM api_methods").fetchall()
    assert rows == [("/api/users/create", "POST", "create_user")]
