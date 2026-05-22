# -*- coding: utf-8 -*-
# Create Date:2026/5/11
# Author: dengwanpeng

"""项目根定位与运行时产物目录解析（多模块共用）。

设计要点：
- 本 skill 是「项目内 skill」，物理位置为 `<project>/.claude/skills/api-test-E10/`。
- 项目根直接由 skill 自身位置推导：`SKILL_ROOT/../../..`。
- 不再依赖 CWD 向上搜索、也不再依赖 config.json 的 project_path 字段。
- 仍提供 on_warn/on_info callback 注入，便于 mitmdump / 独立脚本各自适配日志方式。

被以下模块共用：
- capture/capture_addon.py
- tools/match_captures.py
- tools/scan_page_api.py
- tools/preflight_check.py
"""

import os
from typing import Callable, Optional


# 仓库结构硬约束：test-automation 项目根下必有 "E10自动化" 子目录
REPO_MARKER = "E10自动化"
# skill 内运行时产物在消费方项目下的子目录名（保持不变以兼容现有 .gitignore 与历史落点）
TEMP_DIR_NAME = "api_test_dwp_temp"
# config.json 在 skill 根目录（baseurl / apiDataUpdateDate 等运行时配置仍写入此处）
CONFIG_FILENAME = "config.json"

# 工具内部默认 skill 根（skill_utils 包的上一级即 skill 根）
SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_CONFIG_PATH = os.path.join(SKILL_ROOT, CONFIG_FILENAME)

# 项目根：skill 位于 <project>/.claude/skills/api-test-E10，向上 3 层即项目根
PROJECT_ROOT = os.path.normpath(os.path.join(SKILL_ROOT, "..", "..", ".."))


LogFn = Optional[Callable[[str], None]]


def _noop(_msg: str) -> None:
    pass


def resolve_project_root(
    on_warn: LogFn = None,
    on_info: LogFn = None,
) -> Optional[str]:
    """返回项目根绝对路径。

    通过 skill 自身在 <project>/.claude/skills/api-test-E10/ 的固定位置推导项目根。
    校验：项目根下必须存在 REPO_MARKER 子目录（防御 skill 被复制到错误位置）。
    """
    warn = on_warn or _noop
    info = on_info or _noop
    if not os.path.isdir(os.path.join(PROJECT_ROOT, REPO_MARKER)):
        warn(
            f"未在推导出的项目根下找到 {REPO_MARKER} 子目录: {PROJECT_ROOT}。"
            f"请确认 skill 安装在 <project>/.claude/skills/api-test-E10/ 路径下。"
        )
        return None
    info(f"使用项目根 {PROJECT_ROOT}")
    return PROJECT_ROOT


def get_temp_dir(
    on_warn: LogFn = None,
    on_info: LogFn = None,
) -> Optional[str]:
    """返回 <project>/api_test_dwp_temp 目录绝对路径，并确保其存在。"""
    repo_root = resolve_project_root(on_warn=on_warn, on_info=on_info)
    if not repo_root:
        return None
    temp_dir = os.path.join(repo_root, TEMP_DIR_NAME)
    os.makedirs(temp_dir, exist_ok=True)
    return temp_dir
