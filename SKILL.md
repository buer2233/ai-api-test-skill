---
name: api-test-E10
description: 当前 test-automation 项目内置的接口自动化编写 skill，物理位置 `.claude/skills/api-test-E10/`。用于在 `\test-automation\E10自动化\接口自动化测试` 中新增、修改、补齐、迁移接口测试方法与 pytest 用例。触发场景包括：新增接口方法、新增接口测试用例、补齐参数化、修复接口断言、按指定位置插入代码、按 URL 查重复实现、处理 UTF-8 中文编码、执行 pytest 并根据真实报错循环修复直到通过。运行时产物统一放在项目根 `api_test_dwp_temp/` 目录下。
---

# api-test-E10

随 `test-automation` 项目一起分发的接口自动化编写 skill，把已验证有效的编写习惯、问题处理方式和交付格式沉淀为稳定流程。项目根直接由 skill 在 `<project>/.claude/skills/api-test-E10/` 的固定位置推导，运行时产物统一落在项目根的 `api_test_dwp_temp/` 目录下。

## 适用范围

当任务涉及在 `E10自动化/接口自动化测试/` 内**新增或修改**接口测试方法/pytest 用例时，优先使用本 skill。同样适用于按 URL 查重、处理中文编码/导入路径/登录态/返回结构差异、根据真实 pytest 报错循环修复等场景。

## 🚨 前置门禁（任何工作开始前必校验并执行）

- 必须读取并严格按照要求执行的文件：**@doc/preflight_gates.md**

## 三种用例编写方式的执行流程

### 强制按需读取门禁

进入任一种方式后，AI **必须先 Read 对应的方案文件**，再继续编写接口方法或用例：

| 方式 | 适用场景 | 必读方案文件 |
|---|---|---|
| ① 抓包驱动 | 用户选择方式1，或表达"用抓包 / 读 latest.jsonl / 已完成 UI 操作" | `doc/mode_capture_driven.md` |
| ② 参考已有用例 | 用户选择方式2，或表达"参照 / 仿照 / 复制已有用例" | `doc/mode_reference_case.md` |
| ③ cURL 手工 | 用户选择方式3，或消息中已粘贴 `curl ...` | `doc/mode_curl_manual.md` |

**硬性要求**：

- 编写任何接口方法或 pytest 用例前，必须先 Read `doc/coding_style_guide.md`
- 选定方式后，必须 Read 上表对应的 `doc/mode_*.md`，并按其中步骤执行
- 需要排查历史高频问题时，按需 Read `doc/high_frequency_experience.md`
- 不允许只凭 `SKILL.md` 的摘要执行三种方式的具体步骤

### 共用前置确认动作（进入任一种方式前执行）

- Read `[接口用例文件]`，按 `[接口用例位置]` 定位插入点上下文
- 若 `[接口方法文件]` 非"无新增接口"：Read 该文件，按 `[接口方法位置]` 定位插入点
- 检查插入点是否紧邻 `@pytest.mark.skip`
- 检查测试类前置依赖、fixture、`self.xxx` 真实实例化
- 用 `[用例名]` 作为新增用例的 docstring / 标题文本

### 流程图

Mermaid 源文件与导出 PNG 见 `flow_chart/` 目录。

## 接口方法与用例编写规范

**⚠️ 编写任何接口方法或用例代码前，AI 必须先 Read [`doc/coding_style_guide.md`](./doc/coding_style_guide.md) 并严格遵守其中所有规范。**

该文件覆盖：接口方法结构/命名/payload/取值规则，用例结构/编排模式/参数化/断言风格，以及编写前必检清单（风格对齐、接口查重、编码校验）。

## 项目内规范锚点

编写接口自动化时，优先以以下文件为第一参考（**风格模板，不是功能强绑定模板**）：

- **抓包底座**：`capture/capture_addon.py`
- **索引与匹配工具**：`tools/scan_page_api.py` / `tools/match_captures.py` / `tools/check_capture_server.py`（入口前置 `tools/preflight_check.py` 由 hook 自动执行，见前置 0）
- **全局接口覆盖文档**：`tools/page_api_index.sqlite3` —— 全局 URL 索引，扫描或 AI 新增接口后需更新（纳入版本管理）
- **运行时产物**（项目根 `api_test_dwp_temp/`）：`latest.jsonl`（抓包落盘） / `capture_selection.md`（勾选草稿）

如果用户指定了别的参考文件或明确要求"参考当前位置上下文"，则以用户要求为先。

## 核心原则（详见 @doc/core_principles.md）

1. **最小必要改动** — 只在指定位置插入，不擅自重构无关代码
2. **UTF-8 与中文安全优先** — 文件按 UTF-8 读写 + 写入后真实校验（确认中文存在、无成片问号）
3. **先复用，后新增** — 优先查 `tools/page_api_index.sqlite3`，未命中才新增；新增后必须立刻 `scan_page_api.py` 刷新
4. **以真实返回为准** — 断言基于真实接口返回，警惕"方法返回 `response`"与"返回 `response.get('data')`"两种风格
5. **测试必须闭环** — 默认必须 pytest 跑到通过；执行目录 / PYTHONPATH / 执行命令 / 关键日志 / 最终结果缺一不可

## 失败排查优先级

出现失败时，按以下顺序排查：

1. **导入路径问题**：`ModuleNotFoundError` / `ImportError` / `No module named ...`
2. **编码问题**：中文变成成片问号乱码 / 文件解析失败
3. **装饰器误挂 / 插入位置错误**
4. **fixture / 前置依赖问题**
5. **登录态 / token / 会话问题**
6. **接口真实返回与断言不匹配**
7. **接口 payload 结构不匹配**：后端 SQL 报错、字段类型错误、列表/字符串结构不一致
8. **接口方法返回层级误判**：例如某些方法返回 `response["data"]`，不是完整 `response`

> 排查后若确定为环境/网络/登录/会话问题（非代码问题），上报用户并明确说明。

历史踩坑详见 [`doc/high_frequency_experience.md`](./doc/high_frequency_experience.md)（按需加载）。

## 输出结果模板

完成任务后建议按以下结构输出：

```text
【新增接口用例】(N个)
用例名: 中文说明

【新增接口方法】(N个)
方法名: 中文说明

pytest 执行命令
...

关键日志
...

报错与修复过程
...

最终结果
...
```

### 默认返回要求

- **默认必须返回新增接口用例列表**：`新增接口用例（N个）` + `用例函数名：完整标题文本`，标题文本优先取测试函数 docstring 或用户指定标题
- **默认必须返回新增接口方法列表**：`新增接口方法（N个）` + `方法名：完整标题文本`；未新增也要明确返回 `新增接口方法（0个）`
- **默认必须返回 pytest 执行结果**：至少包含执行命令、通过/失败统计、关键报错或修复说明
- 仅当用户在当前对话中明确强调"不需要反馈新增数据列表"时，才可省略上述清单
- 输出清单时**默认不写文件位置、行号、路径**，除非用户明确要求

---

当你在当前仓库里做接口自动化编写时，把本文件视为**默认工作手册**。
