# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 沟通语言

**与用户沟通时一律使用简体中文**。包括但不限于：解释方案、复述需求、报告执行结果、追问澄清、insight 注释中的解释文字。代码、命令、文件名、英文专有名词保持原样不翻译。

## 仓库性质

本仓库**不是普通应用项目**，而是一个 **Claude Code Skill**（`api-test-dwp`），安装在 `~/.claude/skills/` 下。它的工作是驱动另一个消费方项目（`test-automation/E10自动化/接口自动化测试`）里的接口测试编写。绝大多数"源代码"是 Markdown 规范，只有 `tools/` 和 `capture/` 目录里有 Python。

用户触发本 skill 时，期望你把 `SKILL.md` 当作执行手册严格遵循，而不是去重构它。本仓库内的"代码改动"主要形式是文档编辑。

## 文档层级（加载顺序很重要）

文档刻意拆分，并非每次激活都全部加载：

- `SKILL.md` —— **每次会话必加载**。定义两道前置门禁（任务信息 5 项、编写方式 ①/②/③）、各方式执行流程、核心原则。AI 行为的唯一权威来源。
- `README.md` —— 面向用户的快速指南。与 `SKILL.md` 部分内容重叠。修改策略时**先改 `SKILL.md`**，再把用户可见的部分同步到 `README.md`。
- `coding_style_guide.md` —— **按需加载**，仅在编写接口方法 / 用例代码前 Read。`SKILL.md:301` 明确委派到本文件。
- `high_frequency_experience.md` —— 仅在踩到对应坑（Codex apply_patch、`show_list`、参数化与断言同步等）时加载。
- `flow_chart/flow.md` 与同目录 PNG —— Mermaid 源码与导出图。`flow.md` 实质变化时才更新 PNG。

避免在多个文档间复制策略。这种拆分的目的就是让 `SKILL.md` 保持每次会话固定加载、其余按需拉取。

## CWD 自适应架构（最不显眼的要点）

本 skill 是**全局安装**，但作用于**用户当前所在的消费方项目**。机制有两处：

- `tools/scan_page_api.py:46` 与 `tools/match_captures.py:30` 都定义了 `_find_repo_root(start)`，向上**最多回溯 10 层父目录**，查找名为 `E10自动化` 的子目录。这是工具无视 skill 自身位置、能精确定位消费方测试仓的方式。
- 运行时产物（抓包产生的 `latest.jsonl`、match 产生的 `capture_selection.md`）写入**消费方项目**的 `api_test_dwp_temp/`，**绝不**写入 skill 自身目录。`capture/` 内的旧产物路径与根目录的 `capture_selection.md` 都是历史残留，已纳入 `.gitignore`。
- 与之相反，`tools/page_api_index.json` **纳入 skill 版本管理**——它是全局的"URL → 方法"覆盖索引。`scan_page_api.py`（扫描）与 AI 手工编辑（新增方法后追加条目）都会更新它。

排查"工具找不到文件"问题时，第一步先确认当前 CWD 处在某个含有 `E10自动化` 子目录的树中。

## 任何编写工作前的两道强制门禁

由 `SKILL.md` 强制执行，不得绕过：

1. **门禁 A —— 5 项任务信息**（`SKILL.md:10-52`）。用户必须提供 `[接口方法文件]` / `[接口方法位置]` / `[接口用例文件]` / `[接口用例位置]` / `[用例名]`。两个"方法"字段可以**同时**填"当前用例无新增接口"，但不能只填一个。缺任意一项 → 原文返回打回模板并停止。
2. **门禁 B —— 编写方式**（`SKILL.md:54-92`）。三选一（①抓包驱动 / ②参考已有用例 / ③cURL 手工）。任务里有明确信号时自动推断；否则照抄三选一菜单。所选方式与任务信息记入 TodoWrite 首项。

纯查询 / 诊断 / 工具状态查询类任务可豁免；只要触及接口方法或用例代码即必须走门禁。

## 常用命令

以下命令默认在本 skill 目录（`api-test-dwp/`）下执行：

```bash
# 抓包服务（mitmproxy 监听 12138）—— 方式①使用
capture/start.bat                     # 启动（前台）
capture/stop.bat                      # 停止
python tools/check_capture_server.py  # 退出码 0=RUNNING、1=NOT_RUNNING、2=PORT_OCCUPIED

# 扫描全局 page_api URL（写入 tools/page_api_index.json）
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
- 闭环契约见 `SKILL.md:288-298`——执行命令、关键日志、最终结果三项缺一不可，否则不能宣布完成。

## 本仓库特有的编辑规则

- **Python 源文件（`tools/*.py`、`capture/*.py`）必须 UTF-8 无 BOM**。本 skill 自身的 `SKILL.md` 核心原则 #2 同样适用于 skill 自己——Windows + 中文路径下 Codex / `apply_patch` 经常引入 BOM 或 `???` 乱码。任何编辑后必须重新 Read 文件，确认中文正常显示且无前导 `\ufeff` 字节。
- 修改 `SKILL.md` 策略时，**同步检查 `README.md`** 是否需要跟进（三方式表格、5 项任务信息清单、目录结构块这几处刻意重复）。
- `tools/page_api_index.json` 已纳入版本管理。如果你在消费方项目里手工新增接口方法，必须**在同一变更集里**更新该 JSON 的 `methods[]` 数组与 `by_path` 映射。这是 SKILL.md 核心原则 #3 的硬性要求。
- 不要随意往 `capture/` 添加文件——它会被 `mitmdump -s capture_addon.py` 加载，任何 import 期错误都会让抓包流程失败。

## 文件布局

```
SKILL.md                         AI 执行规范（每次会话必加载）
README.md                        用户快速指南
coding_style_guide.md            接口方法/用例编码规范（按需加载）
high_frequency_experience.md     高频踩坑经验（按需加载）
flow_chart/flow.md + *.png       Mermaid 源码与 6 张子流程图
tools/
  scan_page_api.py               AST 解析消费方仓库，构建 page_api_index.json
  match_captures.py              将 latest.jsonl 与索引比对
  check_capture_server.py        探测 12138 端口的 mitmdump
  page_api_index.json            纳入版本管理的全局 URL→方法 索引
capture/
  capture_addon.py               mitmproxy 插件：按 allowed_prefixes 过滤并写 JSONL
  allowed_prefixes.txt           可由用户扩展的 URL 前缀白名单
  start.bat / stop.bat           12138 端口生命周期管理
```
