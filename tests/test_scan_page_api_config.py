import json
import sys
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
if str(SKILL_ROOT) not in sys.path:
    sys.path.insert(0, str(SKILL_ROOT))


def test_scan_all_configured_api_dirs(tmp_path):
    import tools.scan_page_api as scan_page_api

    project = tmp_path / "project"
    api_dir = project / "src" / "clients"
    api_dir.mkdir(parents=True)
    api_file = api_dir / "user_api.py"
    api_file.write_text(
        '''
import requests


class UserApi:
    def create_user(self):
        """创建用户"""
        # Author: tester
        # Create Date: 2026-06-01
        url = f"https://{self.base_url}/api/users/create"
        return requests.post(url, json={})
'''.strip(),
        encoding="utf-8",
    )

    records, scanned_files = scan_page_api._scan_all(str(project), [str(api_dir)])

    assert scanned_files == 1
    assert len(records) == 1
    assert records[0]["api_url"] == "/api/users/create"
    assert records[0]["http_method"] == "POST"
    assert records[0]["file"] == "src/clients/user_api.py"


def test_scan_dirs_from_config(tmp_path, monkeypatch):
    import skill_utils.config_loader as config_loader
    import tools.scan_page_api as scan_page_api

    project = tmp_path / "project"
    api_dir = project / "custom_api"
    api_dir.mkdir(parents=True)
    (api_dir / "order_api.py").write_text(
        '''
import requests


class OrderApi:
    def list_orders(self):
        """查询订单"""
        # Create Date: 2026-06-01
        url = "https://example.com/api/orders/list"
        return requests.get(url)
'''.strip(),
        encoding="utf-8",
    )
    config_path = tmp_path / "config.json"
    config_path.write_text(
        json.dumps(
            {
                "project_root": str(project),
                "paths": {"api_method_dirs": ["custom_api"], "pytest_workdir": "."},
                "api_index": {"scan_dirs": ["custom_api"]},
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(config_loader, "DEFAULT_CONFIG_PATH", config_path)

    repo_root, scan_dirs = scan_page_api._resolve_scan_roots()
    records, scanned_files = scan_page_api._scan_all(repo_root, scan_dirs)

    assert repo_root == str(project.resolve())
    assert scan_dirs == [str(api_dir.resolve())]
    assert scanned_files == 1
    assert records[0]["api_url"] == "/api/orders/list"


def test_scan_self_http_shortcut_method(tmp_path):
    import tools.scan_page_api as scan_page_api

    api_file = tmp_path / "gbif_api.py"
    api_file.write_text(
        '''
class GbifAPI:
    def species_search(self, status_code=200, **kwargs):
        """按关键词搜索物种"""
        # Create Date: 2026-06-10
        url = "/api/species/search"
        payload = {}
        payload.update(kwargs)
        return self.get(url, status_code=status_code, params=payload)
'''.strip(),
        encoding="utf-8",
    )

    records = scan_page_api._parse_file(str(api_file))

    assert len(records) == 1
    assert records[0]["api_url"] == "/api/species/search"
    assert records[0]["http_method"] == "GET"
