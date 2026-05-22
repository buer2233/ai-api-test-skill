# -*- coding: utf-8 -*-
# Create Date:2026/5/11
# Author: dengwanpeng

"""api-test-E10 共享工具包。

放置规则：任何被两个及以上模块复用的基础函数/常量，统一放在本包下，
不要在调用方文件内复制粘贴。详见 CLAUDE.md / AGENTS.md 的复用规则。

为什么叫 `skill_utils` 而不是 `utils`？
- 调用方通过 `sys.path.insert(0, _SKILL_ROOT)` 把 skill 根目录加进 sys.path 最前面；
- 消费方项目 `E10自动化/接口自动化测试` 下也有同名 `utils` 包；
- 用更独特的名字可避免两个 `utils` 互相覆盖造成的难以排查的 import 错误。

公开 API 一览（详见各模块 docstring）：

- 来自 `project_root`：
    REPO_MARKER / TEMP_DIR_NAME / CONFIG_FILENAME
    SKILL_ROOT / DEFAULT_CONFIG_PATH / PROJECT_ROOT
    resolve_project_root / get_temp_dir

- 来自 `common_function`：
    update_skill_config

- 来自 `api_index_db`：
    DB_FILENAME
    get_default_db_path / connect / ensure_schema
    replace_index / insert_methods / update_method
    is_empty / existing_url_method_pairs
    load_methods / load_metadata

- 来自 `api_path_match`：
    MATCH_RULES / api_path_matches
"""

# --- project_root ---------------------------------------------------------
from skill_utils.project_root import (  # noqa: F401
    REPO_MARKER,
    TEMP_DIR_NAME,
    CONFIG_FILENAME,
    SKILL_ROOT,
    DEFAULT_CONFIG_PATH,
    PROJECT_ROOT,
    resolve_project_root,
    get_temp_dir,
)

# --- common_function ------------------------------------------------------
from skill_utils.common_function import (  # noqa: F401
    update_skill_config,
)

# --- api_index_db ---------------------------------------------------------
from skill_utils.api_index_db import (  # noqa: F401
    DB_FILENAME,
    get_default_db_path,
    connect,
    ensure_schema,
    replace_index,
    insert_methods,
    update_method,
    is_empty,
    existing_url_method_pairs,
    load_methods,
    load_metadata,
)

# --- api_path_match -------------------------------------------------------
from skill_utils.api_path_match import (  # noqa: F401
    MATCH_RULES,
    api_path_matches,
)


__all__ = [
    # project_root
    "REPO_MARKER",
    "TEMP_DIR_NAME",
    "CONFIG_FILENAME",
    "SKILL_ROOT",
    "DEFAULT_CONFIG_PATH",
    "PROJECT_ROOT",
    "resolve_project_root",
    "get_temp_dir",
    # common_function
    "update_skill_config",
    # api_index_db
    "DB_FILENAME",
    "get_default_db_path",
    "connect",
    "ensure_schema",
    "replace_index",
    "insert_methods",
    "update_method",
    "is_empty",
    "existing_url_method_pairs",
    "load_methods",
    "load_metadata",
    # api_path_match
    "MATCH_RULES",
    "api_path_matches",
]
