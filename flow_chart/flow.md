# api-test-dwp 执行流程图

本文件使用 [Mermaid](https://mermaid.js.org/) 绘制。VSCode / GitHub / Obsidian / Typora 等均可直接渲染。

---

## 一、总览（入口流程）

```mermaid
flowchart TD
    Start([用户触发任务]) --> ExceptCheck{纯查询/工具/诊断类?}
    ExceptCheck -- 是 --> QuickAnswer[直接响应并提示<br/>正式编写需先提交任务信息]
    ExceptCheck -- 否 --> A[前置 A<br/>校验 5 项任务信息]

    A -- 缺任一项 --> ARej[打回：返回填写模板<br/>等用户补齐]
    ARej --> Start

    A -- 5 项齐全 --> A2{[接口方法文件]<br/>与 [接口方法位置]<br/>是否声明<br/>'当前用例无新增接口'?}

    A2 -- 两项同为'无新增接口' --> NoNewApi[登记: 本次不得新增接口<br/>只能复用现有]
    A2 -- 两项均为具体内容 --> HasNewApi[登记: 允许按指定位置<br/>新增接口方法]
    A2 -- 只填一项'无新增接口' --> A2Rej[打回: 必须同时声明]
    A2Rej --> Start

    NoNewApi --> B[前置 B<br/>确认编写方式]
    HasNewApi --> B

    B --> BSig{任务里有<br/>明确方式信号?}
    BSig -- 是 --> BAuto[按信号自动推断<br/>方式①/②/③]
    BSig -- 否 --> BAsk[照抄三选一菜单<br/>等用户回数字]
    BAsk --> BRecv[收到用户回复]

    BAuto --> Todo[TodoWrite 首项:<br/>方式N + 任务信息]
    BRecv --> Todo

    Todo --> Dispatch{方式分流}
    Dispatch -- 方式① --> Flow1[方式1: 抓包驱动]
    Dispatch -- 方式② --> Flow2[方式2: 参考已有用例]
    Dispatch -- 方式③ --> Flow3[方式3: cURL 手工]

    Flow1 --> Pytest[pytest 闭环]
    Flow2 --> Pytest
    Flow3 --> Pytest

    Pytest --> Report[输出新增方法/用例清单<br/>+ 执行结果]
    Report --> End([完成])

    classDef reject fill:#f88,stroke:#c00,color:#000
    classDef pass fill:#8f8,stroke:#080,color:#000
    classDef wait fill:#fc8,stroke:#c80,color:#000
    class ARej,A2Rej reject
    class NoNewApi,HasNewApi pass
    class BAsk,BRecv wait
```

---

## 二、方式①：抓包驱动

```mermaid
flowchart TD
    F1Start([方式1 入口]) --> Chk[check_capture_server.py]
    Chk -->|RUNNING exit=0| UI
    Chk -->|NOT_RUNNING exit=1| Start1[后台启动<br/>start.bat]
    Start1 --> Wait1[等 2 秒]
    Wait1 --> ReChk[再次检测]
    ReChk -->|RUNNING| UI
    ReChk -->|仍失败| Manual[提示用户<br/>手动双击 start.bat]
    Manual --> F1End([终止])
    Chk -->|PORT_OCCUPIED exit=2| Stop[询问是否运行<br/>stop.bat 释放]
    Stop --> Chk

    UI[提示用户操作 UI<br/>浏览器代理 127.0.0.1:12138<br/>完成后回复 '继续']
    UI --> UserOp[用户完成 UI 操作]
    UserOp --> Scan[scan_page_api.py<br/>增量/全量刷新索引]
    Scan --> Match[match_captures.py<br/>生成 capture_selection.md]

    Match --> Stop2[AI 停下]
    Stop2 --> Tick[等用户勾选并回复 '已勾选']
    Tick --> Read[读 capture_selection.md]

    Read --> ConflictChk{前置A='无新增接口'<br/>但草稿有新接口勾选?}
    ConflictChk -- 是 --> Reject1[打回:<br/>改前置A 或取消勾选]
    Reject1 --> End1([终止])
    ConflictChk -- 否 --> Compose[按抓包顺序组装用例<br/>新接口按前置A位置新增<br/>已实现复用<br/>登录/二进制不入例]

    Compose --> Verify[pytest 闭环]
    Verify --> F1End2([返回总览])
```

### 方式① 关键动作与产物

| 步骤 | 动作 | 产物/输出 |
|---|---|---|
| 1 | 探测 12138 端口 | RUNNING / NOT_RUNNING / PORT_OCCUPIED |
| 2 | 启动抓包 | `capture/latest.jsonl` 持续追加 |
| 3 | 刷新索引 | `tools/page_api_index.json` |
| 4 | 生成草稿 | `api-test-dwp/capture_selection.md` |
| 5 | 等用户勾选 | `[x]/[ ]` 标记 |
| 6 | 编写方法与用例 | 新方法写入 `[接口方法文件]`，新用例写入 `[接口用例文件]` |
| 7 | pytest 闭环 | 执行日志 + 通过/失败统计 |

---

## 三、方式②：参考已有用例

```mermaid
flowchart TD
    F2Start([方式2 入口]) --> RefChk{用户已指定参考样本?}
    RefChk -- 否 --> AskRef[反问:<br/>请指定 test函数名 或 同类特征]
    AskRef --> RecvRef[收到参考]
    RecvRef --> Read1
    RefChk -- 是 --> Read1

    Read1[Read 参考用例全文<br/>+ 测试类头部]
    Read1 --> Read2[查 page_api_index.json<br/>确认参考用例调用的方法位置]
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

## 四、方式③：cURL 手工

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

## 五、pytest 闭环（三方式共用）

```mermaid
flowchart TD
    V0([三种方式编写完成]) --> Enc[UTF-8 校验 + py_compile]
    Enc --> Cwd[切工作目录<br/>E10自动化/接口自动化测试]
    Cwd --> Env[设置 PYTHONPATH<br/>接口自动化测试;test_case]
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

## 六、三方式对比速查

| 维度 | 方式1 抓包 | 方式2 参考 | 方式3 cURL |
|---|---|---|---|
| 典型场景 | 新接口多 / 复杂链路 | 同类用例批量 / 修改参数 | 抓包不可用 / 数据过多 |
| 用户准备成本 | 低（UI 操作即可） | 中（指定参考） | 高（收集 cURL + 响应） |
| 新接口能力 | ✅ 索引驱动查重 | ⚠️ 默认不新增，必要时新增 | ✅ 按 cURL 新增 |
| AI 主观判断 | 低（索引 + 草稿） | 中（仿写需理解参考） | 中（需理解 cURL 语义） |
| 最常见失败 | 登录态 / 浏览器代理 | 参考样本选错 | cURL 不全 / 响应缺失 |
| 闭环严格度 | 强（草稿必停等） | 强（参考必 Read） | 强（cURL+响应必配对） |

---

## 七、前置 A / 前置 B 决策闸门

```mermaid
flowchart LR
    Q1[用户请求] --> G1{是编写类任务?}
    G1 -- 否 --> PassThru[例外通道:<br/>查询/工具/诊断]
    G1 -- 是 --> G2{前置A 5项齐全?}

    G2 -- 否 --> Ret1[返回填写模板]
    G2 -- 部分: 只一项填无新增 --> Ret2[返回同填提示]
    G2 -- 是(含双无新增) --> G3{前置B 方式已定?}

    G3 -- 任务有信号 --> Auto[自动推断]
    G3 -- 无信号 --> Ask[三选一菜单]
    G3 -- 用户已回复数字 --> Take[采纳]

    Auto --> Go[进入对应方式流程]
    Take --> Go

    style Ret1 fill:#f88
    style Ret2 fill:#f88
    style Ask fill:#fc8
    style PassThru fill:#8cf
    style Go fill:#8f8
```

---

## 八、本流程图与 SKILL.md 的对应关系

| 流程图章节 | SKILL.md 对应章节 |
|---|---|
| 一、总览 | 🚨 前置必填 A + B |
| 二、方式① | ① 方式1：抓包驱动（推荐） |
| 三、方式② | ② 方式2：参考已有用例（推荐） |
| 四、方式③ | ③ 方式3：cURL 手工（补充） |
| 五、pytest 闭环 | 标准执行流程 → 步骤 5 |
| 六、对比速查 | 三种方式的共用规范 |
| 七、决策闸门 | 前置必填 A / B 校验规则 |

---

## 九、维护说明

- 本文件与 `SKILL.md` 保持**双向一致**：修改任一侧流程，另一侧必须同步
- Mermaid 语法兼容性优先 GitHub 与 VSCode 的 Mermaid 插件
- 如流程图需要导出为图片，推荐 [Mermaid Live Editor](https://mermaid.live/)
