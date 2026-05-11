# -*- coding: utf-8 -*-
# Create Date:2026/5/11
# Author: dengwanpeng

"""
存放当前SKILL内的所有全局通用的方法

已有的全局通用方法：
- update_skill_config：通用更新 skill 根目录 config.json 的方法。

"""

import json
import os
from typing import Callable, Optional

from utils.project_root import DEFAULT_CONFIG_PATH


LogFn = Optional[Callable[[str], None]]


def _noop(_msg: str) -> None:
    pass


def update_skill_config(
    update_config: dict,
    config_path: str = DEFAULT_CONFIG_PATH,
    on_warn: LogFn = None,
    on_info: LogFn = None,
) -> bool:
    """通用更新 skill 根目录 config.json 的方法。"""
    warn = on_warn or _noop
    info = on_info or _noop
    if not isinstance(update_config, dict):
        warn("update_config 必须是 dict，已跳过 config.json 更新")
        return False

    config_data = {}
    if os.path.isfile(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config_data = json.load(f)
        except Exception as e:
            warn(f"读取 config.json 失败，将重建配置: {e}")
            config_data = {}
    if not isinstance(config_data, dict):
        warn("config.json 内容不是对象，将重建配置")
        config_data = {}

    config_data.update(update_config)
    try:
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config_data, f, ensure_ascii=False, indent=2)
            f.write("\n")
        info(f"已更新 config.json: {', '.join(update_config.keys())}")
        return True
    except Exception as e:
        warn(f"写入 config.json 失败: {e}")
        return False
