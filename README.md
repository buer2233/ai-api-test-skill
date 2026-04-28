# api-test-dwp

面向 `test-automation` 仓库的**接口自动化编写 Skill**，支持三种编写方式。

## 🚨 使用前必读 A：任务信息模板

**每次触发接口方法/用例编写任务时，请先把下面这段信息填好发给 AI**。缺任意一项 AI 会直接打回，不开始工作。

```markdown
# 本次任务信息
- `[接口方法文件]` = `填写接口方法所在文件路径`（本次无新增接口时填：当前用例无新增接口）
- `[接口方法位置]` = `填写接口方法新增位置，例如：文件末尾 / 第123行后 / 某方法后`（本次无新增接口时填：当前用例无新增接口）
- `[接口用例文件]` = `填写接口用例所在文件路径`
- `[接口用例位置]` = `填写接口用例新增位置，例如：文件末尾 / 第456行插入 / 某用例后/ 完善某用例`
- `[用例名]` = `填写本次新增用例的完整中文功能名称`
```

- **允许"无新增接口"占位**：只复用仓库现有接口时，把 `[接口方法文件]` 与 `[接口方法位置]` **同时**填"当前用例无新增接口"即可
- **例外**：纯查询/分析/工具类对话（如"查已实现的方法""帮我启动抓包""扫索引""看某文件"）不需要填

## 🚨 使用前必读 B：选择编写方式

任务信息齐全后，AI 会让你在以下 **3 种方式** 中选择一个（或根据任务里的信号自动推断）：

| 方式 | 简介 | 适合场景 |
|---|---|---|
| **① 推荐：抓包驱动** | UI 操作 → AI 读 `latest.jsonl` → 勾选接口 → 生成用例 | 新接口较多 / 业务链路复杂 |
| **② 推荐：参考已有用例** | 告诉 AI "参照哪个已有用例"，AI 仿写 | 同类批量 / 只改参数断言 / 修复用例 |
| **③ 补充：cURL 手工** | 你提供 `curl` 命令 + 接口返回值，AI 据此编写 | 抓包工具不可用 / 数据过大 |

**详细决策树与流程图见** [`flow_chart/flow.md`](./flow_chart/flow.md)。

## 一、这是什么

一个**强绑定当前仓库**的 Skill，把接口自动化编写统一到三种可选路径上：

```
方式① 抓包驱动： UI 操作 → AI 读抓包 JSONL → 勾选 → 生成方法/用例 → pytest
方式② 参考复制： 用户指定参考用例 → AI 读参考 → 仿写 → pytest
方式③ cURL 手工： 用户粘贴 cURL + 响应 → AI 解析 → 生成方法/用例 → pytest
```

## 二、环境要求

| 项 | 要求 |
|---|---|
| OS | Windows 10/11（已在 Windows 下验证 `.bat`） |
| Python | ≥ 3.8 |
| pip | 能访问公司/公网 pip 源 |
| mitmproxy | 最新稳定版（`pip install mitmproxy`） |
| 浏览器 | Chrome 推荐，配合 SwitchyOmega 插件可切换代理 |

## 三、一键安装

```bat
pip install mitmproxy
```

验证：

```bat
mitmdump --version
```

## 四、快速开始（按方式分路径）

### 方式① 抓包驱动

#### 步骤 1：启动抓包

双击 `capture/start.bat`，看到 `Proxy server listening at *:12138` 即成功。

或直接让 AI 启动：

> "帮我启动 api-test-dwp 抓包"

AI 会检查 12138 端口，未开启时自动运行 `start.bat`。

#### 步骤 2：在浏览器完成业务操作

- 先确保浏览器代理指向 `127.0.0.1:12138`
- 首次使用需安装 mitmproxy CA 证书（详见 `capture/README.md`）
- 然后正常使用被测系统，AI 会自动抓包 + 过滤 + 落盘到 `capture/latest.jsonl`

#### 步骤 3：告诉 AI 基于抓包生成用例

> "基于抓包生成接口用例"（连同 `# 本次任务信息` 一起发给 AI）

AI 将：
1. 读取 `capture/latest.jsonl`
2. 按 URL path 与仓库 `page_api` 代码查重
3. 生成 `capture_selection.md` 草稿供你勾选
4. 根据勾选结果，新接口写方法，已实现接口直接复用
5. 按抓包顺序编排用例
6. 执行 `pytest` 直到通过

---

### 方式② 参考已有用例

把 `# 本次任务信息` + **参考样本**一起发给 AI：

> 本次任务信息：...
>
> 参考用例：`test_case/test_eBuilder_case/test_ebuilder_page_case/test_ebuilder_page_coms_dataDisplay2_api_PC/test_ebuilder_page_coms_dataDisplay2_new2_api_PC.py::test_ebuilder_TFAA_mindmap_sort`
>
> 差异点：把排序从升序改为降序，预期数据调整

AI 将：
1. Read 参考用例 + 测试类头部
2. 按 `page_api_index.json` 核对调用链
3. 仿写新用例（保留步骤骨架、参数化、断言风格）
4. 执行 `pytest` 直到通过

---

### 方式③ cURL 手工

把 `# 本次任务信息` + **cURL 命令 + 响应**一起发给 AI：

> 本次任务信息：...
>
> 接口1 cURL：
> ```bash
> curl -X POST "https://weapp.mulinquan.cn/api/bs/ebuilder/xxx" -H "Content-Type: application/json" -d '{"a":1}'
> ```
> 接口1 响应：
> ```json
> {"code":200,"data":{...}}
> ```
>
> 接口2 cURL：...

AI 将：
1. 解析每个 cURL 的 method/URL/headers/body
2. 按 `pure_path` 查重：命中复用，未命中按 `[接口方法文件]/[接口方法位置]` 新增
3. 以 cURL 顺序组装用例步骤
4. 断言取自用户提供的响应
5. 执行 `pytest` 直到通过

## 五、目录结构

```
api-test-dwp/
├── README.md                    # 本文件
├── SKILL.md                     # Skill 主规范（AI 按此执行）
├── flow_chart/                  # 流程图目录（Mermaid 源文件 + PNG 导出图）
│   ├── flow.md                  # 当前 skill 的完整流程图源码
│   ├── 1.主流程图.png
│   ├── 2.前置操作的门禁要求.png
│   ├── 3.推荐方式1-抓包驱动.png
│   ├── 4.推荐方式2-参考已有用例.png
│   ├── 5.补充方式3-手工复制cURL.png
│   └── 6.pytest执行闭环.png
├── .gitignore                   # 忽略运行时产物
├── capture/                     # 抓包底座（方式① 用）
│   ├── README.md                # 抓包配置详细指引（首次必读）
│   ├── capture_addon.py         # mitmdump addon，落盘 JSONL
│   ├── start.bat                # 一键启动 12138
│   ├── stop.bat                 # 停止 12138 进程
│   ├── allowed_prefixes.txt     # 用户可扩展的过滤前缀
│   └── latest.jsonl             # 运行时产物（已 .gitignore）
├── tools/                       # 索引与匹配工具（三方式共用）
│   ├── scan_page_api.py         # 扫描 page_api 生成索引
│   ├── match_captures.py        # 抓包 vs 索引 → 生成选择草稿
│   ├── check_capture_server.py  # 检测 12138 抓包服务器状态
│   └── page_api_index.json      # 运行时索引（已 .gitignore）
└── capture_selection.md         # 运行时选择草稿（已 .gitignore）
```

## 六、与仓库其它 Skill 的关系

- 仓库里 `CLAUDE.md` 指向本 Skill 作为接口自动化的首选规范入口
- UI 自动化仍在 `E10自动化/UI自动化/` 内，本 Skill 只管接口
- 跨框架账号仍共用 `account.txt`，本 Skill 不改动账号机制

## 七、常见问题

**Q：12138 端口被占怎么办？**
A：运行 `capture/stop.bat` 释放；如仍失败，查 `netstat -ano | findstr :12138` 看哪个 PID 占用。

**Q：mitmproxy 证书装了但 HTTPS 仍告警？**
A：99% 是装到了"当前用户"而非"本地计算机"。参考 `capture/README.md` 第 3 步重装。

**Q：抓不到 `/oa/second` 下的请求？**
A：检查 `E10自动化/接口自动化测试/config.py` 中 `RunConfig.baseurl` 是否与浏览器访问的域名一致；addon 只记录与 baseurl 匹配的请求。

**Q：AI 说"抓包数据太多"，怎么减少？**
A：addon 已按 baseurl + 多前缀过滤；若仍冗余，可在 `capture/allowed_prefixes.txt` 删减前缀，或在 AI 勾选草稿时只勾必要接口。

**Q：抓包里含有我的 Cookie 吗？**
A：`Cookie` 和 `Authorization` 头被摘要（保留前 20 字符 + 长度），不会落全量敏感数据。但响应体不做摘要，建议定期清理 `capture/latest.jsonl`。

**Q：不想用抓包，还能用原来的 cURL 粘贴模式吗？**
A：可以。SKILL.md 中抓包流程只是"优先推荐"，无抓包数据时仍按原流程工作。

## 八、进一步阅读

- **AI 编写规范**：`SKILL.md`
- **流程图源码与导出图**：`flow_chart/flow.md`、`flow_chart/*.png`
- **抓包配置细节**：`capture/README.md`
