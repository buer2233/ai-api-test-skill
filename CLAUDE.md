# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 沟通语言

**与用户沟通时一律使用简体中文**。包括但不限于：解释方案、复述需求、报告执行结果、追问澄清、insight 注释中的解释文字。代码、命令、文件名、英文专有名词保持原样不翻译。

## 仓库性质

本目录是一个 **Claude Code Skill**（`api-test-E10`），**项目级**，固定安装在 `test-automation` 仓库的 `.claude/skills/api-test-E10/` 路径下，随仓库一起分发。它的工作是驱动同一仓库内 `E10自动化/接口自动化测试/` 的接口测试编写。绝大多数"源代码"是 Markdown 规范，只有 `tools/`、`capture/`、`skill_utils/`、`hooks/` 目录里有 Python。

用户触发本 skill 时，期望你把 `SKILL.md` 当作执行手册严格遵循，而不是去重构它。本仓库内的"代码改动"主要形式是文档编辑。

## 文档层级（加载顺序很重要）

文档刻意拆分，并非每次激活都全部加载：

- `SKILL.md` —— **每次会话必加载**。保留两道前置门禁的**触发条件 + 必填字段 + 判定边界**、方式分流、核心原则纲领。AI 行为的入口权威来源；详细执行手册按需 Read `doc/preflight_gates.md` 与 `doc/core_principles.md`，方式细则按需 Read `doc/mode_*.md`。
- `README.md` —— 面向用户的快速指南。与 `SKILL.md` 部分内容重叠。修改策略时**先改 `SKILL.md`**，再把用户可见的部分同步到 `README.md`。
- `python tools/scan_page_api.py`：刷新 `tools/page_api_index.sqlite3` 接口索引。
- `doc/preflight_gates.md` —— **按需加载**，前置门禁详细执行手册（打回模板、三选一菜单等）。SKILL.md 触发前置 A/B 时必须 Read。
- `doc/core_principles.md` —— **按需加载**，核心原则 1-5 的详细规则（查重流程、索引维护、pytest 闭环细节等）。SKILL.md 触发对应原则时按需 Read。
- `doc/mode_capture_driven.md` / `doc/mode_reference_case.md` / `doc/mode_curl_manual.md` —— 三种接口自动化编写方案，选定方式后必须按需读取对应文件。
- `doc/coding_style_guide.md` —— **按需加载**，仅在编写接口方法 / 用例代码前 Read。
- `doc/high_frequency_experience.md` —— 仅在踩到对应坑（Codex apply_patch、`show_list`、参数化与断言同步等）时加载。
- `flow_chart/flow.md` 与同目录 PNG —— Mermaid 源码与导出图。`flow.md` 实质变化时才更新 PNG。

避免在多个文档间复制策略。这种拆分的目的就是让 `SKILL.md` 保持每次会话固定加载、其余按需拉取。

## 项目根定位架构（最不显眼的要点）

本 skill 物理位置固定为 `<project>/.claude/skills/api-test-E10/`。**项目根直接由 skill 自身位置推导**：`SKILL_ROOT/../../..`。统一封装在 `skill_utils/project_root.py`，被 `capture/capture_addon.py`、`tools/match_captures.py`、`tools/scan_page_api.py`、`tools/preflight_check.py` 复用。

校验：推导出的项目根下必须存在 `E10自动化` 子目录，否则报错并拒绝继续工作（防御 skill 被复制到错误位置）。

不再使用 `config.json.project_path` 字段，也不再有「CWD 向上 10 层搜索 `E10自动化`」的 fallback 逻辑。`config.json` 仅保留 `baseurl` / `apiDataUpdateDate` / `multi_capture` 等运行时配置。

剩余两条仍然成立：

- 运行时产物（抓包产生的 `latest.jsonl`、match 产生的 `capture_selection.md`）写入**项目根**的 `api_test_dwp_temp/`，**绝不**写入 skill 自身目录。
- 与之相反，`tools/page_api_index.sqlite3` 与本 skill 全部源码一起**纳入版本管理**。

排查"工具找不到文件"问题时，先确认 skill 仍处在 `<project>/.claude/skills/api-test-E10/` 路径下，其上 3 层即项目根，并且项目根下确实有 `E10自动化` 子目录。

## 复用代码必须放在 skill_utils/（硬规则）

**任何被两个及以上模块复用的基础函数 / 常量 / 工具类，统一放在 `skill_utils/` 下，不得在调用方文件内复制粘贴**。这条规则覆盖：

- 跨模块共用的纯函数（如项目根定位、路径规范化、URL 解析等）
- 跨模块共用的配置常量（如 `REPO_MARKER = "E10自动化"`、`TEMP_DIR_NAME = "api_test_dwp_temp"`）
- 与运行时环境无关的解析 / 校验逻辑

当你发现某段逻辑要在第二处使用时：

1. 立刻把它抽进 `skill_utils/` 下合适的模块（按职责命名，如 `skill_utils/project_root.py`、`skill_utils/url_parse.py`），**不要在新位置复制一份**。
2. 调用方通过 `sys.path.insert(0, _SKILL_ROOT)` + `from skill_utils.xxx import yyy` 引用——`_SKILL_ROOT` 由 `os.path.abspath(__file__)` 向上推算两层，**不要依赖 CWD**。
3. 涉及日志输出的工具函数（如读 config 失败时的 warn），通过 **callback 注入**（`on_warn` / `on_info` 参数）解耦——`skill_utils` 本身不依赖 `mitmproxy.ctx.log` 或 `print(sys.stderr)`，由调用方各自传 lambda 适配。
4. 不在 `skill_utils` 内引入任何重量级第三方依赖；只用标准库 + 项目已直接依赖的库。

发现仓库内现有重复实现却没放进 `skill_utils` 的，按上述规则补救。

## 任何编写工作前的两道强制门禁

由 `SKILL.md` 强制执行，不得绕过：

1. **门禁 A —— 5 项任务信息**（见 `SKILL.md` "前置必填 A"）。用户必须提供 `[接口方法文件]` / `[接口方法位置]` / `[接口用例文件]` / `[接口用例位置]` / `[用例名]`。两个"方法"字段可以**同时**填"当前用例无新增接口"，但不能只填一个。缺任意一项 → 原文返回打回模板并停止。
2. **门禁 B —— 编写方式**（见 `SKILL.md` "前置必填 B"）。三选一（①抓包驱动 / ②参考已有用例 / ③cURL 手工）。任务里有明确信号时自动推断；否则照抄三选一菜单。所选方式与任务信息记入 TodoWrite 首项。

纯查询 / 诊断 / 工具状态查询类任务可豁免；只要触及接口方法或用例代码即必须走门禁。

## 常用命令

以下命令默认在本 skill 目录（`.claude/skills/api-test-E10/`）下执行：

```bash
# 抓包服务（mitmproxy 监听 12138）—— 方式①使用
capture/start.bat                     # 启动（前台）
capture/stop.bat                      # 停止
capture/restart.bat                   # 停止 12138 后等待 1 秒并重启
python tools/check_capture_server.py  # 退出码 0=RUNNING、1=NOT_RUNNING、2=PORT_OCCUPIED

# 入口前置：接口数据时效检查（skill 触发后第一步必跑）
python tools/preflight_check.py

# 扫描 page_api URL（写入 tools/page_api_index.sqlite3）
python tools/scan_page_api.py         # 自动模式：库空全量重建（id 从 1 起）；库非空时按 Create Date 近 30 天 + (api_url, method) diff 增量追加
python tools/scan_page_api.py --full  # 强制全量重建（清空 + 重写，id 重新从 1）

# 用抓包 JSONL 与索引比对，生成勾选草稿
python tools/match_captures.py
python tools/match_captures.py --jsonl path/to/latest.jsonl
```

`scan_page_api.py` 已覆盖三类 HTTP method 写法：`requests.<verb>(...)` / `requests.request("VERB", ...)` / `self.send_msg("get"|"post", ...)`。method 在入库前统一 `upper()`。

`preflight_check.py` 仅做日期比对：
- 当前时间与 `config.json.apiDataUpdateDate` 相差 ≤ 7 天 → 提示一周内最新
- > 7 天 → 自动调 `scan_page_api.py`，并写回 `apiDataUpdateDate=今天`
- 当前日期早于 `apiDataUpdateDate` → 原文返回让用户改正

项目内 pytest 闭环（与编写方式无关，需在项目仓库内执行）：

- 工作目录：`<project>/E10自动化/接口自动化测试`
- `PYTHONPATH` 需同时包含上述目录与其下 `test_case` 子目录
- 跑单个用例：进入工作目录后执行 `pytest -k <用例名>`
- 闭环契约见 `SKILL.md` "核心原则 → 测试必须闭环"——执行命令、关键日志、最终结果三项缺一不可，否则不能宣布完成。

## 本目录特有的编辑规则

- **Python 源文件（`tools/*.py`、`capture/*.py`、`skill_utils/*.py`、`hooks/*.py`）必须 UTF-8 无 BOM**。本 skill 自身的 `SKILL.md` 核心原则 #2 同样适用于 skill 自己——Windows + 中文路径下 Codex / `apply_patch` 经常引入 BOM 或 `???` 乱码。任何编辑后必须重新 Read 文件，确认中文正常显示且无前导 `﻿` 字节。
- 修改 `SKILL.md` 策略时，**同步检查 `README.md` 和 `doc/` 下对应方案文件** 是否需要跟进（三方式表格、5 项任务信息清单、目录结构块这几处刻意重复）。
- `tools/page_api_index.sqlite3` 已纳入版本管理。如果你在项目内手工新增接口方法，必须**在同一变更集里**更新该 SQLite 索引。这是 SKILL.md 核心原则 #3 的硬性要求。
- 不要随意往 `capture/` 添加文件——它会被 `mitmdump -s capture_addon.py` 加载，任何 import 期错误都会让抓包流程失败。

## 文件布局

```
.claude/skills/api-test-E10/
├── README.md                     # 用户快速指南
├── SKILL.md                      # AI 执行规范入口（前置门禁 + 方式分流）
├── doc/                          # 按需加载的拆分方案与辅助规范
│   ├── preflight_gates.md         # 前置门禁详细执行手册
│   ├── core_principles.md         # 核心原则 1-5 详细规则
│   ├── mode_capture_driven.md     # 方式1：抓包驱动
│   ├── mode_reference_case.md     # 方式2：参考已有用例
│   ├── mode_curl_manual.md        # 方式3：cURL 手工
│   ├── coding_style_guide.md      # 接口方法/用例编码风格规范
│   └── high_frequency_experience.md # 高频踩坑经验
├── .gitignore                    # 忽略运行时产物
├── flow_chart/                   # 流程图（Mermaid 源码 + 导出 PNG）
│   ├── flow.md
│   ├── 1.主流程图.png
│   ├── 2.前置操作的门禁要求.png
│   ├── 3.推荐方式1-抓包驱动.png
│   ├── 4.推荐方式2-参考已有用例.png
│   ├── 5.补充方式3-手工复制cURL.png
│   └── 6.pytest执行闭环.png
├── capture/                      # 抓包底座（方式①）
│   ├── README.md
│   ├── start.bat
│   ├── stop.bat
│   ├── restart.bat
│   ├── capture_addon.py
│   └── allowed_prefixes.txt
├── tools/                        # 索引与匹配工具（三方式共用）
│   ├── preflight_check.py        # skill 入口前置：接口数据时效检查
│   ├── scan_page_api.py          # 扫描 page_api 生成索引
│   ├── match_captures.py         # 抓包 vs 索引 → 勾选草稿
│   ├── check_capture_server.py   # 检测 12138 抓包服务器状态
│   └── page_api_index.sqlite3    # SQLite 接口覆盖文档（纳入版本管理）
├── skill_utils/                        # 多模块共用的基础函数
│   ├── project_root.py           # 项目根定位（由 skill 自身位置推导）
│   ├── common_function.py        # 通用配置更新等共享方法
│   ├── api_index_db.py           # SQLite 索引读写
│   └── api_path_match.py         # 抓包路径匹配规则
├── hooks/                        # Claude Code PreToolUse hook
│   └── preflight_hook.py
└── config.json                   # 运行时配置：baseurl / apiDataUpdateDate
```

## 其它需要准备的规则
1. 新增python文件时,文件最前面都需要加上如下内容:
```python
# -*- coding: utf-8 -*-
# Author: dengwanpeng
```
2. 无论是AGENTS.md还是CLAUDE.md文件修改，都需要同步的修改另外一个文件，两个文件保持一致。
