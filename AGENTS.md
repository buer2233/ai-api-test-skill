# Repository Guidelines

## 语言要求
默认使用简体中文进行文档编写、说明输出、评审备注与协作沟通。仅在用户明确要求英文，或外部规范强制要求英文时，才切换语言。

## 项目结构与模块组织
本仓库用于维护 `api-test-dwp` 接口自动化 Skill。核心执行规范放在 `SKILL.md`，面向使用者的快速说明放在 `README.md`，编码约束与经验总结分别放在 `coding_style_guide.md` 和 `high_frequency_experience.md`。流程图相关文件集中在 `flow_chart/`，抓包能力放在 `capture/`，复用型 Python 工具放在 `tools/`。不要提交运行期产物，例如 `capture/latest.jsonl`、勾选草稿，或目标项目 `api_test_dwp_temp/` 下的临时文件。

## 构建、测试与开发命令
本仓库没有独立构建步骤，日常工作以维护文档和脚本为主。
- `python tools/check_capture_server.py`：检查本地 `12138` 端口上的 mitmproxy 抓包服务是否可用。
- `python tools/scan_page_api.py`：刷新 `tools/page_api_index.json` 接口索引。
- `python tools/match_captures.py`：将抓包结果转换为可勾选的 Markdown 草稿。
- `mitmdump -s capture/capture_addon.py --listen-port 12138`：手动启动抓包服务。
- `python -m py_compile tools\scan_page_api.py`：对修改过的 Python 工具做快速语法校验。

## 编码风格与命名约定
所有文件统一使用 UTF-8 编码。Markdown 内容保持简洁、直接，并与现有中文说明风格一致。Python 脚本遵循当前仓库既有风格：4 空格缩进、文件名使用 `snake_case`、函数职责单一、避免引入不必要依赖。生成产物和索引文件名称保持稳定，例如 `page_api_index.json`、`latest.jsonl`、`capture_selection.md`。

## 测试规范
优先做最小范围验证。修改 Python 工具后，先对变更文件执行 `python -m py_compile`，再按实际影响运行对应脚本。涉及抓包流程时，应验证 `capture/start.bat` 或等价 `mitmdump` 命令可以正常启动，并确认 `tools/match_captures.py` 仍能生成符合预期的 Markdown 输出。若依赖特定环境、代理或证书配置，需在 PR 中明确说明。

## 提交与合并请求规范
最近提交历史以中文短句为主，常见前缀包括 `修复：`、`重构：`、`文档优化：`。提交信息应聚焦单一目的，明确说明对使用流程或工具行为的影响。PR 至少应包含：变更目的、影响路径、已执行的验证命令，以及在修改 Markdown 产物、流程图或抓包行为时附上示例输出。

## Agent 维护说明
`SKILL.md` 是执行流程的唯一事实来源，修改工作流时需同步更新 `README.md`、`coding_style_guide.md` 以及相关流程图。凡是调整贡献方式、命令入口或脚本行为，必须在同一个 PR 中同时更新面向人的说明文档与实际工具脚本，避免文档与实现脱节。
