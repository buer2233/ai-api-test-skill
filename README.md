# api-test-common

> 一个面向 **所有 `python + pytest + requests` 接口自动化测试框架** 的 AI Skill：把接口方法扫描、用例编写、抓包分析、pytest 失败维护和项目编码风格约束串成可落地的自动化工作流。

AI 执行规范详见 [`SKILL.md`](./SKILL.md)，完整流程图详见 [`flow_chart/flow.md`](./flow_chart/flow.md)。

如果你的接口自动化项目满足这三个条件：**Python 编写、pytest 执行、requests 发请求**，这个 Skill 就可以通过 `config.json` 接入你的项目，而不是被某一个固定目录、固定包名或固定业务系统绑定。

它的目标不是再造一个测试框架，而是让 AI 更稳定地在你现有的接口自动化框架里工作：读懂现有接口层、沿用已有编码风格、避免重复造接口方法、按真实 pytest 结果闭环维护。

## 为什么值得关注

- **框架无侵入接入**：通过 `config.json` 指定项目根、接口方法目录、用例目录、pytest 工作目录和扫描目录；不要求你迁移项目结构。
- **适配真实项目写法**：支持直接 `requests.*`、`requests.request(...)`、`self.get/post/...`、`self.request("METHOD", ...)`、`send_msg(...)` 等常见封装，并支持后续追加特殊提取规则。
- **自动建立 API 索引**：扫描现有接口方法，生成 `tools/page_api_index.sqlite3`，用于查重、抓包匹配、源码分析和新增用例前的接口覆盖判断。
- **先学习你的编码风格**：初始化扫描时基于你提供的接口方法模板和 pytest 用例模板生成 `coding_style_guide` 草稿，让 AI 按你的项目风格写代码。
- **新增和维护都能跑通闭环**：新增任务支持抓包、参考已有用例、cURL、Java Controller 源码四种入口；维护任务支持抓包回溯、参考用例、cURL、pytest 报错驱动四种方式。
- **pytest 结果优先**：维护时以真实 pytest 报错分类，区分“功能 BUG / 用例待维护 / 信息不足”，避免为了通过测试盲目改断言。
- **面向 Windows 友好**：路径、中文目录、PowerShell pytest 命令、UTF-8 编码和抓包运行目录都做了显式约束。
- **保留安全门禁**：新增/维护任务有明确前置清单，特殊接口提取规则采用“预览 → 用户确认 → 增量入库”，不偷偷改库。

## 适配范围

当前 Skill 专注一个清晰边界：`python + pytest + requests` 接口自动化测试框架。

| 支持 | 暂不支持 |
|---|---|
| pytest 用例组织与执行 | unittest |
| requests 及基于 requests 的轻量封装 | httpx / aiohttp |
| 现有 page_api / api_client / service_api 等接口封装目录 | 非 Python 接口测试框架 |
| 抓包、cURL、参考用例、Java Controller 源码辅助编写 | 通用 UI 自动化、性能测试、契约测试平台 |

## 典型使用路径

1. 在 [`config.json`](./config.json) 中配置你的测试框架路径。
2. 选择接口方法模板和 pytest 用例模板，运行初始化扫描，生成编码风格草稿和 API 索引。
3. 新增接口自动化用例时，按前置清单提供接口方法文件、用例文件和用例名，选择抓包 / 参考用例 / cURL / Controller 源码方式。
4. 维护失败用例时，指定用例位置，AI 按最新 pytest 报错定位并分类处理。
5. 每次改动都以目标 pytest 命令和关键日志收尾，避免只生成代码不验证。

## 环境要求与安装

| 项 | 要求 | 依赖的第三方 Skill | Skill 安装命令与 GitHub 地址 |
|---|---|---|---|
| OS | Windows 10/11 | - | - |
| Python | ≥ 3.8 | - | - |
| mitmproxy | `pip install mitmproxy`（验证：`mitmdump --version`） | - | - |
| pytest 失败修复 | 维护方式④默认优先使用 | `/test-fixing` | `npx skills add sickn33/antigravity-awesome-skills@test-fixing -g -y`<br/>GitHub: `https://github.com/sickn33/antigravity-awesome-skills` |
| Python 断点调试 | `/test-fixing` 无法解决、调用栈或前后接口信息不明确时兜底使用 | `/Debugging` | `npx skills add pluginagentmarketplace/custom-plugin-python@debugging -g -y`<br/>GitHub: `https://github.com/pluginagentmarketplace/custom-plugin-python` |

使用前必须先初始化本目录下的 [`config.json`](./config.json)，把 `project_root`、API 方法目录、pytest 工作目录、用例目录和索引扫描目录改成目标接口自动化项目的真实路径。

第三方依赖 Skill 需要在当前 AI 工具环境中可用：`/test-fixing` 用于默认测试修复流程，`/Debugging` 用于维护困难时通过断点、执行堆栈、局部变量、请求 payload、接口响应和方法返回值辅助定位。

## 使用前：初始化 config.json

本 skill 不再从固定目录或项目 marker 推导项目根。所有路径都从 `config.json` 读取。

最小必填项：

```json
{
  "framework": "pytest_requests",
  "project_root": "D:/your-api-test-project",
  "paths": {
    "api_method_dirs": ["tests/page_api"],
    "test_case_dirs": ["tests/cases"],
    "pytest_workdir": "tests",
    "runtime_temp_dir": "runtime"
  },
  "pytest": {
    "pythonpath": ".",
    "command_template": "pytest {target} -v --tb=short"
  },
  "api_index": {
    "db_path": "tools/page_api_index.sqlite3",
    "extract_rules_path": "tools/api_extract_rules.json",
    "scan_dirs": ["tests/page_api"],
    "extract_rules": "builtin_requests_plus_generated"
  }
}
```

`tools/api_extract_rules.json` 是内部规则文件，由初始化扫描或 AI 维护；用户无需手写正则。

历史项目路径只作为迁移参考，不再是默认硬规则。

初始化扫描示例：

```powershell
python tools/init_project_scan.py `
  --config config.json `
  --api-template D:\your-api-test-project\tests\page_api\user_api.py `
  --case-template D:\your-api-test-project\tests\cases\test_user_api.py
```

扫描完成后会生成：

- 编码风格草稿：`<project_root>/<paths.runtime_temp_dir>/coding_style_guide_draft.md`
- API 覆盖索引：`tools/page_api_index.sqlite3`
- 内部提取规则文件：`tools/api_extract_rules.json`

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
| [`doc/mode_java_controller_source.md`](./doc/mode_java_controller_source.md) | 新增方式4：Java Controller 源码参考详细流程 |
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
