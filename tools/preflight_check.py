# -*- coding: utf-8 -*-
# Author: dengwanpeng

"""api-test-dwp Skill 前置快速检查。

设计原则：
- 入口动作，必须够快；任何"重操作"放到下游脚本里。
- 输出文本面向 AI 直接读取，所以提示语必须稳定、可识别。

目前只做一件事：
  根据 config.json 中的 apiDataUpdateDate 判断是否需要刷新接口索引：
    - delta ≤ 7 天      → 提示一周内最新，直接返回
    - delta > 7 天      → 调 scan_page_api.py 增量扫描，把新增接口列表透传给上层
    - 当前日期 < 更新日 → 配置写错，回执让用户修正

后续可以追加更多前置检查，但务必保持轻量。
"""

import json
import os
import subprocess
import sys
from datetime import datetime


# Windows + 中文环境下，默认 stdout/stderr 走 cp936，子进程被父进程
# 以 utf-8 捕获时会出现 UnicodeDecodeError。这里统一改为 utf-8 输出。
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass


TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
_SKILL_ROOT = os.path.dirname(TOOLS_DIR)
if _SKILL_ROOT not in sys.path:
    sys.path.insert(0, _SKILL_ROOT)

from utils.project_root import DEFAULT_CONFIG_PATH  # noqa: E402


DATE_FIELD = "apiDataUpdateDate"
MAX_INTERVAL_DAYS = 7
DATE_FORMATS = ("%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d")


def _load_config() -> dict:
    if not os.path.isfile(DEFAULT_CONFIG_PATH):
        return {}
    try:
        with open(DEFAULT_CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"读取 config.json 失败: {e}", file=sys.stderr)
        return {}
    return data if isinstance(data, dict) else {}


def _parse_date(value: str):
    value = (value or "").strip()
    if not value:
        return None
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    return None


def _invalid_date_msg(value: str) -> str:
    return f"config.json 中填写的 {DATE_FIELD} 时间有误，请检查并改正：{value!r}"


def _run_scan() -> int:
    """调用 scan_page_api.py；stdout/stderr 直接透传，保留 new_methods 清单。"""
    scan_script = os.path.join(TOOLS_DIR, "scan_page_api.py")
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    result = subprocess.run(
        [sys.executable, scan_script],
        cwd=_SKILL_ROOT,
        text=True,
        encoding="utf-8",
        env=env,
        capture_output=True,
    )
    if result.stdout:
        sys.stdout.write(result.stdout)
        if not result.stdout.endswith("\n"):
            sys.stdout.write("\n")
    if result.stderr:
        sys.stderr.write(result.stderr)
        if not result.stderr.endswith("\n"):
            sys.stderr.write("\n")
    return result.returncode


def main() -> int:
    config_data = _load_config()
    raw = config_data.get(DATE_FIELD, "")
    update_date = _parse_date(raw)
    if not update_date:
        print(_invalid_date_msg(raw))
        return 1

    today = datetime.now().date()
    delta_days = (today - update_date).days
    if delta_days < 0:
        # 当前日期早于 apiDataUpdateDate，配置必然有误
        print(_invalid_date_msg(raw))
        return 1
    if delta_days <= MAX_INTERVAL_DAYS:
        print("数据库中的接口为一周内的最新数据，无需更新。")
        return 0

    code = _run_scan()
    if code != 0:
        print("接口数据库更新失败，请根据上方日志处理。", file=sys.stderr)
        return code
    # scan 已经打印过 [scan_page_api] recent_new_methods 块，这里再补一条人类可读提示
    print("本次扫描出的新增接口信息见上方 [scan_page_api] recent_new_methods 输出。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
