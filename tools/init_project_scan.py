# -*- coding: utf-8 -*-
# Author: dengwanpeng

"""项目初始化扫描：生成编码风格草稿、内部提取规则与接口索引。"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional


TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
_SKILL_ROOT = os.path.dirname(TOOLS_DIR)
if _SKILL_ROOT not in sys.path:
    sys.path.insert(0, _SKILL_ROOT)

from skill_utils.api_index_db import replace_index  # noqa: E402
from skill_utils.config_loader import load_config  # noqa: E402
from tools import scan_page_api  # noqa: E402


DEFAULT_RULES = {
    "version": 1,
    "generated_at": "",
    "url_extract_rules": [],
    "method_extract_rules": [],
}


def _read_text(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def _write_json(path: Path, data: Dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _render_coding_style_draft(api_template: str, case_template: str) -> str:
    api_source = _read_text(api_template)
    case_source = _read_text(case_template)
    return "\n".join(
        [
            "# 接口编码风格指南草稿",
            "",
            "> 本文件由初始化扫描生成，请人工确认后再合并到 doc/coding_style_guide.md。",
            "",
            "## 接口方法模板",
            "",
            "```python",
            api_source,
            "```",
            "",
            "## pytest 用例模板",
            "",
            "```python",
            case_source,
            "```",
            "",
        ]
    )


def _write_rules(path: Path) -> None:
    data = dict(DEFAULT_RULES)
    data["generated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    _write_json(path, data)


def init_project_scan(
    config_path: Optional[str] = None,
    api_template: Optional[str] = None,
    case_template: Optional[str] = None,
    draft_path: Optional[str] = None,
) -> Dict[str, int]:
    config = load_config(config_path)
    if not api_template or not case_template:
        raise ValueError("必须提供 api_template 和 case_template")

    draft = Path(draft_path) if draft_path else config.runtime_temp_dir / "coding_style_guide_draft.md"
    draft.parent.mkdir(parents=True, exist_ok=True)
    draft.write_text(_render_coding_style_draft(api_template, case_template), encoding="utf-8")

    _write_rules(config.extract_rules_path)
    url_rules, method_rules = scan_page_api._load_extract_rules(str(config.extract_rules_path))
    records, scanned_files = scan_page_api._scan_all(
        str(config.project_root),
        [str(path) for path in config.api_scan_dirs],
        url_rules=url_rules,
        method_rules=method_rules,
    )
    metadata = {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "repo_root": str(config.project_root).replace("\\", "/"),
        "scan_mode": "init_project_scan",
        "scanned_files": str(scanned_files),
        "total_methods": str(len(records)),
    }
    replace_index(str(config.api_index_db_path), records, metadata)
    return {"records": len(records), "scanned_files": scanned_files}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default=None, help="config.json 路径")
    parser.add_argument("--api-template", required=True, help="接口方法模板文件")
    parser.add_argument("--case-template", required=True, help="pytest 用例模板文件")
    parser.add_argument("--draft-out", default=None, help="编码风格草稿输出路径")
    args = parser.parse_args()
    result = init_project_scan(
        config_path=args.config,
        api_template=args.api_template,
        case_template=args.case_template,
        draft_path=args.draft_out,
    )
    print(f"[init_project_scan] records={result['records']} scanned_files={result['scanned_files']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
