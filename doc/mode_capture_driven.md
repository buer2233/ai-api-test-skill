# 方式1：抓包驱动

> 触发条件：前置 B 选择 ①，或用户明确表达“用抓包 / 读 latest.jsonl / 已完成 UI 操作”。

## 强制读取要求

进入本方式后，AI 必须先读取：

1. `doc/coding_style_guide.md`
2. 本文件 `doc/mode_capture_driven.md`
3. 必要时读取 `capture/README.md` 排查抓包证书、代理或端口问题

## 执行步骤

1. **判断是否需要重启抓包服务**：先检查用户是否明确提及“重启抓包服务 / 重新启动抓包 / restart capture”。
2. **二选一处理抓包服务**：
   - 若用户明确提及重启抓包服务：执行 `capture/restart.bat`，该脚本会停止 `12138` 端口进程，等待 1 秒后重新执行 `capture_addon.py` 开启服务。
   - 若用户未提及重启抓包服务：执行默认检查并按需开启逻辑，即运行 `tools/check_capture_server.py`，退出码解释：
   ```text
   RUNNING (exit=0)        → 进入步骤 3
   NOT_RUNNING (exit=1)    → 后台启动 start.bat：
                             start /B cmd /c "capture\start.bat"
                             或直接：mitmdump -s capture/capture_addon.py --listen-port 12138
                             启动后等待 2 秒再次检测，仍失败 → 提示用户手动双击
   PORT_OCCUPIED (exit=2)  → 提示用户 12138 被非 mitmdump 进程占用，是否运行 stop.bat 释放
   ```
3. **返回抓包服务基本信息**：AI 执行开启或重启抓包服务后，必须从启动日志或 `capture_addon.py` 初始化输出中明确告知用户当前服务信息：`self.baseurl = _load_baseurl()` 的结果、`self.prefixes = _load_prefixes()` 的结果、`self.jsonl_path = _get_jsonl_path()` 的结果；若无法读取完整日志，需说明“未能从后台日志确认”，并提示用户查看抓包窗口输出。
4. **提示用户操作 UI**：浏览器代理 `127.0.0.1:12138`；证书已装“本地计算机 → 受信任的根证书颁发机构”；完成 UI 操作后回复“继续”。
5. **生成/刷新索引**：执行 `tools/scan_page_api.py`（默认增量，必要时加 `--full` 全量刷新），生成/更新 `tools/page_api_index.sqlite3`。
6. **生成勾选草稿**：执行 `tools/match_captures.py` → 消费方项目 `api_test_dwp_temp/capture_selection.md`。
   - “新接口”：默认 `[x]`
   - “已实现接口”：默认 `[ ]`（如需重跑手勾）
   - “特殊处理接口” (`body_skipped=true`)：默认 `[ ]` + ⚠️
   - “登录/登出接口”：仅展示，默认不入
7. **等待用户勾选**：AI 必须停下，**不得擅自续跑**。
8. **读勾选结果 → 编写**：
   - 新接口落点：按 `pure_path` 前缀推荐并校验前置 A 中的 `[接口方法文件]`，冲突时反问用户。
   - 若前置 A 是“当前用例无新增接口”，而草稿里仍有新接口 `[x]`：**必须打回**，让用户二选一（改前置 A 或取消勾选新接口）。
   - 已实现接口复用 `tools/page_api_index.sqlite3` 中记录的方法。
   - 登录/二进制接口默认不入例。
9. **执行 pytest 直到通过**：强制步骤，不得跳过；要求见 `SKILL.md` 的“核心原则 → 测试必须闭环”。

## 方式1关键原则

- 抓包草稿是门禁：没有用户确认勾选结果，不得开始生成接口方法或用例。
- 抓包记录只作为候选来源，最终仍要按 `tools/page_api_index.sqlite3` 查重。
- 生成方法和用例前，必须先按 `doc/coding_style_guide.md` 做风格对齐。
- 抓包中的 Cookie / token 不硬编码到用例，统一使用项目已有登录 fixture 或 API。
- 对 `body_skipped=true` 的二进制/文件响应接口，不要凭空构造响应断言。
