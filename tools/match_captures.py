# -*- coding: utf-8 -*-
r"""读取 capture/latest.jsonl + tools/page_api_index.json，
生成 api-test-dwp/capture_selection.md 草稿供用户勾选。

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
SKILL_DIR = os.path.dirname(TOOLS_DIR)
INDEX_PATH = os.path.join(TOOLS_DIR, "page_api_index.json")
DEFAULT_JSONL = os.path.join(SKILL_DIR, "capture", "latest.jsonl")
OUT_MD = os.path.join(SKILL_DIR, "capture_selection.md")


def _load_index() -> dict:
    if not os.path.isfile(INDEX_PATH):
        return {"methods": [], "by_path": {}}
    with open(INDEX_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _load_jsonl(path: str) -> List[dict]:
    if not os.path.isfile(path):
        return []
    records = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
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


def _find_impl(index: dict, pure_path: str):
    methods = index.get("methods", [])
    ids = index.get("by_path", {}).get(pure_path, [])
    return [methods[i] for i in ids if 0 <= i < len(methods)]


def _normalize_path_for_index(pure_path: str, repo_baseurl_tail: str = "") -> List[str]:
    """返回可能的 path 变体，用于模糊匹配索引。"""
    cand = [pure_path]
    if repo_baseurl_tail and pure_path.startswith(repo_baseurl_tail):
        stripped = pure_path[len(repo_baseurl_tail):] or "/"
        if stripped != pure_path:
            cand.append(stripped)
    return cand


def _render(records: List[dict], index: dict, jsonl_path: str) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines: List[str] = []
    lines.append(f"# capture_selection（抓包选择草稿）")
    lines.append("")
    lines.append(f"- 生成时间：{now}")
    lines.append(f"- 抓包数据：`{os.path.relpath(jsonl_path, SKILL_DIR).replace(os.sep, '/')}`")
    lines.append(f"- 索引来源：`{os.path.relpath(INDEX_PATH, SKILL_DIR).replace(os.sep, '/')}`")
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
                    f"  - 已实现：`{im['file']}` → `{im['class']}.{im['method']}` (line {im['line']})"
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
    parser.add_argument("--jsonl", default=DEFAULT_JSONL, help="抓包 JSONL 路径")
    parser.add_argument("--out", default=OUT_MD, help="输出草稿路径")
    args = parser.parse_args()

    index = _load_index()
    if not index.get("methods"):
        print("WARN: page_api_index.json 为空或缺失，请先运行 scan_page_api.py", file=sys.stderr)

    records = _load_jsonl(args.jsonl)
    if not records:
        print(f"WARN: 抓包数据为空 → {args.jsonl}", file=sys.stderr)

    records = _dedup_by_method_path(records)
    content = _render(records, index, args.jsonl)

    with open(args.out, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"[match_captures] records={len(records)} → {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
