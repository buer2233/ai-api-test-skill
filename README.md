# api-test-dwp

面向 `test-automation` 仓库的**接口自动化编写 Skill**，提供三种编写方式。
AI 执行规范详见 [`SKILL.md`](./SKILL.md)，完整流程图详见 [`flow_chart/flow.md`](./flow_chart/flow.md)。

## 环境要求与安装

| 项 | 要求 |
|---|---|
| OS | Windows 10/11 |
| Python | ≥ 3.8 |
| mitmproxy | `pip install mitmproxy`（验证：`mitmdump --version`） |

## 使用前：填写任务信息

**每次触发接口方法/用例编写时，先填好下面 5 项发给 AI**。缺任意一项 AI 会直接打回。

```markdown
# 本次任务信息
- `[接口方法文件]` = `填写接口方法所在文件路径`（无新增时填：当前用例无新增接口）
- `[接口方法位置]` = `填写接口方法新增位置，例如：文件末尾 / 第123行后 / 某方法后`（无新增时填：当前用例无新增接口）
- `[接口用例文件]` = `填写接口用例所在文件路径`
- `[接口用例位置]` = `填写接口用例新增位置，例如：文件末尾 / 第456行插入 / 某用例后/ 完善某用例`
- `[用例名]` = `填写本次新增用例的完整中文功能名称`
```

- `[接口方法文件]` 与 `[接口方法位置]` **必须同时**填"当前用例无新增接口"，只填一项不合法
- **例外**：纯查询/工具/诊断类对话不需要填

## 三种编写方式

任务信息齐全后，AI 会让您选择以下方式（或根据任务信号自动推断）：

| 方式 | 流程概要 | 适合场景 |
|---|---|---|
| **① 抓包驱动** | UI 操作 → 抓包 JSONL → 勾选接口 → 生成用例 → pytest | 新接口多 / 复杂链路 |
| **② 参考已有用例** | 指定参考用例 → AI 仿写 → pytest | 同类批量 / 修参数断言 |
| **③ cURL 手工** | 粘贴 cURL + 响应 → AI 解析生成 → pytest | 抓包不可用 / 数据过大 |

> 详细决策树与每种方式的完整步骤见 [`flow_chart/flow.md`](./flow_chart/flow.md)。

### 方式① 快速上手

1. 双击 `capture/start.bat` 启动抓包（或让 AI 启动）
2. 浏览器代理 → `127.0.0.1:12138`，完成业务操作后回复"继续"
3. AI 生成勾选草稿 → 您勾选需要的接口 → AI 生成方法/用例 → pytest 闭环

### 方式② 快速上手

发送 `# 本次任务信息` + 参考样本（函数名或文件路径）+ 差异点描述

### 方式③ 快速上手

发送 `# 本次任务信息` + 每个接口的 cURL 命令 + 对应响应体

## 目录结构

```
api-test-dwp/
├── README.md                     # 本文件（用户快速指南）
├── SKILL.md                      # AI 执行规范（核心，每次激活必加载）
├── coding_style_guide.md         # 接口方法/用例编码风格规范（编写时按需加载）
├── high_frequency_experience.md  # 高频踩坑经验（按需查阅）
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
│   ├── capture_addon.py          # mitmdump 插件（过滤 + 落盘 JSONL）
│   ├── allowed_prefixes.txt      # 用户可扩展的 URL 过滤前缀
│   └── latest.jsonl              # 抓包产物（gitignored）
├── tools/                        # 索引与匹配工具（三方式共用）
│   ├── scan_page_api.py          # 扫描 page_api 生成索引
│   ├── match_captures.py         # 抓包 vs 索引 → 勾选草稿
│   ├── check_capture_server.py   # 检测 12138 抓包服务器状态
│   └── page_api_index.json       # 全局接口覆盖文档（纳入版本管理）
└── capture_selection.md          # 勾选草稿（gitignored）
```

## 常见问题

**Q：12138 端口被占？** 运行 `capture/stop.bat`；仍失败则 `netstat -ano | findstr :12138` 查占用 PID。

**Q：mitmproxy HTTPS 仍告警？** 99% 是证书装到"当前用户"而非"本地计算机"，参考 `capture/README.md` 重装。

**Q：抓不到 `/oa/second` 下请求？** 检查 `config.py` 中 `RunConfig.baseurl` 是否与浏览器访问域名一致。

**Q：抓包数据太多？** 在 `capture/allowed_prefixes.txt` 删减前缀，或在勾选草稿中只勾必要接口。

**Q：抓包含敏感信息吗？** `Cookie`/`Authorization` 头仅保留前 20 字符 + 长度摘要，不落全量。建议定期清理 `capture/latest.jsonl`。

**Q：不想用抓包？** 可用方式②（参考已有用例）或方式③（cURL 手工）。

## 进一步阅读

| 文档 | 用途 |
|---|---|
| [`SKILL.md`](./SKILL.md) | AI 编写规范（完整执行流程、校验规则、风格约束） |
| [`flow_chart/flow.md`](./flow_chart/flow.md) | 完整流程图（Mermaid 源码，含决策树与三方式对比） |
| [`capture/README.md`](./capture/README.md) | 抓包配置细节（证书安装、代理设置、过滤规则） |
| [`high_frequency_experience.md`](./high_frequency_experience.md) | 高频踩坑经验（按需查阅） |
