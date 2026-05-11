# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 沟通语言

**与用户沟通时一律使用简体中文**。包括但不限于：解释方案、复述需求、报告执行结果、追问澄清、insight 注释中的解释文字。代码、命令、文件名、英文专有名词保持原样不翻译。

## 仓库性质

本仓库**不是普通应用项目**，而是一个 **Claude Code Skill**（`api-test-dwp`），安装在 `~/.claude/skills/` 下。它的工作是驱动另一个消费方项目（`test-automation/E10自动化/接口自动化测试`）里的接口测试编写。绝大多数"源代码"是 Markdown 规范，只有 `tools/` 和 `capture/` 目录里有 Python。

用户触发本 skill 时，期望你把 `SKILL.md` 当作执行手册严格遵循，而不是去重构它。本仓库内的"代码改动"主要形式是文档编辑。

## 文档层级（加载顺序很重要）

文档刻意拆分，并非每次激活都全部加载：

- `SKILL.md` —— **每次会话必加载**。定义两道前置门禁（任务信息 5 项、编写方式 ①/②/③）、方式分流和核心原则。AI 行为的入口权威来源；三种方式细则按需读取 `doc/mode_*.md`。
- `README.md` —— 面向用户的快速指南。与 `SKILL.md` 部分内容重叠。修改策略时**先改 `SKILL.md`**，再把用户可见的部分同步到 `README.md`。
- `python tools/scan_page_api.py`：刷新 `tools/page_api_index.sqlite3` 接口索引。
- `doc/mode_capture_driven.md` / `doc/mode_reference_case.md` / `doc/mode_curl_manual.md` —— 三种接口自动化编写方案，选定方式后必须按需读取对应文件。
- `doc/coding_style_guide.md` —— **按需加载**，仅在编写接口方法 / 用例代码前 Read。
- `doc/high_frequency_experience.md` —— 仅在踩到对应坑（Codex apply_patch、`show_list`、参数化与断言同步等）时加载。
- `flow_chart/flow.md` 与同目录 PNG —— Mermaid 源码与导出图。`flow.md` 实质变化时才更新 PNG。

避免在多个文档间复制策略。这种拆分的目的就是让 `SKILL.md` 保持每次会话固定加载、其余按需拉取。

## 项目根定位架构（最不显眼的要点）

本 skill 是**全局安装**，但作用于**用户当前所在的消费方项目**。定位项目根采用**两段式**策略，全部封装在 `utils/project_root.py`，被 `capture/capture_addon.py`、`tools/match_captures.py`、`tools/scan_page_api.py` 复用：

1. **优先读 `config.json` 的 `project_path` 字段**（严格 5 条校验：存在 / 解析成功 / 非空 / 绝对路径 / 真实目录 / 含 `E10自动化` 子目录），命中即作为 `repo_root`。AI 在前置 A 校验通过时会写入该字段，详见 `SKILL.md` 「校验通过后立即固化项目根」。
2. **fallback 到 CWD 向上搜索** `E10自动化` 子目录（最多 10 层）。`utils.project_root.find_repo_root` 实现该逻辑。

剩余两条仍然成立：

- 运行时产物（抓包产生的 `latest.jsonl`、match 产生的 `capture_selection.md`）写入**消费方项目**的 `api_test_dwp_temp/`，**绝不**写入 skill 自身目录。
- 与之相反，`tools/page_api_index.sqlite3` **纳入 skill 版本管理**——它是全局 SQLite 接口覆盖索引，主要由 `scan_page_api.py` 扫描生成。

排查"工具找不到文件"问题时，先检查 `config.json` 的 `project_path` 是否正确；其次再看 CWD 是否处在含 `E10自动化` 子目录的树中。

## 复用代码必须放在 utils/（硬规则）

**任何被两个及以上模块复用的基础函数 / 常量 / 工具类，统一放在 `utils/` 下，不得在调用方文件内复制粘贴**。这条规则覆盖：

- 跨模块共用的纯函数（如项目根定位、路径规范化、URL 解析等）
- 跨模块共用的配置常量（如 `REPO_MARKER = "E10自动化"`、`TEMP_DIR_NAME = "api_test_dwp_temp"`）
- 与运行时环境无关的解析 / 校验逻辑

当你发现某段逻辑要在第二处使用时：

1. 立刻把它抽进 `utils/` 下合适的模块（按职责命名，如 `utils/project_root.py`、`utils/url_parse.py`），**不要在新位置复制一份**。
2. 调用方通过 `sys.path.insert(0, _SKILL_ROOT)` + `from utils.xxx import yyy` 引用——`_SKILL_ROOT` 由 `os.path.abspath(__file__)` 向上推算两层，**不要依赖 CWD**。
3. 涉及日志输出的工具函数（如读 config 失败时的 warn），通过 **callback 注入**（`on_warn` / `on_info` 参数）解耦——utils 本身不依赖 `mitmproxy.ctx.log` 或 `print(sys.stderr)`，由调用方各自传 lambda 适配。
4. 不在 utils 内引入任何重量级第三方依赖；只用标准库 + 项目已直接依赖的库。

发现仓库内现有重复实现却没放进 utils 的，按上述规则补救。

## 任何编写工作前的两道强制门禁

由 `SKILL.md` 强制执行，不得绕过：

1. **门禁 A —— 5 项任务信息**（见 `SKILL.md` “前置必填 A”）。用户必须提供 `[接口方法文件]` / `[接口方法位置]` / `[接口用例文件]` / `[接口用例位置]` / `[用例名]`。两个“方法”字段可以**同时**填“当前用例无新增接口”，但不能只填一个。缺任意一项 → 原文返回打回模板并停止。
2. **门禁 B —— 编写方式**（见 `SKILL.md` “前置必填 B”）。三选一（①抓包驱动 / ②参考已有用例 / ③cURL 手工）。任务里有明确信号时自动推断；否则照抄三选一菜单。所选方式与任务信息记入 TodoWrite 首项。

纯查询 / 诊断 / 工具状态查询类任务可豁免；只要触及接口方法或用例代码即必须走门禁。

## 常用命令

以下命令默认在本 skill 目录（`api-test-dwp/`）下执行：

```bash
# 抓包服务（mitmproxy 监听 12138）—— 方式①使用
capture/start.bat                     # 启动（前台）
capture/stop.bat                      # 停止
capture/restart.bat                   # 停止 12138 后等待 1 秒并重启
python tools/check_capture_server.py  # 退出码 0=RUNNING、1=NOT_RUNNING、2=PORT_OCCUPIED

# 扫描全局 page_api URL（写入 tools/page_api_index.sqlite3）
python tools/scan_page_api.py         # 增量（按 mtime）
python tools/scan_page_api.py --full  # 全量重扫

# 用抓包 JSONL 与索引比对，生成勾选草稿
python tools/match_captures.py
python tools/match_captures.py --jsonl path/to/latest.jsonl
```

消费方 pytest 闭环（与编写方式无关，需在消费方仓库内执行）：

- 工作目录：`<消费方>/E10自动化/接口自动化测试`
- `PYTHONPATH` 需同时包含上述目录与其下 `test_case` 子目录
- 跑单个用例：进入工作目录后执行 `pytest -k <用例名>`
- 闭环契约见 `SKILL.md` “核心原则 → 测试必须闭环”——执行命令、关键日志、最终结果三项缺一不可，否则不能宣布完成。

## 本仓库特有的编辑规则

- **Python 源文件（`tools/*.py`、`capture/*.py`）必须 UTF-8 无 BOM**。本 skill 自身的 `SKILL.md` 核心原则 #2 同样适用于 skill 自己——Windows + 中文路径下 Codex / `apply_patch` 经常引入 BOM 或 `???` 乱码。任何编辑后必须重新 Read 文件，确认中文正常显示且无前导 `\ufeff` 字节。
- 修改 `SKILL.md` 策略时，**同步检查 `README.md` 和 `doc/` 下对应方案文件** 是否需要跟进（三方式表格、5 项任务信息清单、目录结构块这几处刻意重复）。
- `tools/page_api_index.sqlite3` 已纳入版本管理。如果你在消费方项目里手工新增接口方法，必须**在同一变更集里**更新该 SQLite 索引。这是 SKILL.md 核心原则 #3 的硬性要求。
- 不要随意往 `capture/` 添加文件——它会被 `mitmdump -s capture_addon.py` 加载，任何 import 期错误都会让抓包流程失败。

## 文件布局

```
api-test-dwp/
├── README.md                     # 本文件（用户快速指南）
├── SKILL.md                      # AI 执行规范入口（前置门禁 + 方式分流）
├── doc/                          # 按需加载的拆分方案与辅助规范
│   ├── mode_capture_driven.md     # 方式1：抓包驱动
│   ├── mode_reference_case.md     # 方式2：参考已有用例
│   ├── mode_curl_manual.md        # 方式3：cURL 手工
│   ├── coding_style_guide.md      # 接口方法/用例编码风格规范
│   └── high_frequency_experience.md # 高频踩坑经验
├── .gitignore                    # 忽略运行时产物
├── flow_chart/                   # 流程图（Mermaid 源码 + 导出 PNG）
│   ├── flow.md                   # 完整流程图与决策树（Mermaid 源码）
│   ├── 1.主流程图.png
│   ├── 2.前置操作的门禁要求.png
│   ├── 3.推荐方式1-抓包驱动.png
│   ├── 4.推荐方式2-参考已有用例.png
│   ├── 5.补充方式3-手工复制cURL.png
│   └── 6.pytest执行闭环.png
├── capture/                      # 抓包底座（方式①）
│   ├── README.md                 # 抓包配置详细指引（证书安装等）
│   ├── start.bat                 # 一键启动 12138
│   ├── stop.bat                  # 停止 12138 进程
│   ├── restart.bat               # 停止 12138 后等待 1 秒并重启
│   ├── capture_addon.py          # mitmdump 插件（过滤 + 落盘 JSONL）
│   └── allowed_prefixes.txt      # 用户可扩展的 URL 过滤前缀
├── tools/                        # 索引与匹配工具（三方式共用）
│   ├── scan_page_api.py          # 扫描 page_api 生成索引
│   ├── match_captures.py         # 抓包 vs 索引 → 勾选草稿
│   ├── check_capture_server.py   # 检测 12138 抓包服务器状态
│   └── page_api_index.sqlite3    # SQLite 全局接口覆盖文档（纳入版本管理）
├── utils/                        # 多模块共用的基础函数（复用规则见 CLAUDE.md / AGENTS.md）
│   ├── project_root.py           # 项目根定位 + config.json 解析
│   ├── common_function.py        # 通用配置更新等共享方法
│   ├── api_index_db.py           # SQLite 索引读写
│   └── api_path_match.py         # 抓包路径匹配规则
└── config.json                   # 运行时配置（AI 写入 project_path / baseurl）
```

## 其它需要准备的规则
1. 新增python文件时,文件最前面都需要加上如下内容:
```python
# -*- coding: utf-8 -*-
# Author: dengwanpeng
```
2. 无论是AGENTS.md还是CLAUDE.md文件修改，都需要同步的修改另外一个文件，两个文件保持一致。
