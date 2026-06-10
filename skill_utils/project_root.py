# -*- coding: utf-8 -*-
# Create Date:2026/5/11
# Author: dengwanpeng

"""项目根定位与运行时产物目录解析（多模块共用）。

设计要点：
- 本 skill 面向通用 python + pytest + requests 接口自动化项目。
- 项目根必须由 skill 根目录 config.json 的 project_root 明确配置。
- 不再依赖 CWD 向上搜索，也不再使用 E10 目录 marker fallback。
- 仍提供 on_warn/on_info callback 注入，便于 mitmdump / 独立脚本各自适配日志方式。

被以下模块共用：
- capture/capture_addon.py
- tools/match_captures.py
- tools/scan_page_api.py
- tools/preflight_check.py
"""

import os
from typing import Callable, Optional

from skill_utils.config_loader import ConfigError, load_config


# 旧版常量仅保留给历史 import 兼容；不再作为项目根定位依据。
REPO_MARKER = ""
# 运行时产物默认落在消费方项目下的子目录名。
TEMP_DIR_NAME = "api_test_dwp_temp"
# config.json 在 skill 根目录（baseurl / apiDataUpdateDate 等运行时配置仍写入此处）
CONFIG_FILENAME = "config.json"

# 工具内部默认 skill 根（skill_utils 包的上一级即 skill 根）
SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_CONFIG_PATH = os.path.join(SKILL_ROOT, CONFIG_FILENAME)

# 旧版 PROJECT_ROOT 不再用于定位；保留空字符串兼容历史 import。
PROJECT_ROOT = ""


LogFn = Optional[Callable[[str], None]]


def _noop(_msg: str) -> None:
    pass


def resolve_project_root(
    on_warn: LogFn = None,
    on_info: LogFn = None,
) -> Optional[str]:
    """返回 config.json 中声明的项目根绝对路径。"""
    warn = on_warn or _noop
    info = on_info or _noop
    try:
        config = load_config()
    except ConfigError as exc:
        warn(f"项目根配置无效: {exc}")
        return None
    project_root = str(config.project_root)
    info(f"使用项目根 {project_root}")
    return project_root


def get_temp_dir(
    on_warn: LogFn = None,
    on_info: LogFn = None,
) -> Optional[str]:
    """返回 <project>/api_test_dwp_temp 目录绝对路径，并确保其存在。"""
    warn = on_warn or _noop
    info = on_info or _noop
    try:
        config = load_config()
    except ConfigError as exc:
        warn(f"运行时目录配置无效: {exc}")
        return None
    temp_dir = str(config.runtime_temp_dir)
    os.makedirs(temp_dir, exist_ok=True)
    info(f"使用运行时目录 {temp_dir}")
    return temp_dir
