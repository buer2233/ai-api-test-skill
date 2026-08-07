# -*- coding: utf-8 -*-
# Author: dengwanpeng

"""API 路径匹配规则。"""

import re
from typing import Callable, List


PathMatcher = Callable[[str, str], bool]


def _normalize(path: str) -> str:
    if not path:
        return ""
    value = path.split("?", 1)[0].strip()
    if not value.startswith("/"):
        value = "/" + value
    return value.rstrip("/") or "/"


def _exact_match(covered_path: str, captured_path: str) -> bool:
    return _normalize(covered_path) == _normalize(captured_path)


def _brace_placeholder_match(covered_path: str, captured_path: str) -> bool:
    """支持一个或多个 `{任意值}` 路径占位符匹配。

    每个占位符默认匹配**同一路径段**内的非 `/` 内容，兼容
    `/api/{module}/{submodule}/stage` 与 `/api/inc/{1}data/` 等写法。
    """
    normalized = _normalize(covered_path)
    if not re.search(r"\{[^/{}]+\}", normalized):
        return False
    pattern = re.escape(normalized)
    pattern = re.sub(r"\\\{[^/{}]+\\\}", "[^/]+", pattern)
    return re.fullmatch(pattern, _normalize(captured_path)) is not None


def _param_multi_segment_match(template_path: str, concrete_path: str) -> bool:
    """`{param}` / `{module}` 等占位符可匹配 **1 个或多个** 路径段。

    用于前端 ``/api/${getApiEbuilderModule(appId)}/groupchat/xxx`` 被抽取为
    ``/api/{param}/groupchat/xxx`` 后，与索引中
    ``/api/ebuilder/form/groupchat/xxx`` 对齐（``{param}`` → ``ebuilder/form``）。

    **禁止**仅靠末尾后缀裸匹配跨产品接口；字面量段必须完全一致。
    """
    t_parts = [p for p in _normalize(template_path).split("/") if p]
    c_parts = [p for p in _normalize(concrete_path).split("/") if p]
    if not t_parts or not c_parts:
        return False

    def is_ph(seg: str) -> bool:
        return bool(re.fullmatch(r"\{[^/{}]+\}", seg)) or seg == "{param}"

    def dfs(i: int, j: int) -> bool:
        if i == len(t_parts) and j == len(c_parts):
            return True
        if i == len(t_parts):
            return False
        if is_ph(t_parts[i]):
            # 至少一个段
            if j >= len(c_parts):
                return False
            for end in range(j + 1, len(c_parts) + 1):
                if dfs(i + 1, end):
                    return True
            return False
        if j >= len(c_parts):
            return False
        if is_ph(c_parts[j]) or t_parts[i] == c_parts[j]:
            return dfs(i + 1, j + 1)
        return False

    # 仅当模板含占位符时启用（避免两段全字面量误走本规则）
    if not any(is_ph(p) for p in t_parts):
        return False
    return dfs(0, 0)


MATCH_RULES: List[PathMatcher] = [
    _exact_match,
    _brace_placeholder_match,
    _param_multi_segment_match,
]


def api_path_matches(covered_path: str, captured_path: str) -> bool:
    """按规则列表判断已覆盖接口是否能匹配抓包/信号接口。

    双向尝试：索引路径 vs 信号路径、信号路径 vs 索引路径
    （``{param}`` 可能出现在任一侧）。
    """
    if any(rule(covered_path, captured_path) for rule in MATCH_RULES):
        return True
    if covered_path != captured_path and any(
        rule(captured_path, covered_path) for rule in MATCH_RULES
    ):
        return True
    return False
