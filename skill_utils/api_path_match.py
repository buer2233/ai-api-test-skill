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

    每个占位符匹配同一路径段内的非 `/` 内容，兼容
    `/api/{module}/{submodule}/stage` 与 `/api/inc/{1}data/` 等写法。
    """
    normalized = _normalize(covered_path)
    if not re.search(r"\{[^/{}]+\}", normalized):
        return False
    pattern = re.escape(normalized)
    pattern = re.sub(r"\\\{[^/{}]+\\\}", "[^/]+", pattern)
    return re.fullmatch(pattern, _normalize(captured_path)) is not None


MATCH_RULES: List[PathMatcher] = [
    _exact_match,
    _brace_placeholder_match,
]


def api_path_matches(covered_path: str, captured_path: str) -> bool:
    """按规则列表判断已覆盖接口是否能匹配抓包接口。"""
    return any(rule(covered_path, captured_path) for rule in MATCH_RULES)
