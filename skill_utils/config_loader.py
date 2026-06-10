# -*- coding: utf-8 -*-
# Author: dengwanpeng

"""读取通用 pytest + requests 接口自动化项目配置。"""

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional


SKILL_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG_PATH = SKILL_ROOT / "config.json"


class ConfigError(RuntimeError):
    """配置缺失或不合法。"""


@dataclass(frozen=True)
class SkillConfig:
    raw: Dict[str, Any]
    config_path: Path
    project_root: Path
    api_method_dirs: List[Path]
    test_case_dirs: List[Path]
    pytest_workdir: Path
    runtime_temp_dir: Path
    api_scan_dirs: List[Path]
    api_index_db_path: Path
    extract_rules_path: Path
    pytest_pythonpath: str
    pytest_command_template: str


def _read_json(config_path: Path) -> Dict[str, Any]:
    if not config_path.is_file():
        raise ConfigError(
            f"未找到 config.json: {config_path}。请先按模板初始化 project_root、paths、pytest 和 api_index 配置。"
        )
    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ConfigError(f"config.json 不是合法 JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise ConfigError("config.json 顶层必须是对象")
    return data


def _as_dict(data: Dict[str, Any], key: str) -> Dict[str, Any]:
    value = data.get(key) or {}
    if not isinstance(value, dict):
        raise ConfigError(f"config.json 中 {key} 必须是对象")
    return value


def _as_list(value: Any, key: str) -> List[str]:
    if value is None:
        return []
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ConfigError(f"config.json 中 {key} 必须是字符串数组")
    return value


def _resolve_under(base: Path, value: str) -> Path:
    path = Path(value)
    if not path.is_absolute():
        path = base / path
    return path.resolve()


def _resolve_existing_dirs(base: Path, values: List[str], key: str) -> List[Path]:
    resolved = [_resolve_under(base, item) for item in values]
    missing = [str(path) for path in resolved if not path.is_dir()]
    if missing:
        raise ConfigError(f"config.json 中 {key} 指向的目录不存在: {', '.join(missing)}")
    return resolved


def _resolve_skill_file(value: str, default: str) -> Path:
    raw = value or default
    path = Path(raw)
    if not path.is_absolute():
        path = SKILL_ROOT / path
    return path.resolve()


def load_config(config_path: Optional[str] = None) -> SkillConfig:
    """读取并校验 skill 配置。

    用户必须配置 project_root。除索引库与内部规则文件外，项目路径均按
    project_root 解析；索引库和规则文件按 skill 根目录解析，保持随 skill 管理。
    """
    cfg_path = Path(config_path).resolve() if config_path else DEFAULT_CONFIG_PATH.resolve()
    data = _read_json(cfg_path)

    project_root_raw = data.get("project_root")
    if not isinstance(project_root_raw, str) or not project_root_raw.strip():
        raise ConfigError("config.json 缺少必填字段 project_root")
    project_root = Path(project_root_raw).expanduser().resolve()
    if not project_root.is_dir():
        raise ConfigError(f"config.json 中 project_root 指向的目录不存在: {project_root}")

    paths = _as_dict(data, "paths")
    api_index = _as_dict(data, "api_index")
    pytest_cfg = _as_dict(data, "pytest")

    api_method_dirs_raw = _as_list(paths.get("api_method_dirs"), "paths.api_method_dirs")
    test_case_dirs_raw = _as_list(paths.get("test_case_dirs"), "paths.test_case_dirs")
    api_scan_dirs_raw = _as_list(api_index.get("scan_dirs"), "api_index.scan_dirs")
    if not api_scan_dirs_raw:
        api_scan_dirs_raw = api_method_dirs_raw
    if not api_scan_dirs_raw:
        raise ConfigError("config.json 缺少 api_index.scan_dirs 或 paths.api_method_dirs")

    api_method_dirs = _resolve_existing_dirs(project_root, api_method_dirs_raw, "paths.api_method_dirs")
    test_case_dirs = _resolve_existing_dirs(project_root, test_case_dirs_raw, "paths.test_case_dirs")
    api_scan_dirs = _resolve_existing_dirs(project_root, api_scan_dirs_raw, "api_index.scan_dirs")

    pytest_workdir = _resolve_under(project_root, paths.get("pytest_workdir") or ".")
    if not pytest_workdir.is_dir():
        raise ConfigError(f"config.json 中 paths.pytest_workdir 指向的目录不存在: {pytest_workdir}")

    runtime_temp_dir = _resolve_under(project_root, paths.get("runtime_temp_dir") or "api_test_dwp_temp")

    return SkillConfig(
        raw=data,
        config_path=cfg_path,
        project_root=project_root,
        api_method_dirs=api_method_dirs,
        test_case_dirs=test_case_dirs,
        pytest_workdir=pytest_workdir,
        runtime_temp_dir=runtime_temp_dir,
        api_scan_dirs=api_scan_dirs,
        api_index_db_path=_resolve_skill_file(
            api_index.get("db_path") or "",
            "tools/page_api_index.sqlite3",
        ),
        extract_rules_path=_resolve_skill_file(
            api_index.get("extract_rules_path") or "",
            "tools/api_extract_rules.json",
        ),
        pytest_pythonpath=str(pytest_cfg.get("pythonpath") or "."),
        pytest_command_template=str(pytest_cfg.get("command_template") or "pytest {target} -v --tb=short"),
    )


def get_project_root(config_path: Optional[str] = None) -> str:
    return str(load_config(config_path).project_root)


def get_runtime_temp_dir(config_path: Optional[str] = None, create: bool = False) -> str:
    temp_dir = load_config(config_path).runtime_temp_dir
    if create:
        os.makedirs(temp_dir, exist_ok=True)
    return str(temp_dir)
