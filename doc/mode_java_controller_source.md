# 方式4：Java Controller 源码参考

> 触发条件：前置 B 选择 ④，或用户明确提供 Jacoco Controller 源码报告链接、Java Controller 源码、Controller Markdown 文件，并要求补齐后端已有但接口自动化未覆盖的接口。

## 强制读取要求

进入本方式后，AI 必须先读取：

1. `doc/coding_style_guide.md`
2. 本文件 `doc/mode_java_controller_source.md`
3. 用户提供的 Jacoco Controller 源码报告链接、Java Controller 源码或 Controller Markdown 文件
4. 若用户提供参考用例，读取参考用例全文及其所属测试类头部

## 输入优先级

| 优先级 | 输入 | 说明 |
|---|---|---|
| 1 | Jacoco HTML 报告链接 | 最推荐；可同时读取源码、行号锚点和 `fc` / `nc` / `bnc` 覆盖染色 |
| 2 | 本地 Java / Markdown 文件 | 例如 `Java-file/java-code1.md`、`Java-file/java-code2.md` |
| 3 | 用户直接粘贴 Controller 源码 | 适合临时分析 |

Jacoco 覆盖染色只作为参考；接口是否已被接口自动化覆盖，最终以 `tools/page_api_index.sqlite3` 中的 `api_url + method` 查重结果为准。

## 执行步骤

1. **确认新增任务门禁已通过**：
   - 必须已有新增任务 5 项信息。
   - 若 `[接口用例文件]` 不是 `_CSC.py` 后缀文件，AI 只提醒一次：建议把 Controller 源码参考新增用例写入 `_CSC.py` 专用文件；用户坚持时允许继续写入原指定文件。
   - `_CSC.py` 命名示例：`test_ebuilder_page_coms_dataDisplay2_api_PC_CSC.py`，`CSC` 表示 `controller_sourceCode`。
2. **生成 Java 源码分析草稿**：
   - 执行 `tools/analyze_java_controller.py --source <源码路径或Jacoco链接>`。
   - 输出文件固定落到项目根 `api_test_dwp_temp/java_sourceCode_analysisResult.md`，除非用户明确指定 `--out`。
3. **分析脚本必须完成以下工作**：
   - 提取类级 `@RequestMapping`。
   - 提取方法级 `@GetMapping` / `@PostMapping` / `@PutMapping` / `@DeleteMapping` / `@PatchMapping` / `@RequestMapping(method=...)`。
   - 拼接完整接口 URL，例如 `/api/bs/ebuilder/app/setting` + `/publish/info` → `/api/bs/ebuilder/app/setting/publish/info`。
   - 使用 `tools/page_api_index.sqlite3` 的 `api_url + method` 判断接口是否已覆盖。
   - 支持 `{module}` / `{submodule}` 这类路径变量按小写英文路径段模糊匹配，例如 `/api/{module}/{submodule}/stage` 可匹配 `/api/bs/ebuilder/stage`。
   - 生成未覆盖接口候选、已覆盖接口、覆盖状态异常、参数来源特殊接口、建议测试场景。
   - 若 JaCoCo 报告中异常数据较多，AI 必须直接回复并在分析草稿前方醒目写入提醒：请先检查当前测试是否失败过多；待通过率较高后使用较新的 JaCoCo 报告分析，或直接使用历史通过率高的测试结果分析。
4. **等待用户调整分析草稿**：
   - `java_sourceCode_analysisResult.md` 是可编辑草稿。
   - 未覆盖接口默认 `[x]` 只是候选池，不代表直接生成一条大用例。
   - 用户可以调整 `[x]` / `[ ]`、移动接口到其它场景、改场景标题、补充参考用例备注。
   - AI 必须停下，等用户确认“已调整 / 按草稿继续”，不得擅自直接写用例。
5. **读取用户调整后的分析草稿**：
   - 只处理用户保留勾选的接口和场景。
   - 用户调整了分组时，以用户调整后的分组为准。
   - 用户备注了参考用例时，以用户备注为优先参考。
6. **接口调用链路与业务分组分析**：
   - 根据接口名、`@ApiOperation`、参数类型、返回语义、service 调用、读写属性、权限前置等信息，推断可能的接口调用链路。
   - 将接口分为可合并的一条业务链路、必须拆分的独立场景、需要前置数据的接口、暂不适合自动编写的接口。
   - 写清楚每条测试场景的推断依据：接口路径与 method、`@ApiOperation` 或方法名、参数来源与类型、service 调用或返回语义、读写属性、相似参考用例命中依据、Jacoco 信息（如有）。
7. **查找参考用例**：
   - 若用户提供参考用例，优先读取并基于该用例扩展未覆盖接口。
   - 若用户未提供参考用例，AI 主动在当前接口自动化用例库中按 controller/module/path 关键词、接口方法名、业务域目录、payload 字段、`@ApiOperation` 中文描述检索相似用例。
   - 参考已有用例的 fixture、前置数据准备、payload 拼接、接口调用顺序、断言风格。
8. **接口方法编写**：
   - 已覆盖接口复用 `tools/page_api_index.sqlite3` 中记录的方法。
   - 未覆盖接口按 `[接口方法文件]` / `[接口方法位置]` 新增。
   - 若新增前置门禁声明“当前用例无新增接口”，但分析草稿存在未覆盖接口 `[x]`，必须打回让用户二选一：改新增前置任务信息，或取消勾选未覆盖接口。
9. **用例编写**：
   - 建议写入 `_CSC.py` 专用文件；若用户坚持其它文件，按用户指定落点写入。
   - `_CSC.py` 内测试类 docstring 必须明确说明：当前类中的用例全部是参考 Controller 源码新增的接口自动化用例。
   - 按用户确认的场景分组编写，不机械按接口列表顺序生成。
10. **两阶段断言与 pytest 闭环**：
    - 第一阶段：只做基础状态/成功状态断言，并打印完整接口返回值。
    - 执行 pytest 获取真实返回。
    - 补充断言后需要删除掉第一阶段新增的打印print()
    - 最后执行 pytest 闭环，直到通过或触发 3 次调试上限。
11. **3 次调试上限**：
    - 基于当前源码信息调试 3 次仍无法通过时，停止继续尝试。
    - 向用户总结无法请求通过的原因，必须判断更可能属于请求信息不正确、payload 缺字段、前置变量错误、登录态/权限不足、环境数据缺失、接口本身不可用等哪一类。

## 覆盖状态异常规则

若 Jacoco 染色与数据库覆盖结论冲突，必须在分析报告和对外回复中提醒用户排查：

- Jacoco 红色/未覆盖，但 `page_api_index.sqlite3` 已记录接口覆盖。
- Jacoco 绿色/已覆盖，但 `page_api_index.sqlite3` 未记录接口覆盖。

## 方式4关键原则

- `java_sourceCode_analysisResult.md` 是门禁草稿：没有用户确认勾选和分组，不得开始生成接口方法或用例。
- 接口是否已覆盖，只以 `api_url + method` 查重结果为准；Jacoco 只做参考。
- Java Controller 只能证明入口契约，不能证明完整 payload 与真实响应；payload 优先参考相似用例，断言以 pytest 真实返回为准。
- 不把所有未覆盖接口机械塞进一条用例，必须按业务链路设计。
- `_CSC.py` 是建议落点，不是硬性强制；用户可强行指定其它文件。
