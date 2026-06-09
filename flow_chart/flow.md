# api-test-E10 执行流程图

本文件使用 [Mermaid](https://mermaid.js.org/) 绘制。VSCode / GitHub / Obsidian / Typora 等均可直接渲染。

> 新增任务前置门禁见 `doc/preflight_gates_new.md`，维护任务前置门禁见 `doc/preflight_gates_maintenance.md`。新增任务的四种方式已拆分到 `doc/mode_capture_driven.md`、`doc/mode_reference_case.md`、`doc/mode_curl_manual.md`、`doc/mode_java_controller_source.md`；维护任务的四种方式已拆分到 `doc/mode_maintenance_*.md`，维护共用提示词见 `doc/maintenance_prompt_context.md`。本文件仅维护流程图与决策关系。

---

## 一、总览（入口流程）

```mermaid
flowchart TD
    Start([用户触发任务]) --> ExceptCheck{纯查询/工具/诊断类?}
    ExceptCheck -- 是 --> QuickAnswer[直接响应并提示<br/>正式编写需先确认新增/维护<br/>并提交对应任务信息]
    ExceptCheck -- 否 --> P0[前置 0<br/>运行 preflight_check.py]

    P0 --> P0Result{索引数据<br/>是否可用?}
    P0Result -- 日期配置有误 --> P0Fail[回显错误信息<br/>请用户修正 config.json]
    P0Fail --> Start
    P0Result -- "数据最新 / 已自动更新" --> T[识别任务类型<br/>新增 / 维护]

    T --> TSig{任务里有<br/>新增/维护明确信号?}
    TSig -- 是 --> TAuto[按信号自动推断<br/>新增 / 维护]
    TSig -- 否 --> TAsk[询问任务类型<br/>等用户确认新增 / 维护]
    TAsk --> TRecv[收到用户回复]

    TAuto --> Route{任务类型?}
    TRecv --> Route

    Route -- 新增 --> ReadNew[读取并执行<br/>doc/preflight_gates_new.md]
    Route -- 维护 --> ReadMaint[读取并执行<br/>doc/preflight_gates_maintenance.md]

    ReadNew --> NewInfo{新增 5 项<br/>任务信息齐全?}
    NewInfo -- 否 --> ARej[打回：返回新增填写模板<br/>等用户补齐]
    ARej --> Start
    NewInfo -- 是 --> A2{"接口方法文件<br/>与 接口方法位置<br/>是否声明<br/>当前用例无新增接口?"}

    A2 -- "两项同为无新增接口" --> NoNewApi["登记: 本次不得新增接口<br/>只能复用现有"]
    A2 -- 两项均为具体内容 --> HasNewApi["登记: 允许按指定位置<br/>新增接口方法"]
    A2 -- "只填一项无新增接口" --> A2Rej["打回: 必须同时声明"]
    A2Rej --> Start

    NoNewApi --> NewMode{新增方式已确定?<br/>含自动推断}
    HasNewApi --> NewMode
    NewMode -- 是 --> NewTodo[TodoWrite 首项:<br/>新增 + 方式N + 5 项任务信息]
    NewMode -- 否 --> NewAsk[按 preflight_gates_new.md<br/>询问新增四选一]
    NewAsk --> NewTodo

    ReadMaint --> MaintInfo{维护 2 项<br/>任务信息齐全?}
    MaintInfo -- 否 --> AMRej[打回：返回维护填写模板<br/>等用户补齐]
    AMRej --> Start
    MaintInfo -- 是 --> MaintMode{维护方式已确定?<br/>含自动推断}
    MaintMode -- 是 --> MaintTodo[TodoWrite 首项:<br/>维护 + 方式N + 2 项任务信息]
    MaintMode -- 否 --> MaintAsk[按 preflight_gates_maintenance.md<br/>询问维护四选一]
    MaintAsk --> MaintTodo

    NewTodo --> Dispatch{任务类型 + 方式分流}
    MaintTodo --> Dispatch
    Dispatch -- 新增-方式① --> Flow1A[新增方式1: 抓包驱动]
    Dispatch -- 新增-方式② --> Flow2A[新增方式2: 参考已有用例]
    Dispatch -- 新增-方式③ --> Flow3A[新增方式3: cURL 手工]
    Dispatch -- 新增-方式④ --> Flow4A[新增方式4: Java Controller 源码参考]
    Dispatch -- 维护-方式① --> Flow1B[维护方式1: 抓包驱动]
    Dispatch -- 维护-方式② --> Flow2B[维护方式2: 参考已有用例]
    Dispatch -- 维护-方式③ --> Flow3B[维护方式3: cURL 手工]
    Dispatch -- 维护-方式④ --> Flow4B[维护方式4: pytest 报错驱动]

    Flow1A --> Pytest[pytest 闭环]
    Flow2A --> Pytest
    Flow3A --> Pytest
    Flow4A --> Pytest
    Flow1B --> Pytest
    Flow2B --> Pytest
    Flow3B --> Pytest
    Flow4B --> Pytest

    Pytest --> Report[输出新增/维护方法与用例清单<br/>+ 执行结果]
    Report --> End([完成])

    classDef reject fill:#f88,stroke:#c00,color:#000
    classDef pass fill:#8f8,stroke:#080,color:#000
    classDef wait fill:#fc8,stroke:#c80,color:#000
    class ARej,AMRej,A2Rej,P0Fail reject
    class NoNewApi,HasNewApi pass
    class TAsk,TRecv,ReadNew,ReadMaint,NewAsk,MaintAsk wait
```

---

## 二、前置 0 / 新增前置 / 维护前置决策闸门

```mermaid
flowchart LR
    Q1[用户请求] --> G1{是编写类任务?}
    G1 -- 否 --> PassThru[例外通道:<br/>查询/工具/诊断]
    G1 -- 是 --> G0[运行 preflight_check.py]
    G0 --> G0R{索引数据可用?}
    G0R -- 否 --> G0Fail[回显错误<br/>等用户修正]
    G0R -- 是 --> G1T{任务类型明确?}

    G1T -- 否 --> AskType[询问新增 / 维护]
    G1T -- 是 --> TypeRoute{任务类型?}
    AskType --> TypeRoute

    TypeRoute -- 新增 --> ReadN[读取<br/>preflight_gates_new.md]
    TypeRoute -- 维护 --> ReadM[读取<br/>preflight_gates_maintenance.md]

    ReadN --> NInfo{新增 5 项齐全?}
    NInfo -- 否 --> Ret1[返回新增填写模板]
    NInfo -- 只一项填无新增 --> Ret2[返回同填提示]
    NInfo -- 是 --> NMode{新增方式已定?}

    ReadM --> MInfo{维护 2 项齐全?}
    MInfo -- 否 --> RetM[返回维护填写模板]
    MInfo -- 是 --> MMode{维护方式已定?}

    NMode -- 任务有信号 --> AutoN[自动推断新增方式]
    NMode -- 无信号 --> AskN[新增四选一菜单]
    NMode -- 用户已回复数字 --> TakeN[采纳新增方式]

    MMode -- 任务有信号 --> AutoM[自动推断维护方式]
    MMode -- 无信号 --> AskM[维护四选一菜单]
    MMode -- 用户已回复数字 --> TakeM[采纳维护方式]

    AutoN --> Go[进入对应方式流程]
    AskN --> Go
    TakeN --> Go
    AutoM --> Go
    AskM --> Go
    TakeM --> Go

    style G0Fail fill:#f88
    style Ret1 fill:#f88
    style RetM fill:#f88
    style Ret2 fill:#f88
    style AskType fill:#fc8
    style AskN fill:#fc8
    style AskM fill:#fc8
    style PassThru fill:#8cf
    style Go fill:#8f8
```

---

## 三、新增任务总览（入口到方式分流）

```mermaid
flowchart TD
    NStart([新增任务进入]) --> NeedGate{是否已读取并执行<br/>preflight_gates_new.md?}
    NeedGate -- 否 --> ReadGate[先读取新增前置门禁]
    NeedGate -- 是 --> Info
    ReadGate --> Info{新增 5 项<br/>任务信息齐全?}

    Info -- 否 --> AskInfo[照抄新增填写模板<br/>等用户补齐]
    AskInfo --> NStop([暂停])
    Info -- 是 --> ApiPair{"接口方法文件<br/>与 接口方法位置<br/>是否声明<br/>当前用例无新增接口?"}

    ApiPair -- "两项同为无新增接口" --> NoNew[登记: 本次无新增接口<br/>只能复用现有接口]
    ApiPair -- 两项均为具体内容 --> HasNew[登记: 允许按指定落点<br/>新增接口方法]
    ApiPair -- "只填一项无新增接口" --> RejectPair[打回: 两项必须同时声明]
    RejectPair --> NStop

    NoNew --> Mode{新增方式已确定?}
    HasNew --> Mode
    Mode -- 任务有明确信号 --> AutoMode[自动推断<br/>方式1 / 方式2 / 方式3 / 方式4]
    Mode -- 用户已回复数字 --> TakeMode[采纳用户选择]
    Mode -- 否 --> AskMode[照抄新增四选一菜单<br/>等用户选择]
    AskMode --> TakeMode

    AutoMode --> ReadDocs[读取 coding_style_guide.md<br/>+ 对应 mode_*.md]
    TakeMode --> ReadDocs
    ReadDocs --> Dispatch{进入新增方式}
    Dispatch --> N1[新增方式1：抓包驱动]
    Dispatch --> N2[新增方式2：参考已有用例]
    Dispatch --> N3[新增方式3：cURL 手工]
    Dispatch --> N4[新增方式4：Java Controller 源码参考]

    N1 --> VerifyN[pytest 闭环]
    N2 --> VerifyN
    N3 --> VerifyN
    N4 --> VerifyN
    VerifyN --> NEnd([完成新增])

    classDef nWait fill:#fc8,stroke:#c80,color:#000
    classDef nPass fill:#8f8,stroke:#080,color:#000
    classDef nReject fill:#f88,stroke:#c00,color:#000
    class ReadGate,AskInfo,AskMode,ReadDocs nWait
    class NoNew,HasNew,N1,N2,N3,N4,NEnd nPass
    class RejectPair nReject
```

### 新增任务关键原则

- 新增前先读取 `doc/preflight_gates_new.md`，并完成 5 项任务信息校验。
- `[fixture]` 为选填，不参与缺项判定；其余字段必须是真实文件、真实位置和完整中文用例名。
- `[接口方法文件]` 与 `[接口方法位置]` 可同时声明“当前用例无新增接口”；只声明一项时必须打回。
- 声明“无新增接口”后，后续只能复用仓库现有接口方法，不得新增接口方法。
- 方式未明确时必须照抄新增四选一菜单；有明确抓包、参考样本、cURL 或 Java Controller/Jacoco 信号时可自动推断。
- 进入具体方式前，必须读取 `doc/coding_style_guide.md` 与对应 `doc/mode_*.md`。

---

## 四、新增方式①：抓包驱动

```mermaid
flowchart TD
    F1Start([方式1 入口]) --> NeedRestart{用户提及<br/>重启抓包服务?}
    NeedRestart -->|是| Restart[restart.bat<br/>停止 12138<br/>等 1 秒后重启]
    NeedRestart -->|否| Chk[check_capture_server.py]
    Restart --> ServiceInfo[返回 self.baseurl<br/>self.prefixes<br/>self.jsonl_path]
    Chk -->|RUNNING exit=0| UI
    Chk -->|NOT_RUNNING exit=1| Start1[后台启动<br/>start.bat]
    Start1 --> Wait1[等 2 秒]
    Wait1 --> ReChk[再次检测]
    ReChk -->|RUNNING| ServiceInfo
    ReChk -->|仍失败| Manual[提示用户<br/>手动双击 start.bat]
    Manual --> F1End([终止])
    Chk -->|PORT_OCCUPIED exit=2| Stop[询问是否运行<br/>stop.bat 释放]
    Stop --> Chk

    ServiceInfo --> UI
    UI[步骤4: 提示用户操作 UI<br/>浏览器代理 127.0.0.1:12138<br/>完成后回复 '继续']
    UI --> UserOp[用户完成 UI 操作]
    UserOp --> Scan[步骤5: scan_page_api.py<br/>增量/全量刷新索引]
    Scan --> Match[步骤6: match_captures.py<br/>生成 capture_selection.md]

    Match --> Stop2[步骤7: AI 停下]
    Stop2 --> Tick[等用户勾选并回复 '已勾选']
    Tick --> Read[步骤8: 读 capture_selection.md<br/>回看 latest.jsonl]

    Read --> ConflictChk{前置A='无新增接口'<br/>但草稿有新接口勾选?}
    ConflictChk -- 是 --> Reject1[打回:<br/>改前置A 或取消勾选]
    Reject1 --> End1([终止])
    ConflictChk -- 否 --> Landing[步骤8: 落点校验<br/>新接口按 pure_path 推荐<br/>已实现接口按索引复用<br/>登录/二进制不入例]
    Landing --> Analyze[步骤9: 分析抓包数据<br/>识别入口 / 区分读写<br/>梳理主线 / 确定依赖]
    Analyze --> Design[步骤10: 设计用例<br/>页面加载合并<br/>写操作独立<br/>依赖链串联]
    Design --> Similar[步骤11: 相似度检查<br/>已有高度相似用例?<br/>询问是否复用/补充/参数化]
    Similar --> Compose[步骤12: 用例编写<br/>按设计清单写方法和 pytest 用例<br/>遵守 coding_style_guide.md]

    Compose --> Verify[步骤13: pytest 闭环]
    Verify --> F1End2([返回总览])
```

### 方式① 关键动作与产物

| 步骤 | 动作 | 产物/输出 |
|---|---|---|
| 1 | 判断是否需要重启 | 用户是否明确提及重启抓包服务 |
| 2 | 二选一处理抓包服务 | 重启：`restart.bat`；未重启：检查端口并按需 `start.bat` |
| 3 | 返回服务信息 | `self.baseurl` / `self.prefixes` / `self.jsonl_path` |
| 4 | 提示用户操作 UI | 浏览器代理与证书提示，完成后回复“继续” |
| 5 | 刷新索引 | `tools/page_api_index.sqlite3` |
| 6 | 生成草稿 | `api_test_dwp_temp/capture_selection.md` |
| 7 | 等用户勾选 | `[x]/[ ]` 标记，AI 不得擅自续跑 |
| 8 | 读勾选结果与落点校验 | 只处理用户确认勾选接口；新接口校验新增前置门禁，已实现接口按索引复用 |
| 9 | 分析抓包数据 | 入口请求、读写类型、业务主线、接口依赖关系 |
| 10 | 设计用例 | 页面加载合并，写操作独立，依赖链串联 |
| 11 | 相似度检查 | 高度相似用例处理建议，按用户确认复用/补充/参数化 |
| 12 | 用例编写 | 新方法写入 `[接口方法文件]`，新用例写入 `[接口用例文件]` |
| 13 | pytest 闭环 | 执行日志 + 通过/失败统计 |

---

## 五、新增方式②：参考已有用例

```mermaid
flowchart TD
    F2Start([方式2 入口]) --> RefChk{用户已指定参考样本?}
    RefChk -- 否 --> AskRef[反问:<br/>请指定 test函数名 或 同类特征]
    AskRef --> RecvRef[收到参考]
    RecvRef --> Read1
    RefChk -- 是 --> Read1

    Read1[Read 参考用例全文<br/>+ 测试类头部]
    Read1 --> Read2[查 page_api_index.sqlite3<br/>确认参考用例调用的方法位置]
    Read2 --> A3Chk{前置A='无新增接口'?}

    A3Chk -- 是 --> Skip[跳过接口查重]
    A3Chk -- 否 --> Diff[从用户业务改动点<br/>判断是否真有新 URL]
    Diff -->|无新 URL| Remind[提醒用户改前置A为<br/>'当前用例无新增接口']
    Remind --> End2([终止等待修正])
    Diff -->|有新 URL| Skip

    Skip --> Clone[仿写用例<br/>复用步骤骨架/参数化/断言风格<br/>沿用 self.xxx 实例名<br/>只改业务语义片段]
    Clone --> Doc[用例 docstring = 用例名]
    Doc --> Verify2[pytest 闭环]
    Verify2 --> F2End([返回总览])
```

### 方式② 关键原则（禁止行为）

| 动作 | 是否允许 |
|---|---|
| 为新用例增加参考没有的能力（如分组、排序） | ❌ 禁止 |
| 把简化参考改成复杂版本 | ❌ 禁止 |
| 为新用例挂 `@pytest.mark.skip` | ❌ 除非用户声明"写占位" |
| 引入参考用例没有的 API 实例 | ❌ 禁止 |
| 修改参考用例本身 | ❌ 禁止（除非用户要求） |

---

## 六、新增方式③：cURL 手工

```mermaid
flowchart TD
    F3Start([方式3 入口]) --> CheckPair{每个接口都有<br/>cURL + 响应体?}
    CheckPair -- 否 --> AskMiss[反问: 缺哪一个]
    AskMiss --> Recv[补齐后继续]
    Recv --> Parse
    CheckPair -- 是 --> Parse

    Parse[逐条解析 cURL<br/>Method / URL / Headers / Body]
    Parse --> Strip[去除硬编码 ETEAMSID<br/>timestamp / Referer / UA]
    Strip --> Dedup[按 pure_path 查索引]

    Dedup --> DedupBranch{命中索引?}
    DedupBranch -- 是 --> Reuse[复用已有方法]
    DedupBranch -- 否 --> NewApiChk{前置A='无新增接口'?}

    NewApiChk -- 是 --> Reject3[打回:<br/>改前置A 或让 AI 找已有替代]
    Reject3 --> End3([终止])
    NewApiChk -- 否 --> NewApi[按前置A位置新增方法]

    Reuse --> Assemble
    NewApi --> Assemble
    Assemble[按 cURL 先后顺序<br/>组装用例步骤]

    Assemble --> Assert[断言取自响应体<br/>code/结构/关键字段/排序值列表]
    Assert --> Verify3[pytest 闭环]
    Verify3 --> F3End([返回总览])
```

### 方式③ cURL 处理清单

| cURL 项 | 处理方式 |
|---|---|
| `-X GET/POST/PUT/DELETE` | 作为接口方法的 method 参数 |
| `--url "https://host/api/xxx?a=1"` | 拆 pure_path + query 参数 |
| `-H "Cookie: ETEAMSID=xxxx"` | 删除硬编码，改用 `login_api_new` 动态获取 |
| `-H "Content-Type: application/json"` | 保留 |
| `-H "Referer: ..."` / `-H "User-Agent: ..."` | 删除，不写入方法 |
| `-d '{"a":1,"timestamp":...}'` | `timestamp/_t` 改为调用时生成 |
| `--data-urlencode` | 按 form 编码落入 payload |

---

## 七、新增方式④：Java Controller 源码参考

```mermaid
flowchart TD
    F4Start([方式4 入口]) --> Source{已提供 Controller 源码<br/>或 Jacoco 链接?}
    Source -- 否 --> AskSource[追问源码文件 / Markdown / Jacoco URL]
    AskSource --> SourceRecv[收到源码信息]
    Source -- 是 --> Analyze
    SourceRecv --> Analyze

    Analyze[执行 analyze_java_controller.py<br/>提取 mapping 并按 api_url+method 查重]
    Analyze --> Draft[生成 java_sourceCode_analysisResult.md<br/>未覆盖接口默认 x<br/>场景分组可编辑]
    Draft --> StopDraft[AI 停下<br/>等待用户调整勾选与分组]
    StopDraft --> Confirm[用户确认按草稿继续]

    Confirm --> ReadDraft[重新读取用户调整后的草稿<br/>只处理保留勾选的接口和场景]
    ReadDraft --> Design[按接口调用链路和业务场景设计用例<br/>写清推断依据]
    Design --> Ref[查找现有相似用例<br/>或读取用户指定参考用例]
    Ref --> Landing{用例文件是否为 _CSC.py?}
    Landing -- 是 --> UseCSC[直接写入专用文件]
    Landing -- 否 --> RemindCSC[仅提醒一次建议使用 _CSC.py<br/>用户坚持则按指定文件]
    RemindCSC --> UseUserFile[按用户指定文件继续]

    UseCSC --> Compose[新增/复用接口方法<br/>编写基础断言 + 打印完整返回]
    UseUserFile --> Compose
    Compose --> Run1[第一次 pytest<br/>获取真实返回]
    Run1 --> Assert[依据真实返回补充断言]
    Assert --> Retry{调试次数 < 3?}
    Retry -- 是 --> Verify[pytest 闭环]
    Verify --> Result{通过?}
    Result -- 是 --> F4End([返回总览])
    Result -- 否 --> Retry
    Retry -- 否 --> Stop3[停止继续尝试<br/>总结请求信息 / payload / 前置变量 / 权限 / 环境等原因]
    Stop3 --> F4End
```

### 方式④ 关键动作与产物

| 步骤 | 动作 | 产物/输出 |
|---|---|---|
| 1 | 读取 Controller/Jacoco | Java 源码、行号、Jacoco `fc`/`nc`/`bnc`（如有） |
| 2 | 提取接口并查重 | 类级 + 方法级 mapping 拼完整 URL，以 `api_url + method` 查 `page_api_index.sqlite3` |
| 3 | 生成可编辑草稿 | `api_test_dwp_temp/java_sourceCode_analysisResult.md` |
| 4 | 用户调整草稿 | 勾选接口、调整场景分组、补充参考用例备注 |
| 5 | 设计用例 | 按调用链路拆分，不机械把所有 `[x]` 接口写成一条用例 |
| 6 | 参考已有用例 | AI 自行检索或按用户指定参考用例复用 fixture、payload、断言风格 |
| 7 | 编写 `_CSC.py` 用例 | 非 `_CSC.py` 只提醒一次，用户可强行指定其它文件 |
| 8 | 两阶段断言 | 先基础断言并打印返回，再按真实返回补充断言 |
| 9 | pytest 闭环 | 最多调试 3 次，不通过则总结原因并停止 |

---

## 八、维护任务总览（入口到方式分流）

```mermaid
flowchart TD
    MStart([维护任务进入]) --> NeedCtx{是否已读取<br/>maintenance_prompt_context.md?}
    NeedCtx -- 否 --> ReadCtx[先读取维护专用上下文]
    NeedCtx -- 是 --> MT
    ReadCtx --> MT[锁定维护目标<br/>用例 / 方法 / 链路]

    MT --> Scope{变更范围清晰?}
    Scope -- 否 --> AskScope[追问影响接口<br/>参考样本 / 抓包 / cURL / 差异点]
    AskScope --> MT2[补齐维护信息]
    Scope -- 是 --> TMode{维护方式已确定?}
    MT2 --> TMode

    TMode -- 否 --> AskMode[照抄四选一菜单<br/>等用户选择维护方式]
    TMode -- 是 --> RunMode[进入维护方式分流]
    AskMode --> RunMode

    RunMode --> M1[维护方式1：抓包驱动]
    RunMode --> M2[维护方式2：参考已有用例]
    RunMode --> M3[维护方式3：cURL 手工]
    RunMode --> M4[维护方式4：pytest 报错驱动]

    M1 --> VerifyM[最小回归 pytest]
    M2 --> VerifyM
    M3 --> VerifyM
    M4 --> VerifyM

    VerifyM --> MEnd([完成维护])

    classDef mWait fill:#fc8,stroke:#c80,color:#000
    classDef mPass fill:#8f8,stroke:#080,color:#000
    class AskScope,AskMode,ReadCtx mWait
    class RunMode,M1,M2,M3,M4,MEnd mPass
```

### 维护任务关键原则

- 先找现有实现，不先假设要新建。
- 先判断“只改用例”还是“方法 + 用例一起改”。
- 变更范围大时优先抓包回溯，变更点明确时优先参考样本或 cURL 快修。
- 用户要求 AI 直接运行目标用例并按报错维护时，使用 pytest 报错驱动；该方式默认先用 `/test-fixing`，维护困难或调用栈/前后接口信息不明确时再用 `/Debugging`。
- 维护场景允许新增方法，但新增只是修补手段，不是任务目标。
- 维护时优先跑受影响用例或最小回归集，不默认全量回归。

---

## 九、维护方式①：抓包驱动

```mermaid
flowchart TD
    M1Start([维护方式1 入口]) --> ScopeChk{受影响范围清晰?}
    ScopeChk -- 否 --> AskScope[追问影响接口 / 用例 / 链路 / 差异点]
    AskScope --> ScopeRecv[收到维护范围]
    ScopeChk -- 是 --> ServiceChk{抓包服务是否可用?}
    ScopeRecv --> ServiceChk

    ServiceChk -- 否 --> Boot[检查 / 启动 / 重启抓包服务]
    Boot --> UI[回溯最新链路并完成 UI 操作]
    ServiceChk -- 是 --> UI

    UI --> Capture[读取 latest.jsonl<br/>必要时刷新索引与勾选草稿]
    Capture --> Compare[对照现有实现<br/>索引复用 / 补丁式修改]
    Compare --> Point[定位维护点<br/>只改断言 / 只改参数 / 方法+用例 / 替代方法]
    Point --> Scenario[按业务场景修补已有用例]
    Scenario --> Verify[最小回归 pytest]
    Verify --> M1End([完成维护])

    classDef m1wait fill:#fc8,stroke:#c80,color:#000
    classDef m1pass fill:#8f8,stroke:#080,color:#000
    class AskScope,ScopeRecv,ServiceChk,Boot,UI,Capture,Compare,Point m1wait
```

### 维护方式① 关键动作与产物

| 步骤 | 动作 | 产物/输出 |
|---|---|---|
| 1 | 锁定影响范围 | 受影响的接口、用例、链路、差异点 |
| 2 | 检查抓包服务 | 是否需要启动 / 重启 / 保持当前服务 |
| 3 | 获取最新链路 | `latest.jsonl`、必要时索引与勾选草稿 |
| 4 | 对照现有实现 | 可复用方法、需补丁方法、受影响用例 |
| 5 | 定位维护点 | 断言 / 参数 / fixture / 调用 / 替代方法 |
| 6 | 按业务场景修补 | 最小范围修复已有用例 |
| 7 | 最小回归 | 受影响用例或最小回归集 pytest |

---

## 十、维护方式②：参考已有用例

```mermaid
flowchart TD
    M2Start([维护方式2 入口]) --> RefChk{已提供参考样本?}
    RefChk -- 否 --> AskRef[追问参考样本函数名 / 文件路径 / 同类样本]
    AskRef --> RefRecv[收到参考样本]
    RefChk -- 是 --> RefRead[读取参考用例全文<br/>+ 测试类头部]
    RefRecv --> RefRead

    RefRead --> IndexChk[查 page_api_index.sqlite3<br/>确认参考用例调用的方法]
    IndexChk --> DiffChk{只影响用例?}
    DiffChk -- 否 --> MethodChk[对照现有方法与索引<br/>判断是否连方法一起改]
    DiffChk -- 是 --> Patch[最小补丁维护<br/>断言 / 参数 / fixture / 调用]
    MethodChk --> Patch

    Patch --> Keep[保持公共骨架与 self.xxx 实例]
    Keep --> Verify[最小回归 pytest]
    Verify --> M2End([完成维护])

    classDef m2wait fill:#fc8,stroke:#c80,color:#000
    classDef m2pass fill:#8f8,stroke:#080,color:#000
    class AskRef,RefRecv,RefRead,IndexChk,DiffChk,MethodChk m2wait
```

### 维护方式② 关键原则（禁止行为）

| 动作 | 是否允许 |
|---|---|
| 为维护用例增加参考没有的能力（如分组、排序） | ❌ 禁止 |
| 把局部修补改成复杂重构 | ❌ 禁止 |
| 为维护用例挂 `@pytest.mark.skip` | ❌ 除非用户声明"写占位" |
| 引入参考样本没有的 API 实例 | ❌ 禁止 |
| 修改参考用例本身 | ❌ 禁止（除非用户要求） |

---

## 十一、维护方式③：cURL 手工

```mermaid
flowchart TD
    M3Start([维护方式3 入口]) --> Pair{每个接口都有<br/>cURL + 响应体?}
    Pair -- 否 --> AskPair[追问缺失的 cURL 或响应体]
    AskPair --> PairRecv[补齐后继续]
    PairRecv --> Parse
    Pair -- 是 --> Parse

    Parse[逐条解析 cURL<br/>Method / URL / Headers / Body]
    Parse --> SmallChk{变更点明确且仅 1-2 个接口?}
    SmallChk -- 否 --> Redirect[建议切换抓包驱动<br/>或参考已有用例]
    SmallChk -- 是 --> Compare[对照现有方法<br/>识别复用 / 补丁 / 替代]

    Compare --> Patch[定点修补用例 / 断言 / 参数 / 方法调用]
    Patch --> Assert[以真实响应重写断言]
    Assert --> Verify[最小回归 pytest]
    Verify --> M3End([完成维护])

    classDef m3wait fill:#fc8,stroke:#c80,color:#000
    classDef m3pass fill:#8f8,stroke:#080,color:#000
    class AskPair,PairRecv,Redirect m3wait
```

### 维护方式③ cURL 处理清单

| cURL 项 | 处理方式 |
|---|---|
| `-X GET/POST/PUT/DELETE` | 作为接口方法的 method 参数 |
| `--url "https://host/api/xxx?a=1"` | 拆 pure_path + query 参数 |
| `-H "Cookie: ETEAMSID=xxxx"` | 删除硬编码，改用登录 fixture 动态获取 |
| `-H "Content-Type: application/json"` | 保留 |
| `-H "Referer: ..."` / `-H "User-Agent: ..."` | 删除，不写入方法 |
| `-d '{"a":1,"timestamp":...}'` | `timestamp/_t` 改为调用时生成 |
| `--data-urlencode` | 按 form 编码落入 payload |

---

## 十二、维护方式④：pytest 报错驱动

```mermaid
flowchart TD
    M4Start([维护方式4 入口]) --> Target{已提供<br/>用例文件 + 目标用例?}
    Target -- 否 --> AskTarget[打回维护 2 项模板]
    Target -- 是 --> ReadTarget[读取目标用例全文<br/>+ 测试类头部 / fixture / 导入]

    ReadTarget --> BuildCmd[组装最小 pytest 命令<br/>文件 + 函数名 / -k 关键字]
    BuildCmd --> RunPytest[执行 pytest]
    RunPytest --> Result{结果?}
    Result -- PASS --> M4End([无需修复或已通过])
    Result -- FAIL --> LastErr[只取最后一个 pytest 中断报错<br/>traceback / assertion diff / exception]
    LastErr --> Analyze[基于最后报错充分分析<br/>导入 / fixture / 断言 / 响应 / 返回层级]
    Analyze --> Classify{分类结果?}

    Classify -- 功能 BUG --> Bug[停止改用例<br/>返回失败接口 / 请求信息 / 真实返回摘要<br/>反馈开发处理]
    Classify -- 不明确 --> Unknown[不修改用例<br/>整理页面复现步骤和待确认点<br/>等用户确认]
    Classify -- 用例待维护 --> TestFix[优先使用 /test-fixing<br/>按错误分组和最小补丁维护]

    TestFix --> NeedDebug{维护仍困难<br/>或前后接口 / 调用栈不明确?}
    NeedDebug -- 否 --> Patch[最小补丁修复目标用例<br/>必要时修接口方法]
    NeedDebug -- 是 --> Debug[切换 /Debugging<br/>在报错或关键接口调用处打断点<br/>获取堆栈 / 局部变量 / payload / 响应 / 返回值]
    Debug --> Patch
    Patch --> RunPytest

    classDef m4wait fill:#fc8,stroke:#c80,color:#000
    classDef m4pass fill:#8f8,stroke:#080,color:#000
    classDef m4reject fill:#f88,stroke:#c00,color:#000
    class AskTarget,ReadTarget,BuildCmd,RunPytest,LastErr,Analyze,Classify,TestFix,NeedDebug,Debug m4wait
    class M4End,Patch m4pass
    class Bug,Unknown m4reject
```

### 维护方式④ 执行清单

| 步骤 | 动作 | 产物/输出 |
|---|---|---|
| 1 | 锁定目标 | `[接口用例文件]` + `[接口用例位置]` |
| 2 | 读取上下文 | 目标用例、测试类头部、fixture、导入和实例 |
| 3 | 运行 pytest | 最小范围命令、执行目录、PYTHONPATH |
| 4 | 取最后报错 | 只以最后一个 pytest 中断 traceback、断言差异、exception 作为分类依据 |
| 5 | 分类处理 | 功能 BUG 停止修改并反馈；不明确时返回复现步骤；用例待维护时进入修复 |
| 6 | 优先 `/test-fixing` | 对用例待维护问题按测试修复流程做最小补丁 |
| 7 | 兜底 `/Debugging` | `/test-fixing` 无法解决或接口前后信息不明确时，打断点并读取堆栈、局部变量、payload、响应和返回值辅助定位 |
| 8 | 循环验证 | 同一最小范围 pytest 直到通过或重新分类为 BUG / 不明确 / 非代码问题 |

---

## 十三、pytest 闭环（新增四方式 / 维护四方式共用）

```mermaid
flowchart TD
    V0([编写 / 维护完成]) --> Enc[UTF-8 校验 + py_compile]
    Enc --> Cwd[切工作目录<br/>E10自动化/接口自动化测试/test_case]
    Cwd --> Env[设置 PYTHONPATH<br/>.]
    Env --> Run[执行 pytest]

    Run --> Result{结果?}
    Result -- PASS --> Rep[输出新增方法/用例清单<br/>+ 通过统计]
    Result -- FAIL --> Diag[失败排查优先级]

    Diag --> D1{ModuleNotFoundError?}
    D1 -- 是 --> FixImport[修 sys.path/PYTHONPATH]
    FixImport --> Run
    D1 -- 否 --> D2{中文乱码/编码?}
    D2 -- 是 --> FixEnc[按 UTF-8 重写]
    FixEnc --> Run
    D2 -- 否 --> D3{fixture/装饰器?}
    D3 -- 是 --> FixFix[调整 fixture 或 skip]
    FixFix --> Run
    D3 -- 否 --> D4{登录态/token?}
    D4 -- 是 --> FixAuth[重新 login_api_new]
    FixAuth --> Run
    D4 -- 否 --> D5{断言不匹配?}
    D5 -- 是 --> FixAsr[按真实返回改断言]
    FixAsr --> Run
    D5 -- 否 --> D6{payload 结构?}
    D6 -- 是 --> FixPl[修 payload]
    FixPl --> Run
    D6 -- 否 --> D7[环境/网络问题<br/>上报用户]
    D7 --> Rep

    Rep --> End([结束])
```

---

## 十四、方式对比速查

| 维度 | 方式1 抓包 | 方式2 参考 | 方式3 cURL | 方式4 Java Controller |
|---|---|---|---|---|
| 典型场景 | 新接口多 / 复杂链路 | 同类用例批量 / 修改参数 | 抓包不可用 / 数据过多 | 后端已有接口定义但自动化未覆盖 |
| 用户准备成本 | 低（UI 操作即可） | 中（指定参考） | 高（收集 cURL + 响应） | 中（提供 Controller/Jacoco） |
| 新接口能力 | ✅ 索引驱动查重 | ⚠️ 默认不新增，必要时新增 | ✅ 按 cURL 新增 | ✅ 按源码提取后查重新增 |
| AI 主观判断 | 低（索引 + 草稿） | 中（仿写需理解参考） | 中（需理解 cURL 语义） | 中高（需设计调用链路和场景分组） |
| 最常见失败 | 登录态 / 浏览器代理 | 参考样本选错 | cURL 不全 / 响应缺失 | payload/前置变量从源码无法完整确定 |
| 闭环严格度 | 强（草稿必停等） | 强（参考必 Read） | 强（cURL+响应必配对） | 强（源码分析草稿必停等，调试最多 3 次） |

### 维护方式速查

| 维度 | 维护方式1 抓包 | 维护方式2 参考 | 维护方式3 cURL | 维护方式4 pytest |
|---|---|---|---|---|
| 典型场景 | 多接口/多用例链路变更 | 单用例或同类用例局部修补 | 1-2 个接口的定点修复 | 直接按失败用例报错修复 |
| 用户准备成本 | 中（提供最新链路） | 低（提供参考样本） | 中（提供 cURL + 响应） | 低（提供目标用例） |
| 链路回溯能力 | 强（按最新链路回溯） | 中（依赖参考样本） | 弱（适合明确变更点） | 中（由报错反推） |
| 维护粒度 | 链路级 | 用例级 | 接口级 / 局部级 | 失败点级 |
| 最常见失败 | 抓包范围不全 | 参考样本选错 | 响应体/差异点不完整 | 报错属于环境/账号/会话问题，或需 `/Debugging` 补充调用栈 |
| 闭环严格度 | 强（最小回归） | 强（目标用例回归） | 强（受影响用例回归） | 强（同一目标 pytest 循环） |

---

## 十五、本流程图与 SKILL.md 的对应关系

| 流程图章节 | SKILL.md 对应章节 |
|---|---|
| 一、总览 | 🚨 前置门禁（按新增 / 维护分流读取） |
| 二、决策闸门 | 前置必跑 0 + `preflight_gates_new.md` / `preflight_gates_maintenance.md` |
| 三、新增任务总览 | `doc/preflight_gates_new.md` + 新增 mode 文件 |
| 四、新增方式① | `doc/mode_capture_driven.md` |
| 五、新增方式② | `doc/mode_reference_case.md` |
| 六、新增方式③ | `doc/mode_curl_manual.md` |
| 七、新增方式④ | `doc/mode_java_controller_source.md` |
| 八、维护任务总览 | `doc/maintenance_prompt_context.md` + 维护 mode 文件 |
| 九、维护方式① | `doc/mode_maintenance_capture_driven.md` |
| 十、维护方式② | `doc/mode_maintenance_reference_case.md` |
| 十一、维护方式③ | `doc/mode_maintenance_curl_manual.md` |
| 十二、维护方式④ | `doc/mode_maintenance_pytest_driven.md` |
| 十三、pytest 闭环 | 核心原则 → 5. 测试必须闭环 |
| 十四、对比速查 | 新增四方式 / 维护四方式共用规范 |
| 附录 A、Hook 触发时序 | 🚨 前置必跑 0（由 hook 自动执行）+ 项目级 `.claude/settings.json` 的 `hooks.PreToolUse` |

---

## 十六、维护说明

- 本文件与 `SKILL.md` 保持**双向一致**：修改任一侧流程，另一侧必须同步
- Mermaid 语法兼容性优先 GitHub 与 VSCode 的 Mermaid 插件
- 如流程图需要导出为图片，推荐 [Mermaid Live Editor](https://mermaid.live/)

---

## 附录 A、PreToolUse Hook 触发时序图

描述 AI 调用 `Skill({skill: "api-test-E10"})` 时，Claude Code 如何同步拦截、spawn `preflight_hook.py`、并把 `preflight_check.py` 的结果注入 AI 上下文的完整链路。

> 配套实现：`hooks/preflight_hook.py` + 项目级 `.claude/settings.json` 的 `hooks.PreToolUse.matcher="Skill"`。

```mermaid
sequenceDiagram
    autonumber
    participant AI as AI (Claude)
    participant CC as Claude Code Harness
    participant HK as preflight_hook.py
    participant PF as preflight_check.py
    participant FS as config.json / sqlite 索引

    Note over AI,CC: 用户触发任务 → AI 决定调用 Skill 工具

    AI->>CC: Skill({skill: "api-test-E10"})
    Note over CC: 拦截工具调用<br/>查 settings.json<br/>命中 matcher: "Skill"

    CC->>HK: spawn 子进程<br/>cwd=会话CWD<br/>stdin=JSON{tool_name, tool_input.skill, cwd, ...}
    activate HK

    HK->>HK: 读 stdin 并解析 tool_input.skill

    alt skill != "api-test-E10"
        HK-->>CC: exit 0（无 stdout 输出）
        Note over CC: 直接放行<br/>不影响其它 skill
    else skill == "api-test-E10"
        HK->>PF: subprocess.run(preflight_check.py)<br/>PYTHONIOENCODING=utf-8<br/>timeout=120s
        activate PF
        PF->>FS: 读 config.json.apiDataUpdateDate
        FS-->>PF: 日期字符串

        alt delta ≤ 7 天
            PF-->>HK: stdout: "数据库中的接口为一周内的最新数据..."<br/>exit 0
        else delta > 7 天
            PF->>FS: 调 scan_page_api.py 增量扫描
            FS-->>PF: 新增接口清单
            PF-->>HK: stdout: [scan_page_api] recent_new_methods<br/>exit 0
        else 日期非法 / 未来日期
            PF-->>HK: stdout: 错误提示<br/>exit 1
        end
        deactivate PF

        HK->>HK: 拼 JSON: {hookSpecificOutput:<br/> {hookEventName, additionalContext}}
        HK-->>CC: stdout 输出 JSON<br/>exit 0（即便 PF 失败也不阻断）
    end
    deactivate HK

    Note over CC: 解析 hookSpecificOutput<br/>把 additionalContext 注入<br/>AI 下一轮上下文

    CC->>CC: 真正执行 Skill 工具<br/>加载 SKILL.md 等

    CC-->>AI: Skill 工具结果 + preflight additionalContext

    Note over AI: AI 同时看到:<br/>① SKILL.md 内容<br/>② preflight 结论<br/>不再需要主动调 preflight
```

### 关键时序约束（看图配套说明）

| 步骤 | 同步/异步 | 失败处理 |
|---|---|---|
| ②→③ harness 调用 hook | **同步阻塞** | Skill 工具不执行直到 hook 退出 |
| ④ hook 解析 stdin | 同步 | JSON 解析失败 → 直接 exit 0 放行 |
| ⑤ skill 名过滤 | 同步 | 不匹配 → 立即 exit 0，不跑 PF |
| ⑥→⑩ spawn preflight | 同步阻塞 | timeout=120s；超时 → 注入诊断信息但 exit 0 |
| ⑪ JSON 输出 | 同步 | 永远 exit 0（PF 失败也不阻断 Skill） |
| ⑫ 注入 additionalContext | 由 harness 处理 | 作为 system 消息进 AI 上下文 |

### 关键设计取舍

- **永不阻断**：即便 preflight 自己崩了，hook 也 exit 0；宁可让 AI 看到诊断信息自行判断，也不要因 hook 故障让 skill 整个不可用。如需强制阻断，把 hook 末尾改成按 `result.returncode` 决定 exit 2。
- **二次过滤放在脚本里**：`matcher: "Skill"` 在 settings 层只能按工具名匹配，无法区分具体 skill 名；脚本内 `skill_name == "api-test-E10"` 这层过滤是必须的，否则任何 Skill 调用都会触发 preflight。
- **CWD 取 payload.cwd**：preflight 子进程的 CWD 是用户会话 CWD（消费方项目），不是 hook 脚本所在目录——这样 `skill_utils/project_root.py` 的 fallback 路径搜索能正确落到消费方项目。


