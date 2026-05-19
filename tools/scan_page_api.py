# -*- coding: utf-8 -*-
# Author: dengwanpeng

"""扫描 E10自动化/接口自动化测试/test_case/page_api/ 下所有 *.py。

提取 page_api 中已覆盖接口，写入 tools/page_api_index.sqlite3。

用法：
    python scan_page_api.py           # 自动模式：空库走全量替换；非空库走增量追加
    python scan_page_api.py --full    # 强制全量替换（清空后重建，id 从 1 起）

SQLite 字段：
    api_url、api_name、api_desc、author、create_date、update_date、method

扫描规则维护：
    1. URL 抽取规则：在本文件的 URL_EXTRACT_RULES 中追加。
    2. HTTP method 抽取规则：在 REQUEST_METHOD_RULES 中追加。
    3. 跨脚本复用的基础能力请放到 utils/ 下。
"""

import argparse
import ast
import os
import re
import sys
from datetime import date, datetime, timedelta
from typing import Dict, Iterable, List, Optional, Set, Tuple


# Windows + 中文环境下，默认 stdout/stderr 走 cp936，父进程以 utf-8 捕获时会
# 触发 UnicodeDecodeError。这里统一切换到 utf-8，让 preflight_check.py 能稳定读取。
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass


TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
_SKILL_ROOT = os.path.dirname(TOOLS_DIR)
if _SKILL_ROOT not in sys.path:
    sys.path.insert(0, _SKILL_ROOT)

from utils.api_index_db import (  # noqa: E402
    existing_url_method_pairs,
    get_default_db_path,
    insert_methods,
    is_empty,
    load_metadata,
    replace_index,
)
from utils.common_function import update_skill_config  # noqa: E402
from utils.project_root import resolve_project_root  # noqa: E402


INDEX_DB_PATH = get_default_db_path(TOOLS_DIR)
SCANNER_VERSION = "2026-05-12-incremental-v1"
RECENT_DAYS = 30
APIDATA_UPDATE_FIELD = "apiDataUpdateDate"


def _warn(msg: str) -> None:
    print(f"WARN: {msg}", file=sys.stderr)


def _info(msg: str) -> None:
    print(msg)


def _resolve_repo_root() -> Optional[str]:
    return resolve_project_root(on_warn=_warn)


URL_EXTRACT_RULES = [
    {
        "name": "quoted_http_url",
        "pattern": re.compile(
            r"(?i)(?:[rubf]*)(['\"])https?://(?:\{[^'\"]+?\}|[^'\"]*?)(/[^'\"?\s]+(?:\?[^'\"]+)?)\1"
        ),
        "group": 2,
    },
    {
        "name": "concat_http_url_path",
        "pattern": re.compile(
            r"(?i)(?:[rubf]*)(['\"])https?://\1\s*\+\s*[^\n]+?\+\s*(?:[rubf]*)(['\"])(/[^'\"?\s]+(?:\?[^'\"]+)?)\2"
        ),
        "group": 3,
    },
    {
        "name": "url_assignment_path_literal",
        "pattern": re.compile(
            r"(?i)\burl\s*=\s*(?:[rubf]*)(['\"])[^'\"]*?(/(?:api|sapi|base|papi|ipconfigrec|tenantlogo|app)/[^'\"?\s]+(?:\?[^'\"]+)?)\1"
        ),
        "group": 2,
    },
]

REQUEST_METHOD_RULES = [
    # requests.request("GET", ...) / requests.request('post', ...)
    re.compile(r"requests\.request\(\s*['\"]([A-Za-z]+)['\"]"),
    # requests.get(...) / requests.post(...) / 同名快捷方法
    re.compile(r"requests\.(get|post|put|delete|patch|head|options)\(", re.IGNORECASE),
    # self.send_msg("post", url, ...) / self.xxx.send_msg('get', url, ...)
    re.compile(r"\.send_msg\(\s*['\"]([A-Za-z]+)['\"]"),
]

META_COMMENT_RE = re.compile(r"^\s*#\s*(Author|Create Date|Update Date)\s*[:：]\s*(.*?)\s*$", re.IGNORECASE)
DATE_PREFIX_RE = re.compile(r"^(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})")


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


def _parse_create_date(value: str) -> Optional[date]:
    """容错解析 Create Date 注释里的日期。"""
    raw = (value or "").strip()
    if not raw:
        return None
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            continue
    match = DATE_PREFIX_RE.match(raw)
    if match:
        try:
            return date(int(match.group(1)), int(match.group(2)), int(match.group(3)))
        except ValueError:
            return None
    return None


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


def _scan_all(repo_root: str, pages_api_root: str) -> Tuple[List[dict], int]:
    """全量扫描 page_api 目录，返回 (records, scanned_files)。"""
    records: List[dict] = []
    scanned_files = 0
    for fp in _iter_api_files(pages_api_root):
        rel = os.path.relpath(fp, repo_root).replace("\\", "/")
        try:
            mtime = int(os.path.getmtime(fp))
        except OSError:
            continue
        scanned_files += 1
        items = _parse_file(fp)
        for item in items:
            item["file"] = rel
            item["mtime"] = mtime
            records.append(item)
    return records, scanned_files


def _filter_recent(records: List[dict], days: int) -> List[dict]:
    """保留 create_date 在最近 days 天内的记录（含端点）；无日期记录被剔除。"""
    cutoff = date.today() - timedelta(days=days)
    out: List[dict] = []
    for item in records:
        parsed = _parse_create_date(item.get("create_date") or "")
        if parsed and parsed >= cutoff:
            out.append(item)
    return out


def _filter_truly_new(
    records: List[dict],
    existing_pairs: Set[Tuple[str, str]],
) -> List[dict]:
    """从 records 中剔除 DB 已存在的 (api_url, method)；同批次按 (api_url, method, file, line) 去重。"""
    batch_seen: Set[Tuple[str, str, str, int]] = set()
    new_items: List[dict] = []
    for item in records:
        api_url = (item.get("api_url") or "").strip()
        method = (item.get("http_method") or "").strip().upper()
        if not api_url:
            continue
        if (api_url, method) in existing_pairs:
            continue
        dedup_key = (api_url, method, item.get("file") or "", int(item.get("line") or 0))
        if dedup_key in batch_seen:
            continue
        batch_seen.add(dedup_key)
        new_items.append(item)
    return new_items


def _build_metadata(
    repo_root: str,
    pages_api_root: str,
    scanned_files: int,
    total_methods: int,
    unique_paths: int,
    mode: str,
) -> Dict[str, str]:
    return {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "repo_root": repo_root.replace("\\", "/"),
        "pages_api_root": os.path.relpath(pages_api_root, repo_root).replace("\\", "/"),
        "scanner_version": SCANNER_VERSION,
        "scanned_files": str(scanned_files),
        "total_methods": str(total_methods),
        "unique_paths": str(unique_paths),
        "scan_mode": mode,
    }


def _print_new_method_summary(new_items: List[dict]) -> None:
    """以 preflight 可解析的稳定前缀打印新增接口名称。"""
    count = len(new_items)
    print(f"[scan_page_api] recent_new_methods_count={count}")
    if not count:
        return
    print("[scan_page_api] recent_new_methods:")
    for item in new_items:
        api_name = item.get("api_name") or item.get("method") or ""
        api_url = item.get("api_url") or ""
        http_method = (item.get("http_method") or "").upper() or "-"
        print(f"  - {http_method} {api_url} :: {api_name}")


def _update_apidata_date(db_path: str) -> None:
    today_str = date.today().strftime("%Y-%m-%d")
    ok = update_skill_config(
        {APIDATA_UPDATE_FIELD: today_str},
        on_warn=_warn,
        on_info=_info,
    )
    if not ok:
        _warn(f"未能写入 {APIDATA_UPDATE_FIELD}={today_str} 到 config.json")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--full",
        action="store_true",
        help="强制全量替换，忽略增量模式；用于库内 ID 不连续/字段升级等场景",
    )
    parser.add_argument("--db", default=INDEX_DB_PATH, help="SQLite 索引路径（默认 tools/page_api_index.sqlite3）")
    args = parser.parse_args()

    repo_root = _resolve_repo_root()
    if not repo_root:
        print(
            "ERROR: 未找到仓库根（含 E10自动化 目录），请确认当前工作目录在 test-automation 项目内，"
            "或在 skill 根目录 config.json 中配置 project_path",
            file=sys.stderr,
        )
        return 1

    pages_api_root = os.path.join(
        repo_root, "E10自动化", "接口自动化测试", "test_case", "page_api"
    )
    if not os.path.isdir(pages_api_root):
        print(f"ERROR: 未找到 page_api 目录 {pages_api_root}", file=sys.stderr)
        return 1

    force_full = args.full or is_empty(args.db)
    all_records, scanned_files = _scan_all(repo_root, pages_api_root)

    if force_full:
        unique_paths = len({item.get("api_url") for item in all_records if item.get("api_url")})
        metadata = _build_metadata(
            repo_root, pages_api_root, scanned_files, len(all_records), unique_paths,
            mode="full",
        )
        replace_index(args.db, all_records, metadata)
        # 全量模式视所有写入为本次写入；新增列表为空（无前置基线）
        _print_new_method_summary([])
        _update_apidata_date(args.db)
        print(
            f"[scan_page_api] mode=full scanned={scanned_files} "
            f"methods={len(all_records)} unique_paths={unique_paths} → {args.db}"
        )
        return 0

    # 增量模式：扫描完整 → 取近 N 天 → 与 DB diff → 仅 INSERT 新接口
    existing_pairs = existing_url_method_pairs(args.db)
    recent_records = _filter_recent(all_records, RECENT_DAYS)
    new_items = _filter_truly_new(recent_records, existing_pairs)

    metadata = _build_metadata(
        repo_root,
        pages_api_root,
        scanned_files,
        total_methods=len(all_records),
        unique_paths=len({item.get("api_url") for item in all_records if item.get("api_url")}),
        mode="incremental",
    )
    inserted = insert_methods(args.db, new_items, metadata)
    _print_new_method_summary(new_items)
    _update_apidata_date(args.db)
    print(
        f"[scan_page_api] mode=incremental scanned={scanned_files} "
        f"recent={len(recent_records)} new_inserted={inserted} → {args.db}"
    )
    # silence unused metadata warning in older python
    _ = load_metadata
    return 0


if __name__ == "__main__":
    sys.exit(main())
