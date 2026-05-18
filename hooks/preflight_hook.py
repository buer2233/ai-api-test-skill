# -*- coding: utf-8 -*-
# Author: dengwanpeng

"""Claude Code PreToolUse hook：在 AI 调用 Skill 工具触发 api-test-E10 时，
自动执行 tools/preflight_check.py，把输出通过 hookSpecificOutput.additionalContext
注入 AI 上下文，等价于 SKILL.md 里原本的「前置必跑 0」。

Hook I/O 协议（Claude Code 标准）：
- stdin:  JSON {tool_name, tool_input: {skill, args?}, cwd, session_id, ...}
- stdout: JSON {hookSpecificOutput: {hookEventName, additionalContext}}
- exit 0: 放行；exit 2: 阻断该工具调用

⚠️ 触发范围限制：仅在 AI 主动调 `Skill({skill: "api-test-E10"})` 时生效；
   被 `Read` / `@skill_path` / system-reminder 触发的 skill 加载不会进入这里。
"""

import json
import os
import subprocess
import sys

HOOK_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_ROOT = os.path.dirname(HOOK_DIR)
PREFLIGHT_SCRIPT = os.path.join(SKILL_ROOT, "tools", "preflight_check.py")

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return 0

    tool_input = payload.get("tool_input") or {}
    skill_name = (tool_input.get("skill") or "").strip()

    # 只拦截 api-test-E10，避免影响其他 Skill。
    should_run = skill_name == "api-test-E10"

    if not should_run:
        return 0

    cwd = payload.get("cwd") or os.getcwd()
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"

    try:
        result = subprocess.run(
            [sys.executable, PREFLIGHT_SCRIPT],
            cwd=cwd,
            text=True,
            encoding="utf-8",
            env=env,
            capture_output=True,
            timeout=120,
        )
    except Exception as e:
        # preflight 自身崩溃（脚本路径错 / 超时 / Python 缺失），不要阻断 skill
        err_ctx = f"[preflight_hook] 执行 preflight_check.py 失败: {e}"
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "additionalContext": err_ctx,
            }
        }, ensure_ascii=False))
        return 0

    output_blob = (result.stdout or "") + (result.stderr or "")
    context_text = (
        "[preflight_check] 入口前置检查结果（由 hook 自动执行，等价于 SKILL.md 原前置必跑 0）：\n"
        + output_blob.strip()
    )
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "additionalContext": context_text,
        }
    }, ensure_ascii=False))

    # preflight 失败只把诊断注入上下文，不阻断 Skill 调用。
    if result.returncode != 0:
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
