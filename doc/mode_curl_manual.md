# 方式3：cURL 手工

> 触发条件：前置 B 选择 ③，或用户消息中已粘贴 `curl ...` 命令。

## 强制读取要求

进入本方式后，AI 必须先读取：

1. `doc/coding_style_guide.md`
2. 本文件 `doc/mode_curl_manual.md`
3. 用户提供的每条 cURL 与对应真实响应体

## 执行步骤

1. **收齐 cURL 与响应**：AI 必须确认每个待写接口都有成对的 **cURL 命令 + 真实响应体**。
   - 缺失任一 → 反问用户：`接口 <短描述> 缺 cURL 或响应，请补齐`。
2. **解析 cURL**（按先后顺序一一落位）：
   - 方法：GET / POST / PUT / DELETE / PATCH。
   - URL：提取 `pure_path`（剥 host、去 query）。
   - 请求头：保留 Content-Type；Cookie 整体替换为用例内 `login_api_new` 返回的 ETEAMSID。
   - 请求体：JSON → dict；`application/x-www-form-urlencoded` → 保留 str。
3. **接口查重**：以 `pure_path` + method 查 `tools/page_api_index.sqlite3`。
   - 命中 → 直接复用已有方法。
   - 未命中 → 按 `[接口方法文件]/[接口方法位置]` 新增。
   - 若前置 A 是“当前用例无新增接口”但此处未命中 → **必须打回**，让用户二选一（改前置 A 或改用已有近似方法）。
4. **断言来自响应**：直接基于用户提供的响应体做断言。
   - `code` 断言。
   - 关键字段存在性断言。
   - 有排序/过滤时，优先用明确的预期值列表。
   - 禁止凭空猜测返回结构。
5. **按 cURL 先后顺序组装用例**：每条 cURL 对应一个用例步骤（`# 1. ... # 2. ...`）。
6. **执行 pytest 直到通过**：强制步骤，不得跳过；要求见 `SKILL.md` 的“核心原则 → 测试必须闭环”。

## 方式3关键原则

- cURL 里的 ETEAMSID / token 不直接硬编码到用例，改用登录 fixture 动态获取。
- cURL 里的 `timestamp`、`_t` 等时效性参数不保留原值，改为调用时动态生成。
- cURL 中的 `Referer`、`User-Agent` 等非必需头不写入接口方法，保持方法体精简。
- 一条 cURL 只能证明一个接口调用样例，不代表可以推断其它业务分支。
- 用户没有提供真实响应体时，不允许凭空补断言。
