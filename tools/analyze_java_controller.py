# -*- coding: utf-8 -*-
# Author: dengwanpeng

"""分析 Java Controller 源码/Jacoco 报告并生成接口覆盖草稿。

用法：
    python tools/analyze_java_controller.py --source http://host/StageController.java.html#L76
    python tools/analyze_java_controller.py --source Java-file/java-code1.md

输出：
    <project>/api_test_dwp_temp/java_sourceCode_analysisResult.md
"""

import argparse
import html
import os
import re
import sys
import urllib.request
from datetime import datetime
from typing import Dict, Iterable, List, Optional, Tuple


TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
_SKILL_ROOT = os.path.dirname(TOOLS_DIR)
if _SKILL_ROOT not in sys.path:
    sys.path.insert(0, _SKILL_ROOT)

from skill_utils.api_index_db import get_default_db_path, load_methods  # noqa: E402
from skill_utils.api_path_match import api_path_matches  # noqa: E402
from skill_utils.project_root import get_temp_dir, resolve_project_root  # noqa: E402


INDEX_DB_PATH = get_default_db_path(TOOLS_DIR)
DEFAULT_OUT_NAME = "java_sourceCode_analysisResult.md"

HTTP_METHOD_BY_MAPPING = {
    "GetMapping": "GET",
    "PostMapping": "POST",
    "PutMapping": "PUT",
    "DeleteMapping": "DELETE",
    "PatchMapping": "PATCH",
}


def _warn(msg: str) -> None:
    print(f"WARN: {msg}", file=sys.stderr)


def _is_url(value: str) -> bool:
    return value.startswith("http://") or value.startswith("https://")


def _read_source(source: str) -> Tuple[str, str]:
    if _is_url(source):
        url = source.split("#", 1)[0]
        with urllib.request.urlopen(url, timeout=30) as resp:
            charset = resp.headers.get_content_charset() or "utf-8"
            return resp.read().decode(charset, errors="replace"), source
    with open(source, "r", encoding="utf-8") as f:
        return f.read(), os.path.abspath(source)


def _strip_html_tags(value: str) -> str:
    return re.sub(r"<[^>]+>", "", value)


def _extract_jacoco_pre(raw: str) -> Optional[str]:
    match = re.search(r'<pre class="source[^"]*".*?>(.*?)</pre>', raw, re.S)
    if match:
        return match.group(1)
    return None


def _extract_markdown_java(raw: str) -> Optional[str]:
    match = re.search(r"```(?:java)?\s*(.*?)```", raw, re.S | re.I)
    if match:
        return match.group(1)
    return None


def _extract_source_and_coverage(raw: str) -> Tuple[str, Dict[int, dict], bool]:
    """返回 Java 源码、Jacoco 行覆盖信息、是否来自 Jacoco HTML。"""
    pre = _extract_jacoco_pre(raw)
    if pre is not None:
        coverage: Dict[int, dict] = {}
        span_re = re.compile(
            r'<span\s+class="([^"]+)"\s+id="L(\d+)"(?:\s+title="([^"]*)")?>(.*?)</span>',
            re.S,
        )
        for match in span_re.finditer(pre):
            classes, line_no, title, body = match.groups()
            coverage[int(line_no)] = {
                "classes": classes,
                "title": html.unescape(title or ""),
                "text": html.unescape(_strip_html_tags(body)).strip(),
            }
        source = html.unescape(_strip_html_tags(pre))
        return source, coverage, True

    fenced = _extract_markdown_java(raw)
    if fenced is not None:
        return fenced, {}, False
    return raw, {}, False


def _normalize_path(path: str) -> str:
    value = (path or "").strip()
    if not value:
        return ""
    if not value.startswith("/"):
        value = "/" + value
    value = re.sub(r"/+", "/", value)
    return value.rstrip("/") or "/"


def _join_paths(base: str, sub: str) -> str:
    if not base:
        return _normalize_path(sub)
    if not sub:
        return _normalize_path(base)
    return _normalize_path(f"{base.rstrip('/')}/{sub.lstrip('/')}")


def _annotation_args(line: str) -> str:
    start = line.find("(")
    end = line.rfind(")")
    if start == -1 or end == -1 or end <= start:
        return ""
    return line[start + 1:end]


def _mapping_path(annotation_line: str) -> str:
    args = _annotation_args(annotation_line)
    if not args:
        return ""
    named = re.search(r'(?:value|path)\s*=\s*(?:\{\s*)?"([^"]+)"', args)
    if named:
        return named.group(1)
    first = re.search(r'"([^"]+)"', args)
    return first.group(1) if first else ""


def _request_mapping_method(annotation_line: str) -> str:
    args = _annotation_args(annotation_line)
    method = re.search(r"RequestMethod\.(GET|POST|PUT|DELETE|PATCH)", args)
    if method:
        return method.group(1)
    direct = re.search(r'method\s*=\s*"?(GET|POST|PUT|DELETE|PATCH)"?', args, re.I)
    if direct:
        return direct.group(1).upper()
    return ""


def _api_operation(annotation_lines: Iterable[str]) -> str:
    for line in annotation_lines:
        if "@ApiOperation" not in line:
            continue
        args = _annotation_args(line)
        named = re.search(r'(?:value|notes)\s*=\s*"([^"]+)"', args)
        if named:
            return named.group(1)
        first = re.search(r'"([^"]+)"', args)
        if first:
            return first.group(1)
    return ""


def _extract_class_mapping(source: str) -> str:
    before_class = source.split(" class ", 1)[0]
    matches = list(re.finditer(r"@RequestMapping\s*\((.*?)\)", before_class, re.S))
    if not matches:
        return ""
    return _mapping_path(matches[-1].group(0))


def _split_params(params: str) -> List[str]:
    result: List[str] = []
    buf: List[str] = []
    angle = 0
    paren = 0
    for ch in params:
        if ch == "<":
            angle += 1
        elif ch == ">" and angle:
            angle -= 1
        elif ch == "(":
            paren += 1
        elif ch == ")" and paren:
            paren -= 1
        if ch == "," and angle == 0 and paren == 0:
            item = "".join(buf).strip()
            if item:
                result.append(item)
            buf = []
            continue
        buf.append(ch)
    item = "".join(buf).strip()
    if item:
        result.append(item)
    return result


def _parse_param(param: str) -> dict:
    clean = " ".join(param.split())
    kind = "普通参数"
    if "@RequestBody" in clean:
        kind = "RequestBody"
    elif "@RequestParam" in clean:
        kind = "RequestParam"
    elif "HttpServletRequest" in clean:
        kind = "HttpServletRequest"

    explicit_name = ""
    name_match = re.search(r"@RequestParam\s*\((.*?)\)", clean)
    if name_match:
        args = name_match.group(1)
        named = re.search(r'(?:value|name)\s*=\s*"([^"]+)"', args)
        direct = re.search(r'"([^"]+)"', args)
        explicit_name = (named or direct).group(1) if (named or direct) else ""

    required = None
    if "required = false" in clean or "required=false" in clean:
        required = False
    elif "@RequestParam" in clean:
        required = True

    default = ""
    default_match = re.search(r'defaultValue\s*=\s*"([^"]*)"', clean)
    if default_match:
        default = default_match.group(1)

    without_annotations = re.sub(r"@\w+(?:\([^)]*\))?\s*", "", clean).strip()
    pieces = without_annotations.split()
    param_name = pieces[-1] if pieces else ""
    param_type = " ".join(pieces[:-1]) if len(pieces) >= 2 else without_annotations
    return {
        "kind": kind,
        "name": explicit_name or param_name,
        "java_name": param_name,
        "type": param_type,
        "required": required,
        "default": default,
    }


def _method_block(lines: List[str], method_line_idx: int) -> Tuple[str, int]:
    block: List[str] = []
    brace_count = 0
    started = False
    end_idx = method_line_idx
    for idx in range(method_line_idx, len(lines)):
        line = lines[idx]
        block.append(line)
        brace_count += line.count("{")
        if "{" in line:
            started = True
        brace_count -= line.count("}")
        end_idx = idx
        if started and brace_count <= 0:
            break
    return "\n".join(block), end_idx


def _parse_controller(source: str, coverage: Dict[int, dict]) -> List[dict]:
    lines = source.splitlines()
    class_mapping = _extract_class_mapping(source)
    endpoints: List[dict] = []

    idx = 0
    while idx < len(lines):
        line = lines[idx].strip()
        mapping_type = ""
        http_method = ""
        if re.search(r"@(GetMapping|PostMapping|PutMapping|DeleteMapping|PatchMapping)\b", line):
            mapping_type = re.search(
                r"@(GetMapping|PostMapping|PutMapping|DeleteMapping|PatchMapping)\b", line
            ).group(1)
            http_method = HTTP_METHOD_BY_MAPPING[mapping_type]
        elif "@RequestMapping" in line:
            # 类级 RequestMapping 不包含 public 方法声明，后续查不到方法行会自然跳过。
            mapping_type = "RequestMapping"
            http_method = _request_mapping_method(line)
        else:
            idx += 1
            continue

        method_line_idx = -1
        for probe in range(idx + 1, min(idx + 12, len(lines))):
            if re.search(r"\bpublic\b.+\w+\s*\(.*\)", lines[probe]):
                method_line_idx = probe
                break
        if method_line_idx == -1:
            idx += 1
            continue

        annotation_lines = [lines[pos].strip() for pos in range(idx, method_line_idx)]
        signature = lines[method_line_idx].strip()
        sig = re.search(r"\bpublic\s+(.+?)\s+(\w+)\s*\((.*)\)", signature)
        if not sig:
            idx += 1
            continue

        return_type, method_name, raw_params = sig.groups()
        block, end_idx = _method_block(lines, method_line_idx)
        path = _mapping_path(line)
        api_url = _join_paths(class_mapping, path)
        params = [_parse_param(item) for item in _split_params(raw_params)]
        service_calls = sorted(set(re.findall(r"\b(\w+(?:Service|Util|API|Api)\.\w+)\s*\(", block)))
        line_start = method_line_idx + 1
        line_end = end_idx + 1
        coverage_items = [
            item for line_no, item in coverage.items() if line_start <= line_no <= line_end
        ]
        jacoco_status = _coverage_status(coverage_items)
        special_notes = _special_param_notes(http_method, params)
        endpoints.append(
            {
                "method": http_method or "UNKNOWN",
                "api_url": api_url,
                "mapping_type": mapping_type,
                "class_mapping": class_mapping,
                "method_mapping": path,
                "java_method": method_name,
                "return_type": return_type.strip(),
                "api_operation": _api_operation(annotation_lines),
                "params": params,
                "service_calls": service_calls,
                "line_start": line_start,
                "line_end": line_end,
                "jacoco_status": jacoco_status,
                "jacoco_details": _coverage_details(coverage_items),
                "category": _classify_endpoint(http_method, method_name, api_url, params),
                "special_notes": special_notes,
            }
        )
        idx = end_idx + 1
    return endpoints


def _coverage_status(items: List[dict]) -> str:
    if not items:
        return "无染色信息"
    classes = " ".join(item.get("classes", "") for item in items)
    if "nc" in classes or "bnc" in classes:
        return "未覆盖或分支未覆盖"
    if "fc" in classes:
        return "已覆盖"
    return "无染色信息"


def _coverage_details(items: List[dict]) -> str:
    missed = []
    for item in items:
        classes = item.get("classes", "")
        if "nc" in classes or "bnc" in classes:
            detail = item.get("title") or item.get("text") or classes
            if detail:
                missed.append(detail)
    return "；".join(missed[:3])


def _special_param_notes(http_method: str, params: List[dict]) -> List[str]:
    notes = []
    if http_method == "GET" and any(p["kind"] == "RequestBody" for p in params):
        notes.append("GET 方法包含 @RequestBody，真实调用方式需要重点确认")
    if any(p["kind"] == "HttpServletRequest" for p in params):
        notes.append("参数来自 HttpServletRequest，需要从源码中的 request2Map/params.get 语句反推")
    return notes


def _classify_endpoint(http_method: str, method_name: str, api_url: str, params: List[dict]) -> str:
    lower = f"{method_name} {api_url}".lower()
    if "upload" in lower or any(p["kind"] == "HttpServletRequest" for p in params):
        return "特殊参数接口"
    if http_method == "GET" or re.search(r"\b(get|list|page|query|check|info)\w*", method_name, re.I):
        return "查询/初始化接口"
    if re.search(r"\b(save|update|delete|create|enable|publish|change|set|upload)\w*", method_name, re.I):
        return "写入/状态变更接口"
    return "独立业务接口"


def _find_impls(index_methods: List[dict], endpoint: dict) -> List[dict]:
    matched = []
    current_method = endpoint["method"].upper()
    current_url = endpoint["api_url"]
    for item in index_methods:
        indexed_method = (item.get("method") or item.get("http_method") or "").upper()
        if indexed_method != current_method:
            continue
        indexed_url = item.get("api_url") or item.get("pure_path") or ""
        if api_path_matches(indexed_url, current_url) or api_path_matches(current_url, indexed_url):
            matched.append(item)
    return matched


def _reference_hints(index_methods: List[dict], endpoint: dict) -> List[dict]:
    current_method = endpoint["method"].upper()
    tail = endpoint["api_url"].rstrip("/").split("/")[-1].lower()
    hints = []
    for item in index_methods:
        indexed_method = (item.get("method") or item.get("http_method") or "").upper()
        text = " ".join(
            str(item.get(k) or "")
            for k in ("api_url", "api_name", "api_desc", "file", "class_name")
        ).lower()
        if indexed_method == current_method and tail and tail in text:
            hints.append(item)
    return hints[:3]


def _format_params(params: List[dict]) -> str:
    if not params:
        return "无显式参数"
    parts = []
    for p in params:
        required = ""
        if p["required"] is True:
            required = " required"
        elif p["required"] is False:
            required = " optional"
        default = f" default={p['default']}" if p.get("default") else ""
        parts.append(f"{p['kind']} {p['name']}:{p['type']}{required}{default}")
    return "；".join(parts)


def _scenario_groups(endpoints: List[dict]) -> List[dict]:
    uncovered = [e for e in endpoints if not e.get("impls")]
    groups: Dict[str, List[dict]] = {}
    for endpoint in uncovered:
        groups.setdefault(endpoint["category"], []).append(endpoint)

    scenarios = []
    order = ["查询/初始化接口", "写入/状态变更接口", "特殊参数接口", "独立业务接口"]
    for category in order:
        items = groups.get(category) or []
        if not items:
            continue
        if category == "写入/状态变更接口":
            for item in items:
                scenarios.append(
                    {
                        "title": f"{item['api_operation'] or item['java_method']} 场景",
                        "reason": "写入/状态变更接口通常需要独立校验请求前置、执行结果和后置状态。",
                        "endpoints": [item],
                    }
                )
        else:
            scenarios.append(
                {
                    "title": category,
                    "reason": "接口同属一个初步分类，可作为同一业务链路候选；正式编写前可按用户调整继续拆分。",
                    "endpoints": items,
                }
            )
    return scenarios


def _render_report(
    endpoints: List[dict],
    source_label: str,
    out_md: str,
    index_path: str,
    repo_root: str,
    is_jacoco: bool,
) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    uncovered = [e for e in endpoints if not e.get("impls")]
    covered = [e for e in endpoints if e.get("impls")]
    anomalies = [
        e for e in endpoints
        if (e.get("impls") and "未覆盖" in e["jacoco_status"])
        or (not e.get("impls") and e["jacoco_status"] == "已覆盖")
    ]
    lines: List[str] = []
    lines.append("# java_sourceCode_analysisResult（Java Controller 源码分析草稿）")
    lines.append("")
    lines.append(f"- 生成时间：{now}")
    lines.append(f"- 源码来源：`{source_label}`")
    lines.append(f"- 索引来源：`{_display_path(index_path, repo_root)}`")
    lines.append(f"- 输出文件：`{_display_path(out_md, repo_root)}`")
    lines.append(f"- 来源类型：{'Jacoco HTML 报告' if is_jacoco else 'Java/Markdown 源码'}")
    lines.append(f"- 提取接口：{len(endpoints)} 个；未覆盖候选：{len(uncovered)} 个；已覆盖：{len(covered)} 个")
    lines.append("")
    lines.append("## 使用说明")
    lines.append("")
    lines.append("1. `[x]` 表示候选接口或候选场景，正式编写前 AI 会重新读取本文件。")
    lines.append("2. 未覆盖接口默认 `[x]` 只是候选池，不代表必须写成一条用例。")
    lines.append("3. 你可以修改 `[x]` / `[ ]`、移动接口到其它场景、改场景标题，或在备注里指定参考用例。")
    lines.append("4. 接口是否已覆盖以 `page_api_index.sqlite3` 的 `api_url + method` 为准；Jacoco 染色仅作为参考。")
    lines.append("")

    lines.append("## 一、未覆盖接口候选（默认勾选）")
    lines.append("")
    if not uncovered:
        lines.append("_无_")
    for i, endpoint in enumerate(uncovered, 1):
        _render_endpoint(lines, endpoint, i, checked=True)
    lines.append("")

    lines.append("## 二、建议测试场景设计（可调整分组）")
    lines.append("")
    scenarios = _scenario_groups(endpoints)
    if not scenarios:
        lines.append("_无未覆盖接口，不生成测试场景建议_")
    for i, scenario in enumerate(scenarios, 1):
        lines.append(f"- [x] **场景{i}：{scenario['title']}**")
        lines.append(f"  - 合并/拆分原因：{scenario['reason']}")
        lines.append("  - 覆盖接口：")
        for endpoint in scenario["endpoints"]:
            lines.append(f"    - [x] {endpoint['method']} `{endpoint['api_url']}`")
        lines.append("  - 推断依据：接口分类、方法名、`@ApiOperation`、参数来源、service 调用、读写属性。")
        lines.append("  - 用户备注/参考用例：")
    lines.append("")

    lines.append("## 三、已覆盖接口（默认不勾选）")
    lines.append("")
    if not covered:
        lines.append("_无_")
    for i, endpoint in enumerate(covered, 1):
        _render_endpoint(lines, endpoint, i, checked=False)
    lines.append("")

    lines.append("## 四、覆盖状态异常提醒")
    lines.append("")
    if not anomalies:
        lines.append("_无_")
    for endpoint in anomalies:
        if endpoint.get("impls") and "未覆盖" in endpoint["jacoco_status"]:
            reason = "Jacoco 显示红色/未覆盖，但数据库记录接口已覆盖"
        else:
            reason = "Jacoco 显示绿色/已覆盖，但数据库未记录接口覆盖"
        lines.append(f"- ⚠️ {endpoint['method']} `{endpoint['api_url']}`：{reason}")
    lines.append("")

    lines.append("## 五、参数来源特殊接口")
    lines.append("")
    specials = [e for e in endpoints if e.get("special_notes")]
    if not specials:
        lines.append("_无_")
    for endpoint in specials:
        lines.append(f"- {endpoint['method']} `{endpoint['api_url']}`")
        for note in endpoint["special_notes"]:
            lines.append(f"  - {note}")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("_调整勾选与分组后，告诉 AI “已调整 Java 源码分析草稿”，AI 将按本文件继续编写。_")
    return "\n".join(lines)


def _render_endpoint(lines: List[str], endpoint: dict, index: int, checked: bool) -> None:
    mark = "x" if checked else " "
    title = endpoint["api_operation"] or endpoint["java_method"]
    lines.append(f"- [{mark}] **{index}. {endpoint['method']} `{endpoint['api_url']}`** {title}")
    lines.append(f"  - Java 方法：`{endpoint['java_method']}`，行号：L{endpoint['line_start']}-L{endpoint['line_end']}")
    lines.append(f"  - 参数来源：{_format_params(endpoint['params'])}")
    lines.append(f"  - 返回类型：`{endpoint['return_type']}`")
    lines.append(f"  - service/工具调用：{', '.join(endpoint['service_calls']) if endpoint['service_calls'] else '无明显调用'}")
    lines.append(f"  - 读写属性判断：{endpoint['category']}")
    lines.append(f"  - Jacoco：{endpoint['jacoco_status']}{('；' + endpoint['jacoco_details']) if endpoint['jacoco_details'] else ''}")
    if endpoint.get("impls"):
        for impl in endpoint["impls"][:3]:
            lines.append(
                f"  - 已实现：`{impl['file']}` → `{impl.get('class_name')}.{impl.get('api_name')}` (line {impl['line']})"
            )
    else:
        hints = endpoint.get("reference_hints") or []
        if hints:
            lines.append("  - 相似参考候选：")
            for hint in hints:
                lines.append(
                    f"    - `{hint['file']}` → `{hint.get('class_name')}.{hint.get('api_name')}`；依据：method 相同且 URL/方法名相似"
                )
        else:
            lines.append("  - 相似参考候选：未自动命中，编写前需继续检索用例库")


def _display_path(path: str, repo_root: str) -> str:
    try:
        return os.path.relpath(path, repo_root).replace(os.sep, "/")
    except ValueError:
        return path.replace(os.sep, "/")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, help="Java/Markdown 源码路径，或 Jacoco HTML URL")
    parser.add_argument("--out", default=None, help="输出 Markdown 路径（默认 api_test_dwp_temp/java_sourceCode_analysisResult.md）")
    parser.add_argument("--db", default=INDEX_DB_PATH, help="SQLite 索引路径（默认 tools/page_api_index.sqlite3）")
    args = parser.parse_args()

    repo_root = resolve_project_root(on_warn=_warn)
    if not repo_root:
        print("ERROR: 未找到项目根（含 E10自动化 目录）。", file=sys.stderr)
        return 1
    temp_dir = get_temp_dir(on_warn=_warn)
    if not temp_dir:
        return 1
    out_md = args.out or os.path.join(temp_dir, DEFAULT_OUT_NAME)

    raw, source_label = _read_source(args.source)
    source, coverage, is_jacoco = _extract_source_and_coverage(raw)
    endpoints = _parse_controller(source, coverage)
    index_methods = load_methods(args.db)
    for endpoint in endpoints:
        endpoint["impls"] = _find_impls(index_methods, endpoint)
        endpoint["reference_hints"] = _reference_hints(index_methods, endpoint)

    content = _render_report(endpoints, source_label, out_md, args.db, repo_root, is_jacoco)
    with open(out_md, "w", encoding="utf-8") as f:
        f.write(content)
        f.write("\n")

    uncovered = sum(1 for endpoint in endpoints if not endpoint.get("impls"))
    print(f"[analyze_java_controller] endpoints={len(endpoints)} uncovered={uncovered} -> {out_md}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
