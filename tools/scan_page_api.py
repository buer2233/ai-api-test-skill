# -*- coding: utf-8 -*-
"""扫描 E10自动化/接口自动化测试/test_case/page_api/ 下所有 *.py，
提取 "URL 字面量 -> (方法名, 类名, 父类列表, 文件路径)" 的索引，
输出到 tools/page_api_index.json。

用法：
    python scan_page_api.py           # 增量扫描（按 mtime）
    python scan_page_api.py --full    # 全量扫描

索引结构：
    {
      "generated_at": "...",
      "pages_api_root": "...",
      "methods": [
        {
          "file": "...",
          "mtime": 1234567890,
          "class": "EBuilderPagePreviewAPI",
          "bases": ["Page_API"],
          "method": "ebPage_config_update",
          "url_literal": "https://{0}/api/bs/ebuilder/page/config/update",
          "pure_path": "/api/bs/ebuilder/page/config/update",
          "line": 123
        }
      ],
      "by_path": {
        "/api/bs/ebuilder/page/config/update": [index, index, ...]
      }
    }
"""

import argparse
import ast
import json
import os
import re
import sys
from datetime import datetime
from typing import List, Optional


TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
INDEX_PATH = os.path.join(TOOLS_DIR, "page_api_index.json")


def _find_repo_root(start: str) -> Optional[str]:
    cur = start
    for _ in range(10):
        if os.path.isdir(os.path.join(cur, "E10自动化")):
            return cur
        parent = os.path.dirname(cur)
        if parent == cur:
            return None
        cur = parent
    return None


URL_PATTERNS = [
    # "https://{0}/api/xxx".format(self.base_url)  → 捕获 /api/xxx
    re.compile(r'"https?://\{\d*\}(/[^"?\s]+)"'),
    # f"https://{self.base_url}/api/xxx"           → 捕获 /api/xxx
    re.compile(r'f"https?://\{[^"}]+\}(/[^"?\s]+)"'),
    # "https://" + self.base_url + "/api/xxx"      → 捕获 /api/xxx
    re.compile(r'"https?://"\s*\+\s*[^+]+\+\s*"(/[^"?\s]+)"'),
    # 兜底：字面 path "/api/xxx" 出现在 url 变量上下文
    re.compile(r'url\s*=\s*f?"[^"]*?(/(?:api|sapi|base|papi|ipconfigrec|tenantlogo|app)/[^"?\s]+)"'),
]


def _extract_urls_from_source(source: str):
    urls = []
    for pat in URL_PATTERNS:
        for m in pat.finditer(source):
            path = m.group(1)
            urls.append(path)
    return urls


def _parse_file(path: str):
    try:
        with open(path, "r", encoding="utf-8") as f:
            source = f.read()
    except Exception:
        return []

    try:
        tree = ast.parse(source, filename=path)
    except SyntaxError:
        return []

    results = []
    src_lines = source.splitlines()

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            cls_name = node.name
            bases = []
            for b in node.bases:
                try:
                    bases.append(ast.unparse(b))
                except Exception:
                    bases.append(getattr(b, "id", "?"))
            for sub in node.body:
                if isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    start = sub.lineno - 1
                    end = getattr(sub, "end_lineno", sub.lineno) or sub.lineno
                    body_text = "\n".join(src_lines[start:end])
                    urls = _extract_urls_from_source(body_text)
                    if not urls:
                        continue
                    # 去重保序
                    seen = set()
                    unique_urls = []
                    for u in urls:
                        if u not in seen:
                            seen.add(u)
                            unique_urls.append(u)
                    for u in unique_urls:
                        results.append({
                            "class": cls_name,
                            "bases": bases,
                            "method": sub.name,
                            "url_literal": u,  # 这里就是 pure_path
                            "pure_path": u,
                            "line": sub.lineno,
                        })
    return results


def _iter_api_files(root: str):
    for dirpath, _, filenames in os.walk(root):
        for fn in filenames:
            if fn.endswith(".py") and not fn.startswith("__"):
                yield os.path.join(dirpath, fn)


def _load_existing() -> dict:
    if os.path.isfile(INDEX_PATH):
        try:
            with open(INDEX_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--full", action="store_true", help="全量扫描，忽略 mtime 缓存")
    args = parser.parse_args()

    repo_root = _find_repo_root(TOOLS_DIR)
    if not repo_root:
        print("ERROR: 未找到仓库根（含 E10自动化）", file=sys.stderr)
        return 1

    pages_api_root = os.path.join(
        repo_root, "E10自动化", "接口自动化测试", "test_case", "page_api"
    )
    if not os.path.isdir(pages_api_root):
        print(f"ERROR: 未找到 page_api 目录 {pages_api_root}", file=sys.stderr)
        return 1

    existing = {} if args.full else _load_existing()
    # 按 file 聚合旧条目，便于增量
    old_by_file = {}
    for m in existing.get("methods", []):
        old_by_file.setdefault(m["file"], []).append(m)
    old_mtime_by_file = {f: (v[0].get("mtime", 0) if v else 0) for f, v in old_by_file.items()}

    methods: List[dict] = []
    scanned_files = 0
    reused_files = 0

    for fp in _iter_api_files(pages_api_root):
        rel = os.path.relpath(fp, repo_root).replace("\\", "/")
        try:
            mtime = int(os.path.getmtime(fp))
        except OSError:
            continue

        if (not args.full) and rel in old_by_file and old_mtime_by_file.get(rel, 0) == mtime:
            methods.extend(old_by_file[rel])
            reused_files += 1
            continue

        items = _parse_file(fp)
        scanned_files += 1
        for it in items:
            it["file"] = rel
            it["mtime"] = mtime
            methods.append(it)

    by_path = {}
    for idx, m in enumerate(methods):
        by_path.setdefault(m["pure_path"], []).append(idx)

    out = {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "repo_root": repo_root.replace("\\", "/"),
        "pages_api_root": os.path.relpath(pages_api_root, repo_root).replace("\\", "/"),
        "methods": methods,
        "by_path": by_path,
        "_stats": {
            "scanned_files": scanned_files,
            "reused_files": reused_files,
            "total_methods": len(methods),
            "unique_paths": len(by_path),
        },
    }

    with open(INDEX_PATH, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print(
        f"[scan_page_api] scanned={scanned_files} reused={reused_files} "
        f"methods={len(methods)} unique_paths={len(by_path)} → {INDEX_PATH}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
