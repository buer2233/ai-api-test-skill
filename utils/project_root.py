# -*- coding: utf-8 -*-
# Create Date:2026/5/11
# Author: dengwanpeng
"""项目根定位与运行时产物目录解析（多模块共用）。

设计目标：
- 屏蔽 mitmdump / 独立脚本两种运行上下文下的"日志方式差异"——通过
  on_warn / on_info callback 注入；utils 本身不依赖任何日志库。
- 提供"先 config.json 显式声明，后 CWD 向上搜索"的两段式定位策略，
  避免 CWD 不在消费方项目内时把运行时产物错写到 skill 自身目录。

被以下模块共用：
- capture/capture_addon.py
- tools/match_captures.py
- tools/scan_page_api.py
"""

import json
import os
from typing import Callable, Optional


# 仓库结构硬约束：test-automation 项目根下必有 "E10自动化" 子目录
REPO_MARKER = "E10自动化"
# skill 内运行时产物在消费方项目下的子目录名
TEMP_DIR_NAME = "api_test_dwp_temp"
# config.json 在 skill 根目录
CONFIG_FILENAME = "config.json"

# 工具内部默认 skill 根（utils 包的上一级即 skill 根）
SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_CONFIG_PATH = os.path.join(SKILL_ROOT, CONFIG_FILENAME)


LogFn = Optional[Callable[[str], None]]


def _noop(_msg: str) -> None:
    pass


def find_repo_root(start: str, max_levels: int = 10) -> Optional[str]:
    """从 start 向上最多 max_levels 层，找到含 REPO_MARKER 子目录的根。"""
    cur = start
    for _ in range(max_levels):
        if os.path.isdir(os.path.join(cur, REPO_MARKER)):
            return cur
        parent = os.path.dirname(cur)
        if parent == cur:
            return None
        cur = parent
    return None


def find_project_root_from_cwd() -> Optional[str]:
    """从当前工作目录向上查找 test-automation 项目根。"""
    return find_repo_root(os.getcwd())


def load_project_path_from_config(
    config_path: str = DEFAULT_CONFIG_PATH,
    on_warn: LogFn = None,
) -> Optional[str]:
    """读取 skill 根目录 config.json 的 project_path 字段（严格模式）。

    严格校验规则（任一不满足即返回 None，由调用方决定 fallback）：
      1) config.json 文件存在且 JSON 解析成功
      2) project_path 非空字符串
      3) 必须是绝对路径
      4) 目录真实存在
      5) 必须含有 REPO_MARKER 子目录（确认是 test-automation 项目根）

    on_warn: 可选的告警 callback。mitmdump 传 ctx.log.warn，独立脚本传
             lambda m: print("WARN: "+m, file=sys.stderr)。
    """
    warn = on_warn or _noop
    if not os.path.isfile(config_path):
        return None
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            cfg = json.load(f)
    except Exception as e:
        warn(f"读取 config.json 失败: {e}")
        return None
    raw = (cfg.get("project_path") or "").strip()
    if not raw:
        return None
    path = os.path.normpath(raw)
    if not os.path.isabs(path):
        warn(f"config.project_path 必须为绝对路径，已忽略: {raw}")
        return None
    if not os.path.isdir(path):
        warn(f"config.project_path 目录不存在，已忽略: {path}")
        return None
    if not os.path.isdir(os.path.join(path, REPO_MARKER)):
        warn(f"config.project_path 下未找到 {REPO_MARKER} 子目录，已忽略: {path}")
        return None
    return path


def resolve_project_root(
    config_path: str = DEFAULT_CONFIG_PATH,
    on_warn: LogFn = None,
    on_info: LogFn = None,
) -> Optional[str]:
    """统一入口：优先用 config.json 显式配置，否则回退到 CWD 向上搜索。"""
    info = on_info or _noop
    explicit = load_project_path_from_config(config_path, on_warn=on_warn)
    if explicit:
        info(f"使用 config.json 中的 project_path={explicit}")
        return explicit
    return find_project_root_from_cwd()


def get_temp_dir(
    config_path: str = DEFAULT_CONFIG_PATH,
    on_warn: LogFn = None,
    on_info: LogFn = None,
) -> Optional[str]:
    """返回消费方项目下的 api_test_dwp_temp 目录绝对路径，并确保其存在。

    无法定位项目根时返回 None；调用方应负责降级处理（例如 fallback 到
    脚本自身目录，或直接报错退出）。
    """
    repo_root = resolve_project_root(config_path, on_warn=on_warn, on_info=on_info)
    if not repo_root:
        return None
    temp_dir = os.path.join(repo_root, TEMP_DIR_NAME)
    os.makedirs(temp_dir, exist_ok=True)
    return temp_dir
