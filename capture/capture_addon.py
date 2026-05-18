# -*- coding: utf-8 -*-
# Author: dengwanpeng

"""api-test-E10 mitmdump addon

功能：
- 从仓库 RunConfig.baseurl 读取目标域名
- 按 baseurl + 可扩展前缀列表过滤请求
- 对二进制/文件响应跳过 body
- 对登录/登出接口打标
- 对 Cookie/Authorization 做摘要
- 落盘 api_test_dwp_temp/latest.jsonl（JSON Lines）

启动方式：
    mitmdump -s capture_addon.py --listen-port 12138
或双击 start.bat
"""

import ast
import json
import os
import re
import sys
import time
from datetime import datetime
from typing import List, Optional


ADDON_DIR = os.path.dirname(os.path.abspath(__file__))
_SKILL_ROOT = os.path.dirname(ADDON_DIR)
if _SKILL_ROOT not in sys.path:
    sys.path.insert(0, _SKILL_ROOT)

from mitmproxy import ctx, http  # noqa: E402

from skill_utils.common_function import update_skill_config  # noqa: E402
from skill_utils.project_root import (  # noqa: E402
    DEFAULT_CONFIG_PATH,
    TEMP_DIR_NAME,
    resolve_project_root,
)


PREFIX_FILE = os.path.join(ADDON_DIR, "allowed_prefixes.txt")


def _warn(msg: str) -> None:
    ctx.log.warn(f"[api-test-E10] {msg}")


def _info(msg: str) -> None:
    ctx.log.info(f"[api-test-E10] {msg}")


def _resolve_repo_root() -> Optional[str]:
    return resolve_project_root(
        on_warn=_warn,
        on_info=_info,
    )

DEFAULT_PREFIXES = [
    "/api/",
    "/sapi/",
    "/base/",
    "/papi/",
    "/ipconfigrec/",
    "/tenantlogo/",
    "/app/",
]

# 静态资源扩展名（黑名单）
STATIC_SUFFIX = (
    ".css", ".js", ".png", ".jpg", ".jpeg", ".gif", ".svg",
    ".woff", ".woff2", ".ttf", ".eot", ".ico", ".map",
)

# 二进制 Content-Type 前缀（白名单式检测，命中即跳 body）
BINARY_CT_PREFIXES = (
    "application/octet-stream",
    "application/pdf",
    "application/zip",
    "application/x-zip",
    "application/x-rar",
    "application/x-7z",
    "application/x-tar",
    "application/x-gzip",
    "application/vnd.ms-",
    "application/vnd.openxmlformats-",
    "image/",
    "video/",
    "audio/",
)

# 登录/登出路径片段
LOGIN_PATH_HINTS = (
    "/auth/login",
    "/auth/logout",
    "/auth/token",
    "/api/login",
    "/api/logout",
    "/ec/auth/login",
    "/ec/auth/logout",
    "/papi/passport/appnew/login",
)

# 响应体最大保留字节
MAX_BODY_BYTES = 1024 * 1024  # 1MB


# -------------------- 仓库根与临时目录 --------------------
# 项目根定位统一抽到 skill_utils.project_root；本文件不再保留副本。

def _get_jsonl_path() -> str:
    """返回捕获 JSONL 的落地路径，确保产物目录存在。"""
    repo_root = _resolve_repo_root()
    if not repo_root:
        # 无法定位项目根时回退到 skill 目录（极少出现，仅作为兜底）
        return os.path.join(ADDON_DIR, "latest.jsonl")
    temp_dir = os.path.join(repo_root, TEMP_DIR_NAME)
    os.makedirs(temp_dir, exist_ok=True)
    return os.path.join(temp_dir, "latest.jsonl")


# -------------------- baseurl 解析 --------------------

def _parse_baseurl_from_config(config_path: str) -> Optional[str]:
    """用 AST 解析 RunConfig.baseurl，取第一个"未被注释"的赋值。"""
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=config_path)
    except Exception as e:
        ctx.log.warn(f"[api-test-E10] 解析 config.py 失败: {e}")
        return None

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == "RunConfig":
            for stmt in node.body:
                if isinstance(stmt, ast.Assign):
                    for target in stmt.targets:
                        if isinstance(target, ast.Name) and target.id == "baseurl":
                            if isinstance(stmt.value, ast.Constant) and isinstance(stmt.value.value, str):
                                return stmt.value.value
    return None


def _save_baseurl_to_skill_config(baseurl: str) -> None:
    """将当前抓包使用的 baseurl 同步到 skill 根目录 config.json。"""
    if not baseurl:
        return
    update_skill_config(
        {"baseurl": baseurl},
        config_path=DEFAULT_CONFIG_PATH,
        on_warn=_warn,
        on_info=_info,
    )


def _load_baseurl() -> str:
    repo_root = _resolve_repo_root()
    if not repo_root:
        _warn("未找到项目根（skill 未安装在 <project>/.claude/skills/api-test-E10/ 路径下，或项目根缺少 E10自动化 子目录）")
        return ""
    config_path = os.path.join(repo_root, "E10自动化", "接口自动化测试", "config.py")
    if not os.path.isfile(config_path):
        ctx.log.warn(f"[api-test-E10] 未找到 config.py: {config_path}")
        return ""
    baseurl = _parse_baseurl_from_config(config_path)
    if not baseurl:
        ctx.log.warn("[api-test-E10] AST 解析 baseurl 未命中，使用空串（不做 host 过滤）")
        return ""
    baseurl = baseurl.strip()
    _save_baseurl_to_skill_config(baseurl)
    return baseurl


def _load_prefixes() -> List[str]:
    if not os.path.isfile(PREFIX_FILE):
        return list(DEFAULT_PREFIXES)
    try:
        with open(PREFIX_FILE, "r", encoding="utf-8") as f:
            lines = [ln.strip() for ln in f.readlines()]
        prefixes = [ln for ln in lines if ln and not ln.startswith("#")]
        return prefixes or list(DEFAULT_PREFIXES)
    except Exception as e:
        ctx.log.warn(f"[api-test-E10] 读取 allowed_prefixes.txt 失败: {e}")
        return list(DEFAULT_PREFIXES)


# -------------------- 工具 --------------------

def _digest(value: str, keep: int = 20) -> str:
    if not value:
        return ""
    if len(value) <= keep:
        return f"{value}|len={len(value)}"
    return f"{value[:keep]}...|len={len(value)}"


def _is_binary_ct(ct: str) -> bool:
    ct = (ct or "").lower()
    return any(ct.startswith(p) for p in BINARY_CT_PREFIXES)


def _looks_encoded_blob(body_bytes: bytes) -> bool:
    """启发式：超过 2KB 且只包含 base64/十六进制/纯数字字符。"""
    if len(body_bytes) <= 2048:
        return False
    try:
        text = body_bytes.decode("ascii")
    except UnicodeDecodeError:
        return False
    if re.fullmatch(r"[A-Za-z0-9+/=\s]+", text):
        return True
    if re.fullmatch(r"[0-9a-fA-F\s]+", text):
        return True
    if re.fullmatch(r"[0-9\s]+", text):
        return True
    return False


def _match_baseurl(host_port: str, baseurl: str) -> bool:
    if not baseurl:
        return True  # 未解析到 baseurl 时不做 host 过滤（配日志已提示）
    # baseurl 可能含 host:port/path 片段，取 host[:port] 部分比较
    target = baseurl.split("/")[0].strip().lower()
    return host_port.lower() == target or host_port.lower().startswith(target + ":")


def _is_login_path(path: str) -> bool:
    p = path.lower()
    return any(hint in p for hint in LOGIN_PATH_HINTS) or re.search(r"/(login|logout)(?:\?|$)", p) is not None


# -------------------- Addon --------------------

class ApiCaptureAddon:
    def __init__(self):
        self.baseurl = _load_baseurl()
        self.prefixes = _load_prefixes()
        self.jsonl_path = _get_jsonl_path()
        self._ensure_jsonl()
        ctx.log.info(f"[api-test-E10] self.baseurl = {self.baseurl or '<empty>'}")
        ctx.log.info(f"[api-test-E10] self.prefixes = {self.prefixes}")
        ctx.log.info(f"[api-test-E10] self.jsonl_path = {self.jsonl_path}")

    def _ensure_jsonl(self):
        if not os.path.isfile(self.jsonl_path):
            open(self.jsonl_path, "w", encoding="utf-8").close()

    def _should_capture(self, flow: http.HTTPFlow) -> bool:
        req = flow.request
        path = req.path or "/"
        # 静态资源
        pure_path = path.split("?", 1)[0].lower()
        if pure_path.endswith(STATIC_SUFFIX):
            return False
        # host 过滤
        host_port = req.host
        if req.port and req.port not in (80, 443):
            host_port = f"{req.host}:{req.port}"
        if not _match_baseurl(host_port, self.baseurl):
            return False
        # 前缀过滤
        if not any(pure_path.startswith(p) for p in self.prefixes):
            # 有些 baseurl 形如 host/oa/second，真实请求路径会被代理带上 /oa/second 前缀
            # 这里做一次二次剥离尝试
            base_tail = ""
            if self.baseurl and "/" in self.baseurl:
                base_tail = "/" + self.baseurl.split("/", 1)[1].rstrip("/")
            if base_tail and pure_path.startswith(base_tail):
                stripped = pure_path[len(base_tail):] or "/"
                if not any(stripped.startswith(p) for p in self.prefixes):
                    return False
            else:
                return False
        return True

    def _build_record(self, flow: http.HTTPFlow) -> dict:
        req = flow.request
        resp = flow.response

        # Header 脱敏
        req_headers = {}
        for k, v in req.headers.items():
            lk = k.lower()
            if lk in ("cookie", "authorization"):
                req_headers[k] = _digest(v)
            else:
                req_headers[k] = v

        # Request body
        req_body_text = None
        try:
            if req.content is not None:
                req_body_text = req.get_text(strict=False)
        except Exception:
            req_body_text = None

        # Response body 处理
        body_skipped = False
        body_truncated = False
        skip_reason = ""
        resp_body_text = None
        resp_content_type = (resp.headers.get("content-type") or "") if resp else ""

        if resp is not None:
            raw = resp.raw_content or b""
            if _is_binary_ct(resp_content_type):
                body_skipped = True
                skip_reason = f"binary-content-type:{resp_content_type}"
                resp_body_text = f"<BINARY_SKIPPED: content-type={resp_content_type}, size={len(raw)}>"
            elif _looks_encoded_blob(raw):
                body_skipped = True
                skip_reason = "encoded-blob"
                resp_body_text = f"<ENCODED_SKIPPED: size={len(raw)}>"
            else:
                if len(raw) > MAX_BODY_BYTES:
                    body_truncated = True
                    try:
                        resp_body_text = raw[:MAX_BODY_BYTES].decode("utf-8", errors="replace")
                    except Exception:
                        resp_body_text = f"<TRUNCATE_DECODE_FAIL: size={len(raw)}>"
                else:
                    try:
                        resp_body_text = resp.get_text(strict=False)
                    except Exception:
                        resp_body_text = None

        pure_path = (req.path or "/").split("?", 1)[0]
        is_login = _is_login_path(pure_path)

        host_port = req.host
        if req.port and req.port not in (80, 443):
            host_port = f"{req.host}:{req.port}"

        return {
            "ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"),
            "epoch": time.time(),
            "method": req.method,
            "scheme": req.scheme,
            "host": host_port,
            "path": req.path,
            "pure_path": pure_path,
            "url": req.url,
            "req_headers": req_headers,
            "req_body": req_body_text,
            "status": resp.status_code if resp else None,
            "resp_content_type": resp_content_type,
            "resp_body": resp_body_text,
            "body_skipped": body_skipped,
            "body_truncated": body_truncated,
            "skip_reason": skip_reason,
            "is_login": is_login,
        }

    def response(self, flow: http.HTTPFlow):
        try:
            if not self._should_capture(flow):
                return
            record = self._build_record(flow)
            line = json.dumps(record, ensure_ascii=False)
            with open(self.jsonl_path, "a", encoding="utf-8") as f:
                f.write(line + "\n")
        except Exception as e:
            ctx.log.warn(f"[api-test-E10] 落盘异常: {e}")


addons = [ApiCaptureAddon()]
