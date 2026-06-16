import json
import sqlite3
import sys
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
if str(SKILL_ROOT) not in sys.path:
    sys.path.insert(0, str(SKILL_ROOT))


def test_append_rule_preview_then_apply_inserts_only_new_records(tmp_path):
    from skill_utils.api_index_db import replace_index
    from tools.append_extract_rule import append_extract_rule

    project = tmp_path / "project"
    api_dir = project / "api"
    api_dir.mkdir(parents=True)
    (api_dir / "custom_api.py").write_text(
        '''
class CustomApi:
    def create_custom(self):
        """创建自定义资源"""
        # Create Date: 2026-06-04
        path = "/api/custom/create"
        return self.client.request("POST", path)
'''.strip(),
        encoding="utf-8",
    )
    db_path = tmp_path / "page_api_index.sqlite3"
    replace_index(
        str(db_path),
        [
            {
                "api_url": "/api/existing",
                "api_name": "existing",
                "http_method": "GET",
                "file": "api/existing.py",
                "line": 1,
            }
        ],
    )
    rules_path = tmp_path / "api_extract_rules.json"
    rules_path.write_text(
        json.dumps({"url_extract_rules": [], "method_extract_rules": []}),
        encoding="utf-8",
    )
    rule = {
        "url_extract_rules": [
            {"name": "path_assignment", "pattern": r"\bpath\s*=\s*['\"](/api/[^'\"]+)['\"]", "group": 1}
        ],
        "method_extract_rules": [
            {"name": "client_request", "pattern": r"\.client\.request\(\s*['\"]([A-Za-z]+)['\"]", "group": 1}
        ],
    }

    preview = append_extract_rule(
        repo_root=str(project),
        scan_dirs=[str(api_dir)],
        db_path=str(db_path),
        rules_path=str(rules_path),
        rule_update=rule,
        apply=False,
    )
    with sqlite3.connect(db_path) as conn:
        assert conn.execute("SELECT COUNT(*) FROM api_methods").fetchone()[0] == 1
    assert preview["new_records"] == 1
    assert preview["records"][0]["api_url"] == "/api/custom/create"

    applied = append_extract_rule(
        repo_root=str(project),
        scan_dirs=[str(api_dir)],
        db_path=str(db_path),
        rules_path=str(rules_path),
        rule_update=rule,
        apply=True,
    )
    with sqlite3.connect(db_path) as conn:
        rows = conn.execute("SELECT api_url, method FROM api_methods ORDER BY id").fetchall()

    assert applied["inserted"] == 1
    assert rows == [("/api/existing", "GET"), ("/api/custom/create", "POST")]
