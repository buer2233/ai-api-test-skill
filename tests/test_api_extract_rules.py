import json
import sys
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
if str(SKILL_ROOT) not in sys.path:
    sys.path.insert(0, str(SKILL_ROOT))


def test_load_generated_extract_rules(tmp_path):
    import tools.scan_page_api as scan_page_api

    rules_file = tmp_path / "api_extract_rules.json"
    rules_file.write_text(
        json.dumps(
            {
                "url_extract_rules": [
                    {
                        "name": "path_assignment",
                        "pattern": r"\bpath\s*=\s*['\"](/api/[^'\"]+)['\"]",
                        "group": 1,
                    }
                ],
                "method_extract_rules": [
                    {
                        "name": "client_request_method",
                        "pattern": r"\.client\.request\(\s*['\"]([A-Za-z]+)['\"]",
                        "group": 1,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    url_rules, method_rules = scan_page_api._load_extract_rules(str(rules_file))
    source = 'path = "/api/custom/create"\nreturn self.client.request("POST", path)'

    assert scan_page_api._extract_urls_from_source(source, url_rules) == ["/api/custom/create"]
    assert scan_page_api._extract_http_method(source, method_rules) == "POST"


def test_parse_file_with_generated_extract_rules(tmp_path):
    import tools.scan_page_api as scan_page_api

    api_file = tmp_path / "custom_api.py"
    api_file.write_text(
        '''
class CustomApi:
    def create_custom(self):
        """创建自定义资源"""
        # Author: tester
        # Create Date: 2026-06-02
        path = "/api/custom/create"
        return self.client.request("POST", path)
'''.strip(),
        encoding="utf-8",
    )
    url_rules = [
        {
            "name": "path_assignment",
            "pattern": scan_page_api.re.compile(r"\bpath\s*=\s*['\"](/api/[^'\"]+)['\"]"),
            "group": 1,
        }
    ]
    method_rules = [scan_page_api.re.compile(r"\.client\.request\(\s*['\"]([A-Za-z]+)['\"]")]

    records = scan_page_api._parse_file(str(api_file), url_rules=url_rules, method_rules=method_rules)

    assert len(records) == 1
    assert records[0]["api_url"] == "/api/custom/create"
    assert records[0]["http_method"] == "POST"
