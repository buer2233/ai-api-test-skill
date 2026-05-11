# -*- coding: utf-8 -*-
# Author: dengwanpeng

"""扫描 E10自动化/接口自动化测试/test_case/page_api/ 下所有 *.py。

提取 page_api 中已覆盖接口，写入 tools/page_api_index.sqlite3。

用法：
    python scan_page_api.py           # 增量扫描（按 mtime + 扫描器版本）
    python scan_page_api.py --full    # 全量扫描

SQLite 字段：
    api_url、api_name、api_desc、author、create_date、update_date、method

扩展扫描规则：
    1. 优先在本文件的 URL_EXTRACT_RULES 中追加正则规则。
    2. 若需要跨脚本复用的基础能力，请放到 utils/ 下。
"""

import argparse
import ast
import os
import re
import sys
from datetime import datetime
from typing import Dict, Iterable, List, Optional


TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
_SKILL_ROOT = os.path.dirname(TOOLS_DIR)
if _SKILL_ROOT not in sys.path:
    sys.path.insert(0, _SKILL_ROOT)

from utils.api_index_db import (  # noqa: E402
    get_default_db_path,
    load_metadata,
    load_methods,
    replace_index,
)
from utils.project_root import resolve_project_root  # noqa: E402


INDEX_DB_PATH = get_default_db_path(TOOLS_DIR)
SCANNER_VERSION = "2026-05-11-url-rule-v2"


def _warn(msg: str) -> None:
    print(f"WARN: {msg}", file=sys.stderr)


def _resolve_repo_root() -> Optional[str]:
    return resolve_project_root(on_warn=_warn)


URL_EXTRACT_RULES = [
    {
        "name": "quoted_http_url",
        "pattern": re.compile(
            r"(?i)(?:[rubf]*)(['\"])https?://(?:\{[^'\"]+?\}|[^'\"]*?)(/[^'\"?\s]+)\1"
        ),
        "group": 2,
    },
    {
        "name": "concat_http_url_path",
        "pattern": re.compile(
            r"(?i)(?:[rubf]*)(['\"])https?://\1\s*\+\s*[^\n]+?\+\s*(?:[rubf]*)(['\"])(/[^'\"?\s]+)\2"
        ),
        "group": 3,
    },
    {
        "name": "url_assignment_path_literal",
        "pattern": re.compile(
            r"(?i)\burl\s*=\s*(?:[rubf]*)(['\"])[^'\"]*?(/(?:api|sapi|base|papi|ipconfigrec|tenantlogo|app)/[^'\"?\s]+)\1"
        ),
        "group": 2,
    },
]

REQUEST_METHOD_RULES = [
    re.compile(r"requests\.request\(\s*['\"]([A-Za-z]+)['\"]"),
    re.compile(r"requests\.(get|post|put|delete|patch|head|options)\(", re.IGNORECASE),
]

META_COMMENT_RE = re.compile(r"^\s*#\s*(Author|Create Date|Update Date)\s*[:：]\s*(.*?)\s*$", re.IGNORECASE)


def _extract_urls_from_source(source: str) -> List[str]:
    urls: List[str] = []
    for rule in URL_EXTRACT_RULES:
        for match in rule["pattern"].finditer(source):
            urls.append(_clean_url_path(match.group(rule["group"])))
    return [url for url in urls if url]


def _clean_url_path(path: str) -> str:
    value = (path or "").strip().strip("'\"")
    if not value:
        return ""
    value = value.split("?", 1)[0]
    if not value.startswith("/"):
        value = "/" + value
    return value.rstrip("/") or "/"


def _unique_keep_order(values: Iterable[str]) -> List[str]:
    seen = set()
    result = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            result.append(value)
    return result


def _get_bases(node: ast.ClassDef) -> List[str]:
    bases = []
    for base in node.bases:
        try:
            bases.append(ast.unparse(base))
        except Exception:
            bases.append(getattr(base, "id", "?"))
    return bases


def _extract_doc_desc(func: ast.AST) -> str:
    doc = ast.get_docstring(func) or ""
    if not doc:
        return ""
    lines = [line.strip() for line in doc.splitlines() if line.strip()]
    for line in lines:
        match = re.match(r"^(?:desc|description|描述)\s*[:：]\s*(.+)$", line, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    for line in lines:
        if line.startswith(":") or line.startswith("@"):
            continue
        return line
    return ""


def _extract_comment_meta(body_text: str) -> Dict[str, str]:
    meta = {"author": "", "create_date": "", "update_date": ""}
    key_map = {
        "author": "author",
        "create date": "create_date",
        "update date": "update_date",
    }
    for line in body_text.splitlines():
        match = META_COMMENT_RE.match(line)
        if not match:
            continue
        key = key_map.get(match.group(1).lower())
        if key:
            meta[key] = match.group(2).strip()
    return meta


def _extract_http_method(body_text: str) -> str:
    for rule in REQUEST_METHOD_RULES:
        match = rule.search(body_text)
        if match:
            return match.group(1).upper()
    return ""


def _parse_file(path: str) -> List[dict]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            source = f.read()
    except Exception:
        return []

    try:
        tree = ast.parse(source, filename=path)
    except SyntaxError:
        return []

    results: List[dict] = []
    src_lines = source.splitlines()

    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        cls_name = node.name
        bases = _get_bases(node)
        for sub in node.body:
            if not isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            start = sub.lineno - 1
            end = getattr(sub, "end_lineno", sub.lineno) or sub.lineno
            body_text = "\n".join(src_lines[start:end])
            urls = _unique_keep_order(_extract_urls_from_source(body_text))
            if not urls:
                continue
            meta = _extract_comment_meta(body_text)
            api_desc = _extract_doc_desc(sub)
            http_method = _extract_http_method(body_text)
            for url in urls:
                results.append({
                    "class": cls_name,
                    "bases": bases,
                    "method": sub.name,
                    "api_name": sub.name,
                    "api_desc": api_desc,
                    "author": meta["author"],
                    "create_date": meta["create_date"],
                    "update_date": meta["update_date"],
                    "http_method": http_method,
                    "url_literal": url,
                    "pure_path": url,
                    "api_url": url,
                    "line": sub.lineno,
                })
    return results


def _iter_api_files(root: str):
    for dirpath, _, filenames in os.walk(root):
        for filename in filenames:
            if filename.endswith(".py") and not filename.startswith("__"):
                yield os.path.join(dirpath, filename)


def _old_records_by_file(db_path: str) -> Dict[str, List[dict]]:
    old_by_file: Dict[str, List[dict]] = {}
    for item in load_methods(db_path):
        if item.get("file"):
            old_by_file.setdefault(item["file"], []).append(item)
    return old_by_file


def _should_reuse_file(args_full: bool, metadata: dict, rel_path: str, mtime: int, old_by_file: dict) -> bool:
    if args_full:
        return False
    if metadata.get("scanner_version") != SCANNER_VERSION:
        return False
    if rel_path not in old_by_file:
        return False
    old_items = old_by_file.get(rel_path) or []
    return bool(old_items) and int(old_items[0].get("mtime") or 0) == mtime


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--full", action="store_true", help="全量扫描，忽略 mtime 缓存")
    parser.add_argument("--db", default=INDEX_DB_PATH, help="SQLite 索引路径（默认 tools/page_api_index.sqlite3）")
    args = parser.parse_args()

    repo_root = _resolve_repo_root()
    if not repo_root:
        print("ERROR: 未找到仓库根（含 E10自动化 目录），请确认当前工作目录在 test-automation 项目内，或在 skill 根目录 config.json 中配置 project_path", file=sys.stderr)
        return 1

    pages_api_root = os.path.join(
        repo_root, "E10自动化", "接口自动化测试", "test_case", "page_api"
    )
    if not os.path.isdir(pages_api_root):
        print(f"ERROR: 未找到 page_api 目录 {pages_api_root}", file=sys.stderr)
        return 1

    metadata = load_metadata(args.db)
    old_by_file = {} if args.full else _old_records_by_file(args.db)

    methods: List[dict] = []
    scanned_files = 0
    reused_files = 0

    for fp in _iter_api_files(pages_api_root):
        rel = os.path.relpath(fp, repo_root).replace("\\", "/")
        try:
            mtime = int(os.path.getmtime(fp))
        except OSError:
            continue

        if _should_reuse_file(args.full, metadata, rel, mtime, old_by_file):
            methods.extend(old_by_file[rel])
            reused_files += 1
            continue

        items = _parse_file(fp)
        scanned_files += 1
        for item in items:
            item["file"] = rel
            item["mtime"] = mtime
            methods.append(item)

    unique_paths = len({item.get("api_url") or item.get("pure_path") for item in methods})
    replace_index(
        args.db,
        methods,
        {
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "repo_root": repo_root.replace("\\", "/"),
            "pages_api_root": os.path.relpath(pages_api_root, repo_root).replace("\\", "/"),
            "scanner_version": SCANNER_VERSION,
            "scanned_files": scanned_files,
            "reused_files": reused_files,
            "total_methods": len(methods),
            "unique_paths": unique_paths,
        },
    )

    print(
        f"[scan_page_api] scanned={scanned_files} reused={reused_files} "
        f"methods={len(methods)} unique_paths={unique_paths} → {args.db}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
