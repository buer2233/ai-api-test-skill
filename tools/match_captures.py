# -*- coding: utf-8 -*-
# Author: dengwanpeng

r"""读取 api_test_dwp_temp/latest.jsonl + tools/page_api_index.sqlite3（全局），
生成 api_test_dwp_temp/capture_selection.md 草稿供用户勾选。

用法：
    python match_captures.py
    python match_captures.py --jsonl path\to\latest.jsonl

草稿结构：
    ## 使用说明
    ## 需要加入用例的接口（请勾选）
        - [x] / [ ] 条目（新接口默认勾上，已实现默认不勾）
    ## 特殊处理接口（二进制/文件响应，请手动处理）
    ## 已自动忽略的登录/登出接口
"""

import argparse
import json
import os
import sys
from collections import OrderedDict
from datetime import datetime
from typing import List, Optional


TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
_SKILL_ROOT = os.path.dirname(TOOLS_DIR)
if _SKILL_ROOT not in sys.path:
    sys.path.insert(0, _SKILL_ROOT)

from skill_utils.project_root import (  # noqa: E402
    resolve_project_root,
    get_temp_dir,
)
from skill_utils.api_index_db import get_default_db_path, load_methods  # noqa: E402
from skill_utils.api_path_match import api_path_matches  # noqa: E402


INDEX_DB_PATH = get_default_db_path(TOOLS_DIR)


def _warn(msg: str) -> None:
    print(f"WARN: {msg}", file=sys.stderr)


def _resolve_repo_root() -> Optional[str]:
    return resolve_project_root(on_warn=_warn)


def _get_temp_dir() -> str:
    """返回 api_test_dwp_temp 目录路径；定位失败时打印 ERROR 并返回 ""。"""
    temp_dir = get_temp_dir(on_warn=_warn)
    if not temp_dir:
        print(
            "ERROR: 未找到项目根（含 E10自动化 目录）。请确认 skill 安装在 <project>/.claude/skills/api-test-E10/ 路径下。",
            file=sys.stderr,
        )
        return ""
    return temp_dir


def _load_jsonl(path: str) -> List[dict]:
    if not os.path.isfile(path):
        return []
    records = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip().lstrip("\ufeff")
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return records


def _dedup_by_method_path(records: List[dict]) -> List[dict]:
    """同 method+pure_path 仅保留一条（取最后一次，含响应）。"""
    bucket = OrderedDict()
    for r in records:
        key = (r.get("method", ""), r.get("pure_path", ""))
        bucket[key] = r
    return list(bucket.values())


def _display_path(path: str, repo_root: str) -> str:
    try:
        return os.path.relpath(path, repo_root).replace(os.sep, "/")
    except ValueError:
        return path.replace(os.sep, "/")


def _find_impl(index: dict, pure_path: str):
    methods = index.get("methods", [])
    captured_method = (index.get("current_method") or "").upper()
    matched = []
    for item in methods:
        covered_method = (item.get("http_method") or item.get("method") or "").upper()
        if covered_method and captured_method and covered_method != captured_method:
            continue
        if api_path_matches(item.get("api_url") or item.get("pure_path") or "", pure_path):
            matched.append(item)
    return matched


def _normalize_path_for_index(pure_path: str, repo_baseurl_tail: str = "") -> List[str]:
    """返回可能的 path 变体，用于模糊匹配索引。"""
    cand = [pure_path]
    if repo_baseurl_tail and pure_path.startswith(repo_baseurl_tail):
        stripped = pure_path[len(repo_baseurl_tail):] or "/"
        if stripped != pure_path:
            cand.append(stripped)
    return cand


def _render(records: List[dict], index: dict, jsonl_path: str, index_path: str, repo_root: str) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines: List[str] = []
    lines.append(f"# capture_selection（抓包选择草稿）")
    lines.append("")
    lines.append(f"- 生成时间：{now}")
    lines.append(f"- 抓包数据：`{os.path.relpath(jsonl_path, repo_root).replace(os.sep, '/')}`")
    lines.append(f"- 索引来源：`{_display_path(index_path, repo_root)}`")
    lines.append(f"- 抓包条目：{len(records)} 条（已按 method+path 去重）")
    lines.append("")
    lines.append("## 使用说明")
    lines.append("")
    lines.append("1. 本文件是 AI 生成的草稿，请勾选你希望写进用例的接口。")
    lines.append("2. `[x]` 表示默认勾选（通常是新接口），`[ ]` 表示不勾选（通常已实现）。")
    lines.append("3. 保存后告诉 AI \"已勾选\"，AI 将根据勾选结果生成方法与用例。")
    lines.append("4. 已自动忽略的登录/登出接口默认不加入用例；如需强制加入，把它从忽略区移到勾选区。")
    lines.append("5. 特殊处理接口（含二进制/文件响应）默认不勾选；如需处理，请先手动补齐响应结构再勾选。")
    lines.append("")

    # 分桶
    normal_new = []
    normal_exist = []
    special = []
    login_ignored = []

    for r in records:
        if r.get("is_login"):
            login_ignored.append(r)
            continue
        if r.get("body_skipped"):
            special.append(r)
            continue
        index["current_method"] = r.get("method", "")
        impls = _find_impl(index, r.get("pure_path", ""))
        if impls:
            normal_exist.append((r, impls))
        else:
            normal_new.append(r)

    # 需要加入用例的接口
    lines.append("## 需要加入用例的接口（请勾选）")
    lines.append("")
    if not (normal_new or normal_exist):
        lines.append("_无候选接口_")
        lines.append("")
    else:
        lines.append("### 新接口（推荐勾选）")
        lines.append("")
        if not normal_new:
            lines.append("_无_")
        for i, r in enumerate(normal_new, 1):
            lines.append(f"- [x] **{i}. {r.get('method','?')} `{r.get('pure_path','?')}`**")
            lines.append(f"  - 状态码：{r.get('status')}")
            lines.append(f"  - 完整 URL：`{r.get('url','')}`")
            rb = r.get("req_body")
            if rb:
                rb_short = rb if len(rb) <= 200 else rb[:200] + "..."
                lines.append(f"  - 请求体（节选）：`{rb_short}`")
        lines.append("")

        lines.append("### 已实现接口（如需重跑保留，请手动勾选）")
        lines.append("")
        if not normal_exist:
            lines.append("_无_")
        for i, (r, impls) in enumerate(normal_exist, 1):
            lines.append(f"- [ ] **{i}. {r.get('method','?')} `{r.get('pure_path','?')}`**")
            for im in impls[:3]:
                lines.append(
                    f"  - 已实现：`{im['file']}` → `{im.get('class') or im.get('class_name')}.{im.get('api_name') or im.get('method')}` (line {im['line']})"
                )
            if len(impls) > 3:
                lines.append(f"  - 另有 {len(impls)-3} 处实现，详见索引")
        lines.append("")

    # 特殊处理
    lines.append("## 特殊处理接口（二进制/文件响应，请手动处理）")
    lines.append("")
    if not special:
        lines.append("_无_")
    for i, r in enumerate(special, 1):
        lines.append(f"- [ ] **{i}. {r.get('method','?')} `{r.get('pure_path','?')}`** ⚠️ {r.get('skip_reason','')}")
        lines.append(f"  - 状态码：{r.get('status')}")
        lines.append(f"  - Content-Type：{r.get('resp_content_type','')}")
    lines.append("")

    # 已忽略登录
    lines.append("## 已自动忽略的登录/登出接口")
    lines.append("")
    if not login_ignored:
        lines.append("_无_")
    for r in login_ignored:
        lines.append(f"- ~~{r.get('method','?')} `{r.get('pure_path','?')}`~~")
    lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("_勾选完成后，告诉 AI \"已勾选\"即可继续生成。_")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--jsonl", default=None, help="抓包 JSONL 路径（默认 api_test_dwp_temp/latest.jsonl）")
    parser.add_argument("--out", default=None, help="输出草稿路径（默认 api_test_dwp_temp/capture_selection.md）")
    parser.add_argument("--db", default=INDEX_DB_PATH, help="SQLite 索引路径（默认 tools/page_api_index.sqlite3）")
    args = parser.parse_args()

    repo_root = _resolve_repo_root()
    if not repo_root:
        print("ERROR: 未找到项目根（含 E10自动化 目录）。请确认 skill 安装在 <project>/.claude/skills/api-test-E10/ 路径下。", file=sys.stderr)
        return 1

    temp_dir = _get_temp_dir()
    if not temp_dir:
        return 1

    # 索引来自 skill 全局 tools/ 目录（纳入版本管理）
    # 抓包数据与勾选草稿落在项目 api_test_dwp_temp/
    jsonl_path = args.jsonl or os.path.join(temp_dir, "latest.jsonl")
    out_md = args.out or os.path.join(temp_dir, "capture_selection.md")

    index = {"methods": load_methods(args.db)}
    if not index.get("methods"):
        print("WARN: page_api_index.sqlite3 为空或缺失，请先运行 scan_page_api.py", file=sys.stderr)

    records = _load_jsonl(jsonl_path)
    if not records:
        print(f"WARN: 抓包数据为空 → {jsonl_path}", file=sys.stderr)

    records = _dedup_by_method_path(records)
    content = _render(records, index, jsonl_path, args.db, repo_root)

    with open(out_md, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"[match_captures] records={len(records)} → {out_md}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
