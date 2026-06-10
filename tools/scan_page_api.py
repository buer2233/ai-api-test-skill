# -*- coding: utf-8 -*-
# Author: dengwanpeng

"""扫描 config.json 中 api_index.scan_dirs 下所有 *.py。

提取已覆盖接口，写入 tools/page_api_index.sqlite3。

用法：
    python scan_page_api.py           # 自动模式：空库走全量替换；非空库走增量追加
    python scan_page_api.py --full    # 强制全量替换（清空后重建，id 从 1 起）

SQLite 字段：
    api_url、api_name、api_desc、author、create_date、update_date、method

扫描规则维护：
    1. 内置 URL 抽取规则在 URL_EXTRACT_RULES。
    2. 内置 HTTP method 抽取规则在 REQUEST_METHOD_RULES。
    3. 项目特定规则由初始化扫描生成到 tools/api_extract_rules.json。
    4. 跨脚本复用的基础能力请放到 skill_utils/ 下。
"""

import argparse
import ast
import json
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

from skill_utils.api_index_db import (  # noqa: E402
    existing_url_method_pairs,
    get_default_db_path,
    insert_methods,
    is_empty,
    load_metadata,
    replace_index,
)
from skill_utils.common_function import update_skill_config  # noqa: E402
from skill_utils.config_loader import ConfigError, load_config  # noqa: E402
from skill_utils.project_root import resolve_project_root  # noqa: E402


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


def _resolve_scan_roots() -> Tuple[Optional[str], List[str]]:
    try:
        config = load_config()
    except ConfigError as exc:
        _warn(f"读取扫描配置失败: {exc}")
        return None, []
    return str(config.project_root), [str(path) for path in config.api_scan_dirs]


def _resolve_extract_rules_path() -> Optional[str]:
    try:
        config = load_config()
    except ConfigError as exc:
        _warn(f"读取提取规则配置失败: {exc}")
        return None
    return str(config.extract_rules_path)


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
    {
        "name": "url_assignment_format_path_bare_query",
        "pattern": re.compile(
            r"(?i)\burl\s*=\s*(?:[rubf]*)(['\"])[^'\"]*?(/(?:api|sapi|base|papi|ipconfigrec|tenantlogo|app)/[^'\"?\s]+)\?\1\s*\.format\("
        ),
        "group": 2,
    },
]

REQUEST_METHOD_RULES = [
    # requests.request("GET", ...) / requests.request('post', ...)
    re.compile(r"requests\.request\(\s*['\"]([A-Za-z]+)['\"]"),
    # requests.get(...) / requests.post(...) / 同名快捷方法
    re.compile(r"requests\.(get|post|put|delete|patch|head|options)\(", re.IGNORECASE),
    # BaseAPI 封装常见写法：self.get(url, ...) / self.post(url, ...)
    re.compile(r"\bself\.(get|post|put|delete|patch|head|options)\(", re.IGNORECASE),
    # BaseAPI 通用写法：self.request("GET", url, ...)
    re.compile(r"\bself\.request\(\s*['\"]([A-Za-z]+)['\"]", re.IGNORECASE),
    # self.send_msg("post", url, ...) / self.xxx.send_msg('get', url, ...)
    re.compile(r"\.send_msg\(\s*['\"]([A-Za-z]+)['\"]"),
]

META_COMMENT_RE = re.compile(r"^\s*#\s*(Author|Create Date|Update Date)\s*[:：]\s*(.*?)\s*$", re.IGNORECASE)
DATE_PREFIX_RE = re.compile(r"^(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})")


def _compile_rule(rule: dict) -> Optional[dict]:
    try:
        compiled = re.compile(rule["pattern"], re.IGNORECASE if rule.get("ignore_case", True) else 0)
    except Exception as exc:
        _warn(f"提取规则编译失败 {rule.get('name') or '<unnamed>'}: {exc}")
        return None
    return {
        "name": rule.get("name") or "generated_rule",
        "pattern": compiled,
        "group": int(rule.get("group") or 1),
    }


def _load_extract_rules(rules_path: Optional[str] = None):
    url_rules = list(URL_EXTRACT_RULES)
    method_rules = list(REQUEST_METHOD_RULES)
    if not rules_path or not os.path.isfile(rules_path):
        return url_rules, method_rules
    try:
        with open(rules_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as exc:
        _warn(f"读取接口提取规则失败: {exc}")
        return url_rules, method_rules
    if not isinstance(data, dict):
        _warn("接口提取规则文件顶层必须是对象，已忽略")
        return url_rules, method_rules
    for rule in data.get("url_extract_rules") or []:
        if not isinstance(rule, dict):
            continue
        compiled = _compile_rule(rule)
        if compiled:
            url_rules.append(compiled)
    for rule in data.get("method_extract_rules") or []:
        if not isinstance(rule, dict):
            continue
        compiled = _compile_rule(rule)
        if compiled:
            method_rules.append(compiled["pattern"])
    return url_rules, method_rules


def _extract_urls_from_source(source: str, url_rules=None) -> List[str]:
    urls: List[str] = []
    for rule in url_rules or URL_EXTRACT_RULES:
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


def _extract_http_method(body_text: str, method_rules=None) -> str:
    for rule in method_rules or REQUEST_METHOD_RULES:
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


def _parse_file(path: str, url_rules=None, method_rules=None) -> List[dict]:
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
            urls = _unique_keep_order(_extract_urls_from_source(body_text, url_rules=url_rules))
            if not urls:
                continue
            meta = _extract_comment_meta(body_text)
            api_desc = _extract_doc_desc(sub)
            http_method = _extract_http_method(body_text, method_rules=method_rules)
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


def _scan_all(repo_root: str, pages_api_root, url_rules=None, method_rules=None) -> Tuple[List[dict], int]:
    """全量扫描配置的 API 目录，返回 (records, scanned_files)。"""
    records: List[dict] = []
    scanned_files = 0
    roots = pages_api_root if isinstance(pages_api_root, (list, tuple)) else [pages_api_root]
    for root in roots:
        for fp in _iter_api_files(root):
            rel = os.path.relpath(fp, repo_root).replace("\\", "/")
            try:
                mtime = int(os.path.getmtime(fp))
            except OSError:
                continue
            scanned_files += 1
            items = _parse_file(fp, url_rules=url_rules, method_rules=method_rules)
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
    pages_api_root,
    scanned_files: int,
    total_methods: int,
    unique_paths: int,
    mode: str,
) -> Dict[str, str]:
    return {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "repo_root": repo_root.replace("\\", "/"),
        "pages_api_root": ";".join(
            os.path.relpath(path, repo_root).replace("\\", "/")
            for path in (pages_api_root if isinstance(pages_api_root, (list, tuple)) else [pages_api_root])
        ),
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

    repo_root, pages_api_roots = _resolve_scan_roots()
    if not repo_root:
        print(
            "ERROR: 未找到项目根。请先在 config.json 中配置 project_root 与 api_index.scan_dirs。",
            file=sys.stderr,
        )
        return 1

    missing_scan_roots = [path for path in pages_api_roots if not os.path.isdir(path)]
    if missing_scan_roots:
        print(f"ERROR: 未找到 API 扫描目录 {missing_scan_roots}", file=sys.stderr)
        return 1

    force_full = args.full or is_empty(args.db)
    url_rules, method_rules = _load_extract_rules(_resolve_extract_rules_path())
    all_records, scanned_files = _scan_all(
        repo_root,
        pages_api_roots,
        url_rules=url_rules,
        method_rules=method_rules,
    )

    if force_full:
        unique_paths = len({item.get("api_url") for item in all_records if item.get("api_url")})
        metadata = _build_metadata(
            repo_root, pages_api_roots, scanned_files, len(all_records), unique_paths,
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
        pages_api_roots,
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
