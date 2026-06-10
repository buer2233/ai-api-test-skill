# -*- coding: utf-8 -*-
# Author: dengwanpeng

"""追加项目特定接口提取规则，并按预览确认后增量写入索引。"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Dict, List


TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
_SKILL_ROOT = os.path.dirname(TOOLS_DIR)
if _SKILL_ROOT not in sys.path:
    sys.path.insert(0, _SKILL_ROOT)

from skill_utils.api_index_db import existing_url_method_pairs, insert_methods  # noqa: E402
from tools import scan_page_api  # noqa: E402


def _load_rules(path: str) -> Dict[str, List[dict]]:
    rules_path = Path(path)
    if not rules_path.is_file():
        return {"url_extract_rules": [], "method_extract_rules": []}
    try:
        data = json.loads(rules_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"url_extract_rules": [], "method_extract_rules": []}
    if not isinstance(data, dict):
        return {"url_extract_rules": [], "method_extract_rules": []}
    return {
        "url_extract_rules": list(data.get("url_extract_rules") or []),
        "method_extract_rules": list(data.get("method_extract_rules") or []),
    }


def _write_rules(path: str, rules: Dict[str, List[dict]]) -> None:
    rules_path = Path(path)
    rules_path.parent.mkdir(parents=True, exist_ok=True)
    rules_path.write_text(json.dumps(rules, ensure_ascii=False, indent=2), encoding="utf-8")


def _merge_rules(current: Dict[str, List[dict]], update: Dict[str, List[dict]]) -> Dict[str, List[dict]]:
    merged = {
        "url_extract_rules": list(current.get("url_extract_rules") or []),
        "method_extract_rules": list(current.get("method_extract_rules") or []),
    }
    for key in ("url_extract_rules", "method_extract_rules"):
        seen = {(item.get("name"), item.get("pattern")) for item in merged[key] if isinstance(item, dict)}
        for item in update.get(key) or []:
            if not isinstance(item, dict):
                continue
            marker = (item.get("name"), item.get("pattern"))
            if marker in seen:
                continue
            merged[key].append(item)
            seen.add(marker)
    return merged


def append_extract_rule(
    repo_root: str,
    scan_dirs: List[str],
    db_path: str,
    rules_path: str,
    rule_update: Dict[str, List[dict]],
    apply: bool = False,
) -> Dict:
    current_rules = _load_rules(rules_path)
    merged_rules = _merge_rules(current_rules, rule_update)
    temp_rules_path = Path(rules_path).with_suffix(".preview.json")
    _write_rules(str(temp_rules_path), merged_rules)
    try:
        url_rules, method_rules = scan_page_api._load_extract_rules(str(temp_rules_path))
        records, scanned_files = scan_page_api._scan_all(
            repo_root,
            scan_dirs,
            url_rules=url_rules,
            method_rules=method_rules,
        )
    finally:
        try:
            temp_rules_path.unlink()
        except OSError:
            pass

    existing_pairs = existing_url_method_pairs(db_path)
    new_records = scan_page_api._filter_truly_new(records, existing_pairs)
    result = {
        "scanned_files": scanned_files,
        "new_records": len(new_records),
        "records": new_records,
        "inserted": 0,
    }
    if apply:
        _write_rules(rules_path, merged_rules)
        result["inserted"] = insert_methods(db_path, new_records)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--scan-dir", action="append", required=True)
    parser.add_argument("--db", required=True)
    parser.add_argument("--rules", required=True)
    parser.add_argument("--rule-update", required=True, help="规则 JSON 文件")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    update = json.loads(Path(args.rule_update).read_text(encoding="utf-8"))
    result = append_extract_rule(
        repo_root=args.repo_root,
        scan_dirs=args.scan_dir,
        db_path=args.db,
        rules_path=args.rules,
        rule_update=update,
        apply=args.apply,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
