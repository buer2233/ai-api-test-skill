# -*- coding: utf-8 -*-
# Author: dengwanpeng

"""按 config.json 构造 pytest 执行命令。"""

import os
from typing import Optional

from skill_utils.config_loader import load_config


def _powershell_quote(value: object) -> str:
    return str(value).replace('"', '`"')


def build_pytest_command(target: str, config_path: Optional[str] = None, shell: Optional[str] = None) -> str:
    config = load_config(config_path)
    pytest_cmd = config.pytest_command_template.format(target=target)
    shell_name = (shell or ("powershell" if os.name == "nt" else "bash")).lower()
    if shell_name in {"powershell", "pwsh"}:
        workdir = _powershell_quote(config.pytest_workdir)
        pythonpath = _powershell_quote(config.pytest_pythonpath)
        return f'Set-Location -LiteralPath "{workdir}"; $env:PYTHONPATH="{pythonpath}"; {pytest_cmd}'
    if shell_name == "bash":
        return (
            f'cd "{config.pytest_workdir}" && '
            f'PYTHONPATH="{config.pytest_pythonpath}" '
            f"{pytest_cmd}"
        )
    raise ValueError(f"不支持的 shell: {shell}")
