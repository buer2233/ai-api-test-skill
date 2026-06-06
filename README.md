# api-test-E10

`test-automation` 仓库**内置的接口自动化编写 Skill**（项目级，物理位置 `.claude/skills/api-test-E10/`），提供“新增 / 维护”两类任务入口；新增任务提供三种编写方式，维护任务提供四种维护方式。
AI 执行规范详见 [`SKILL.md`](./SKILL.md)，完整流程图详见 [`flow_chart/flow.md`](./flow_chart/flow.md)。

# AI接口自动化测试框架推荐

项目地址：https://github.com/buer2233/ai-api-test

基于当前项目的SKILL，结合通用的接口自动化测试框架编写的，通用的AI接口自动化框架。目前为初版状态，还在持续优化迭代中，感兴趣的大佬可以点个星星关注下。

# 实际的效率提升记录和使用记录

## 数据提升记录

数据来源于我个人工作中负责的EB低代码模块使用AI后的5个月，和使用AI前的5个月。

通过AI+SKILL编写接口用例的效率提升90%，综合效率提升46%。

| 月份                  | 周次           | 接口方法数 | 接口用例数 | 接口+用例总数 | AI使用 |
| --------------------- | -------------- | ---------- | ---------- | ------------- | ------ |
| 未使用AI前的5周数据   | 3月第四周      | 51         | 34         | 85            | 否     |
|                       | 3月第五周      | 5          | 29         | 34            | 否     |
|                       | 4月第一周      | 45         | 18         | 63            | 否     |
|                       | 4月第二周      | 26         | 38         | 64            | 否     |
|                       | 4月第三周      | 2          | 79         | 81            | 否     |
|                       | 合计           | 129        | 198        | 327           |        |
|                       |                |            |            |               |        |
| 使用AI提效后的5周数据 | 4月第四周      | 34         | 84         | 118           | 是     |
|                       | 5月第一周      | 28         | 58         | 86            | 是     |
|                       | 5月第二周      | 1          | 53         | 54            | 是     |
|                       | 5月第三周      | 31         | 109        | 140           | 是     |
|                       | 5月第四周      | 2          | 79         | 81            | 是     |
|                       | 合计           | 96         | 383        | 479           |        |
|                       |                |            |            |               |        |
|                       | 使用AI的提升率 | 74.42%     | 193.43%    | 146.48%       |        |

## 通过AI+SKILL编写自动化测试用例记录

<https://www.yuque.com/bbuer/ebdyfe/gpxaqwd5gnwk3bqt?singleDoc#> 《通过AI+SKILL编写自动化测试用例记录》

## 通过AI+SKILL维护用例的测试记录

<https://www.yuque.com/bbuer/ebdyfe/bua08uq469osgla1?singleDoc#> 《通过AI+SKILL维护用例的测试记录》

## 环境要求与安装

| 项 | 要求 | 依赖的第三方 Skill | Skill 安装命令与 GitHub 地址 |
|---|---|---|---|
| OS | Windows 10/11 | - | - |
| Python | ≥ 3.8 | - | - |
| mitmproxy | `pip install mitmproxy`（验证：`mitmdump --version`） | - | - |
| pytest 失败修复 | 维护方式④默认优先使用 | `/test-fixing` | `npx skills add sickn33/antigravity-awesome-skills@test-fixing -g -y`<br/>GitHub: `https://github.com/sickn33/antigravity-awesome-skills` |
| Python 断点调试 | `/test-fixing` 无法解决、调用栈或前后接口信息不明确时兜底使用 | `/Debugging` | `npx skills add pluginagentmarketplace/custom-plugin-python@debugging -g -y`<br/>GitHub: `https://github.com/pluginagentmarketplace/custom-plugin-python` |

`api-test-E10` 已随 `test-automation` 仓库一起分发，clone 仓库后无需额外安装。Claude Code 会自动从项目 `.claude/skills/` 目录加载本 skill。

第三方依赖 Skill 需要在当前 AI 工具环境中可用：`/test-fixing` 用于默认测试修复流程，`/Debugging` 用于维护困难时通过断点、执行堆栈、局部变量、请求 payload、接口响应和方法返回值辅助定位。

## 使用前：填写任务信息

### 新增用例任务

**新增接口方法/用例时，先填好下面 5 项发给 AI**。缺任意一项 AI 会直接打回。

```markdown
# 本次任务信息
- `[接口方法文件]` = `填写接口方法所在文件路径`（无新增时填：当前用例无新增接口）
- `[接口方法位置]` = `填写接口方法新增位置，例如：文件末尾 / 第123行后 / 某方法后`（无新增时填：当前用例无新增接口）
- `[接口用例文件]` = `填写接口用例所在文件路径`
- `[接口用例位置]` = `填写接口用例新增位置，例如：文件末尾 / 第456行插入 / 某用例后/ 完善某用例`
- `[fixture]` = `选填：接口用例的前后置fixture`
- `[用例名]` = `填写本次新增用例的完整中文功能名称`
```

- `[接口方法文件]` 与 `[接口方法位置]` **必须同时**填"当前用例无新增接口"，只填一项不合法
- `[fixture]` 为选填项，可省略或留空，不参与缺项判定

### 维护用例任务

**维护已有用例时，只强制提供下面 2 项**。不需要补新增任务的 `[接口方法文件]` / `[接口方法位置]` / `[用例名]`，除非本次维护确实涉及新增接口或新增用例。

```markdown
# 本次维护任务信息
- `[接口用例文件]` = `填写接口用例所在文件路径`
- `[接口用例位置]` = `填写具体的待维护的单个/多个用例，例如：test_xxx / 某测试类下的多个用例 / 第456行附近的 xxx 用例`
```

- **例外**：纯查询/工具/诊断类对话不需要填

> 因 skill 已固定安装在 `<project>/.claude/skills/api-test-E10/`，项目根由 skill 自身位置直接推导，**不再需要 AI 在对应前置门禁通过后回写 `config.project_path`**。抓包与勾选工具自动把运行时产物落到 `<project>/api_test_dwp_temp/`。

## 任务类型入口

AI 会先判断本次任务是：

- **新增**：新增接口方法 / 新增用例 / 补齐新链路
- **维护**：修复已有接口方法 / 更新已有用例 / 回溯最新链路 / 定点修补

确认任务类型后，再进入对应方式：新增任务三选一，维护任务四选一。

## 新增任务的三种编写方式

任务信息齐全后，AI 会让您选择以下方式（或根据任务信号自动推断）：

| 方式 | 流程概要 | 适合场景 |
|---|---|---|
| **① 抓包驱动** | UI 操作 → 抓包 JSONL → 勾选接口 → 分析抓包 → 设计用例 → 相似度检查 → 编写用例 → pytest | 新接口多 / 复杂链路 |
| **② 参考已有用例** | 指定参考用例 → AI 仿写 → pytest | 同类批量 / 修参数断言 |
| **③ cURL 手工** | 粘贴 cURL + 响应 → AI 解析生成 → pytest | 抓包不可用 / 数据过大 |

> 详细决策树与每种方式的完整步骤见 [`flow_chart/flow.md`](./flow_chart/flow.md)。

## 维护任务的四种维护方式

维护任务信息齐全后，AI 会让您选择以下方式（或根据任务信号自动推断）：

| 方式 | 流程概要 | 适合场景 |
|---|---|---|
| **① 抓包驱动** | 最新抓包 → 回溯链路 → 对照现有实现 → 维护用例 → pytest | 链路变化大 / 多接口联动 |
| **② 参考已有用例** | 指定参考样本 → 对照差异 → 局部维护 → pytest | 同类用例结构稳定 / 参数断言调整 |
| **③ cURL 手工** | 粘贴 cURL + 响应 → 对照旧实现 → 定点维护 → pytest | 少量接口变化明确 |
| **④ pytest 报错驱动** | AI 直接执行目标用例 pytest → 按最后一个中断报错分类 → 用例待维护时优先 `/test-fixing` → 必要时 `/Debugging` 断点定位 → 循环验证 | 用户只想指定用例后让 AI 自行跑失败并维护 |

### 新增任务方式① 快速上手

1. 双击 `capture/start.bat` 启动抓包（或让 AI 启动）
2. 浏览器代理 → `127.0.0.1:12138`，完成业务操作后回复"继续"
3. AI 生成勾选草稿 → 您勾选需要的接口 → AI 分析抓包、设计用例、检查相似用例 → 编写方法/用例 → pytest 闭环

### 新增任务方式② 快速上手

发送 `# 本次任务信息` + 参考样本（函数名或文件路径）+ 差异点描述

### 新增任务方式③ 快速上手

发送 `# 本次任务信息` + 每个接口的 cURL 命令 + 对应响应体

> 运行时产物（`latest.jsonl`、`capture_selection.md`）落在**项目根**的 `api_test_dwp_temp/` 下，**不在** skill 自身目录。

## 常见问题

**Q：12138 端口被占？** 运行 `capture/stop.bat`；仍失败则 `netstat -ano | findstr :12138` 查占用 PID。

**Q：mitmproxy HTTPS 仍告警？** 99% 是证书装到"当前用户"而非"本地计算机"，参考 `capture/README.md` 重装。

**Q：抓不到 `/oa/second` 下请求？** 检查 `config.py` 中 `RunConfig.baseurl` 是否与浏览器访问域名一致。

**Q：抓包数据太多？** 在 `capture/allowed_prefixes.txt` 删减前缀，或在勾选草稿中只勾必要接口。

**Q：抓包含敏感信息吗？** `Cookie`/`Authorization` 头仅保留前 20 字符 + 长度摘要，不落全量。建议定期清理项目根下 `api_test_dwp_temp/latest.jsonl`。

**Q：不想用抓包？** 可用方式②（参考已有用例）或方式③（cURL 手工）。

**Q：抓包数据落到 skill 目录而不是项目目录？** 本版本 skill 已固定安装在 `<project>/.claude/skills/api-test-E10/`，项目根由 skill 位置直接推导。如发现产物落到 skill 目录，请确认目录路径符合该结构、且项目根下存在 `E10自动化` 子目录。

## 进一步阅读

| 文档 | 用途 |
|---|---|
| [`SKILL.md`](./SKILL.md) | AI 编写规范（前置门禁、方式分流、核心原则） |
| [`doc/preflight_gates_new.md`](./doc/preflight_gates_new.md) | 新增任务前置门禁详细执行手册（按需加载） |
| [`doc/preflight_gates_maintenance.md`](./doc/preflight_gates_maintenance.md) | 维护任务前置门禁详细执行手册（按需加载） |
| [`doc/core_principles.md`](./doc/core_principles.md) | 核心原则 1-5 详细规则（按需加载） |
| [`doc/maintenance_prompt_context.md`](./doc/maintenance_prompt_context.md) | 维护专用提示词上下文 |
| [`doc/mode_capture_driven.md`](./doc/mode_capture_driven.md) | 新增方式1：抓包驱动详细流程 |
| [`doc/mode_reference_case.md`](./doc/mode_reference_case.md) | 新增方式2：参考已有用例详细流程 |
| [`doc/mode_curl_manual.md`](./doc/mode_curl_manual.md) | 新增方式3：cURL 手工详细流程 |
| [`doc/mode_maintenance_capture_driven.md`](./doc/mode_maintenance_capture_driven.md) | 维护方式1：抓包驱动详细流程 |
| [`doc/mode_maintenance_reference_case.md`](./doc/mode_maintenance_reference_case.md) | 维护方式2：参考已有用例详细流程 |
| [`doc/mode_maintenance_curl_manual.md`](./doc/mode_maintenance_curl_manual.md) | 维护方式3：cURL 手工详细流程 |
| [`doc/mode_maintenance_pytest_driven.md`](./doc/mode_maintenance_pytest_driven.md) | 维护方式4：pytest 报错驱动详细流程 |
| [`doc/coding_style_guide.md`](./doc/coding_style_guide.md) | 接口方法/用例编码风格规范 |
| [`doc/high_frequency_experience.md`](./doc/high_frequency_experience.md) | 高频踩坑经验（按需查阅） |
| [`flow_chart/flow.md`](./flow_chart/flow.md) | 完整流程图（Mermaid 源码，含决策树与方式对比） |
| [`capture/README.md`](./capture/README.md) | 抓包配置细节（证书安装、代理设置、过滤规则） |

# 友情链接
L站：[Linux do](https://linux.do/)