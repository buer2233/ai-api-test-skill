# 方式 5：API-TPL 驱动新增（一期）

> 触发条件：任务类型为「新增」，且输入来自 git-diff-analyse 分析报告中**人工勾选 `[x]`** 的 `API-TPL-*` 条目；或用户明确说「按 API-TPL / 方式5 / 模版落地」。

---

## 1. 强制读取要求

进入本方式后，AI 必须先读取：

1. `doc/preflight_gates_new.md`（新增前置门禁）
2. `doc/coding_style_guide.md`
3. **本文件** `doc/mode_api_tpl.md`（全文，作为标准执行手册）
4. **`output/<run>/api-landing.md`**（方式5 **专用**精简输入）  
   - **仅含**：接口自动化模版 + 批准勾选 + 采用建议  
   - **禁止**整份读取 `ai-result.md`（噪声大、浪费上下文）  
   - **禁止**用 `functional-cases.html` 写自动化（那是功能复测清单）  
   - 若尚无 `api-landing.md`：先运行  
     `python -m git_diff_analyse export-report-artifacts --evidence output/<run>`  
5. 同目录 `api_signals.json`（参数来源）与 `coverage.json`（查重与落点参考，按需）

> **维护既有用例**请走**维护方式4**，严格按 `doc/mode_maintenance_pytest_driven.md` 执行。  
> **不要**改方式4文档，**不要**把方式5流程写进方式4。未勾选方式4维护项时，**禁止**做维护。

---

## 2. 适用 / 不适用

### 适用

- 覆盖结论为缺口 / 仅有方法无用例，且用户在 `api-landing.md` 中勾选了对应 API-TPL  
- 需要按真实 pytest 闭环补齐 page_api 方法 + 用例  

### 不适用

- 未勾选的 API-TPL（保持 `[ ]`）——**不得**擅自生成  
- 方式4维护勾选区未勾选——**不得**维护已有用例  
- `covered_as_shared` 高扇出——默认不方式5全量补测；除非用户点名单 URL  
- 纯前端无接口功能点——只写功能用例，不走本方式  

---

## 3. 输入与产物边界

| 文件 | 用途 | 方式5是否读 |
|---|---|---|
| `api-landing.md` | 模版 + 勾选 + 采用建议 | **必读，唯一主输入** |
| `api_signals.json` | URL/参数证据 | 按需 |
| `coverage.json` | 查重、cases、建议动作 | 按需 |
| `ai-result.md` | 完整分析（给人读） | **禁止整份加载** |
| `functional-cases.html` | 功能测试复测清单 | **不读**（非自动化） |

覆盖状态对**人类/报告**表述（写用例注释、报告、HTML 时）：

| 机读标签 | 业务表述 |
|---|---|
| L1 命中 / covered_* | **已自动化接口** |
| no_method | **未覆盖的新接口** |
| method_only | 已有接口方法、尚无用例 |

---

## 4. 标准执行步骤（必须按序）

### 步骤 0 — 确认勾选范围

1. 只处理 `api-landing.md` 中 **`[x]`** 的 API-TPL。  
2. 记录每条：id、title、method、path、params、**trigger_steps（触发步骤）**、related_tc、备注（含 `{param}` 特殊说明）。  
3. **trigger_steps 必填来源**：API-TPL 的 `trigger_steps` 字段（与关联功能用例 TC 的操作链路一致，描述前端如何触发该接口）。若模版缺此字段，须从同 run 的 `ai-result.md` 对应 `## TC-*`「操作链路」摘录补全，**禁止编造与业务无关的步骤**。  
4. 方式4维护区若全是 `[ ]`：**跳过维护，零改动既有用例。**

### 步骤 1 — L1 查重（`{param}` 模糊匹配，**全量强制**）

1. 使用 `tools/page_api_index.sqlite3`，按 `api_url + method` 查重。  
2. **禁止**只做字符串全等对比。  
3. **`{param}` / `{module}` 等占位符规则（以后所有接口一律遵守）**：  
   - 表示**可变模块前缀**，可匹配索引路径中 **一个或多个** 路径段；  
   - 其余**字面量段必须完全一致**；  
   - 例：`/api/{param}/groupchat/create` **匹配** `/api/ebuilder/form/groupchat/create`；  
   - 实现：`skill_utils/api_path_match.py` → `api_path_matches` / `_param_multi_segment_match`；  
   - 覆盖机打表同样规则（`git_diff_analyse.coverage.paths_structurally_compatible`）。  
4. 模糊命中已有方法：**不得重复新增**；复用既有方法与 URL 落点写法。  
5. 未命中：进入步骤 2 新增。

### 步骤 2 — 定落点

1. 优先 `placement_hints`。  
2. 其次：同模块已有 page_api 目录、模糊匹配到的既有文件、CodeGraph/目录约定。  
3. `{param}` 命中后，**新方法 URL 必须写成索引中的真实路径**（如 `ebuilder/form/...`），不要把字面量 `{param}` 写进代码。  
4. page_api URL 拼接须与**同类文件既有写法一致**：  
   - 若该类 `base_url` 已含协议（如 `EbuilderWorkFlowApprovalProcess` / `doShareDatas`）：用 `"{0}/api/..."`.format(self.base_url)  
   - 若 `base_url` 仅为 host（如多数 `ebuilder_form_*`）：用 `"https://{0}/api/..."`.format(self.base_url)  
   - **禁止**双写 `https://` 导致 `host=https` 连接失败。

### 步骤 3 — 编写 page_api 方法

1. 严格遵循 `coding_style_guide.md`（结构、IsAI、error_msg、返回值等通用规范）。  
2. 参数：优先 `api_signals` / API-TPL；**有则填、无则空**；禁止编造字段名。  
3. **方式5 专属强制：方法 docstring 必须含 `触发步骤:`**（不写在通用 coding_style_guide，仅本方式要求）：  
   - 字面量前缀 **`触发步骤:`**，不可改成「操作路径」「步骤」等别名；  
   - 内容 = API-TPL 的 `trigger_steps`（前端如何操作才会打到该接口），与功能用例分步风格一致；  
   - 有 related_tc 时必写 `来源功能用例: TC-xxx`；  
   - 示例：

```python
def getShareBaseInfo(self, ETEAMSID, objId, status_code=200, **kwargs):
    """EB表单数据-共享-获取共享基础信息（批量共享前置）

    触发步骤:
    1. 打开移动端建模列表运行页，定位目标数据行
    2. 进入共享设置/共享列表（进入时触发本接口）
    3. 新增共享对象并保存
    来源功能用例: TC-001-mobile-list-share
    """
    # Author: Author
    # Create Date: YYYY-MM-DD
    # IsAI: True
    ...
```

4. 复用已有方法时：若 docstring 尚无 `触发步骤:`，**补写**（不重复造方法）；并确认返回层级（完整 response / `data` / 业务 dict）。  
5. 缺 `触发步骤:` 的新增方法 = **不合格交付**，不得进入 pytest 收尾。

### 步骤 4 — 编写 pytest 用例（前置强制）

#### 4.1 EB 表单数据前置（强制）

涉及表单/数据/共享/群聊/列表动作时，**必须**用成熟前置，禁止空 `data_details=[]` 手搓：

```python
# 对齐 test_ebuilder_page_case/conftest.py common_ebForm_data（约 L393-401）
form_name = f"通用EB表单数据:..."
add_data = ["测试数据1", "测试数据2", "筛选数据1", "筛选数据2"]
form_res = eb_form.add_form_data(ETEAMSID, app_id, form_name, add_data=add_data)
# 使用 form_res["form_id"] / ["formId"] / ["listId"] / ["data_ids"] / ["formField_id"] ...
```

- 需要 `dataId` 的接口：断言 `data_ids` 非空后再调。  
- 需要共享 id 的接口：先 `doShareDatas`，再 `getShareList`，从 **`shareListEntities` / `shareDatas`** 取 id（不要只认 `displayData`）。  
- 需要 `actionId`：取按钮 **`actions[].id`**，不是 `button.id`。  
- 需要群聊 `buttonId`：从 `button_getButtonList` / `form_getListButtons` 找「事项群聊」；**禁止空 buttonId**（会系统错误）。

#### 4.2 用例标题语义化（方式5 强制）

pytest 用例 **docstring 标题**必须在基础说明后追加 **`——` + 语义化备注**，一眼能看清「这个用例测了什么」：

| 不合格 | 合格 |
|---|---|
| `方式5-API-TPL-001 共享基础信息 getShareBaseInfo` | `方式5-API-TPL-001 共享基础信息 getShareBaseInfo——验证进入共享设置时可取到共享基础配置` |
| `方式5-API-TPL-005 事项群聊创建` | `方式5-API-TPL-005 事项群聊创建——验证未建群时按向导创建群聊接口可成功返回` |

规则：

1. 格式：`{TPL/接口简述}——{验证点：谁在什么场景下期望什么}`  
2. 备注用业务语言，不写内部实现细节堆砌  
3. **缺 `——` 语义备注的用例标题 = 不合格交付**

#### 4.3 用例编写纪律

1. 优先对齐目标文件插入点上下文或末尾用例风格。  
2. **禁止**用 `try/except` 吞掉主路径失败后 `print` 继续或 `pytest.skip`「环境不足」。  
3. **禁止** `assert x or True`、空成功断言等假绿。  
4. 断言必须基于**真实返回结构**（`code`、`data`、业务字段如 `isSuccess`）。  
   - 例：`conditionCheck` 不能只断言 `code==200`；必须 `data.isSuccess is True`，且 `conditionStr` 为合法 `json.dumps({"sql": "..."})`（参考 nListView 既有用法）。  
5. 失败时 assert 消息带上完整 `res=`，便于调试。

#### 4.4 调试阶段 vs 交付阶段（强制）

| 阶段 | 要求 |
|---|---|
| **调试中** | 可临时 `print` 完整响应；**多次** pytest；按真实返回改参数/断言，直到全绿 |
| **pytest 已通过后** | **必须删除**调试 `print` / 临时 dump；交付干净用例 |
| **禁止** | 为通过而 skip；调试通过后仍保留大段打印 |

### 步骤 5 — pytest 闭环

工作目录与 `PYTHONPATH`（强制）：

```text
cd <project>/E10自动化/接口自动化测试/test_case
PYTHONPATH=.   # 或 PowerShell: $env:PYTHONPATH = "."
pytest <用例相对路径> -v --tb=short
```

1. 最小范围跑目标文件/目标函数。  
2. 失败 → 根据真实返回修 page_api 或用例 → 再跑，直到通过。  
3. 建议通过后**再跑一遍**确认稳定（两次独立运行，非复制日志）。  
4. 通过后执行步骤 4.4：删除调试打印。

### 步骤 6 — 刷新 page_api_index

新增方法后按 skill 要求扫描/更新 `tools/page_api_index.sqlite3`，保证 L1 可查。

### 步骤 7 — 停止并交付

1. 输出：新增方法列表、用例列表、pytest 命令与结果、diff 摘要。  
2. **禁止 `git commit` / `git push`**。  
3. 等人 review 后由人工提交。

---

## 5. 门禁速查

| 允许 | 禁止 |
|---|---|
| 改 `test-automation` 下接口方法与用例 | `git commit` / `git push` |
| 按 core_principles 跑 pytest | hard-reset 清用户本地改动 |
| 更新 `page_api_index.sqlite3` | 处理未勾选 API-TPL |
| 调试期打印真实返回 | 编造 URL / 参数名 |
| 通过后删除调试打印 | 整份读 `ai-result.md` 做方式5 |
| 方法备注写 `触发步骤:`（来自 TPL/TC） | 新增方法缺 `触发步骤:` |
| 用例 docstring 含 `——` 语义备注 | 用例标题无语义备注 |
| | 编造与功能用例无关的触发步骤 |
| | `try/skip` 吞主路径失败 |
| | 假绿断言（`or True` 等） |
| | URL 全等匹配忽略 `{param}` |
| | 改方式4 skill 正文 |

---

## 6. 输出模板

```text
【方式5 API-TPL 落地】
TPL: API-TPL-xxx
URL: ...
动作: 新增方法 / 复用已有方法 / 新增用例

【新增/复用接口方法】(N个)
方法名: ...
触发步骤: 已写入 docstring（来源 TC-xxx / API-TPL trigger_steps）

【新增接口用例】(N个)
用例名: ...——语义化验证点（已写）

pytest 命令
cd .../test_case && PYTHONPATH=. pytest <path> -v --tb=short

结果
N passed

调试打印: 已删除（若曾添加）
触发步骤: 全部新增/复用方法已含「触发步骤:」

【停止】未执行 git commit / push，请人工审查后提交。
```

---

## 7. 与其它方式的关系

| 方式 | 文档 | 典型输入 |
|---|---|---|
| ① 抓包 | `mode_capture_driven.md` | 抓包 JSONL |
| ② 参考用例 | `mode_reference_case.md` | 已有相似用例 |
| ③ cURL | `mode_curl_manual.md` | 手工 cURL |
| ④ Controller | `mode_java_controller_source.md` | Java/Jacoco |
| **⑤ API-TPL** | **本文件** | **`api-landing.md` 已勾选模版** |

- 方式5 缺 payload 时可再读 Controller/抓包补证据，但 URL 不得偏离 TPL/signals。  
- **方式4 保持独立**：维护时只读方式4文档；目标可参考 `coverage.json` 的 `cases[]`，**不自动 dump** `covered_as_shared`。

---

## 8. 参考实现（本仓库）

- 用例样例：`test_case/test_eBuilder_case/test_ebuilder_form_case/test_ebuilder_form_view_case/test_ebuilder_form_api_tpl_landing_api.py`  
- 前置样例：`test_ebuilder_page_case/conftest.py` → `common_ebForm_data`（`add_form_data` + `add_data`）  
- 路径匹配：`skill_utils/api_path_match.py`  
- 分析侧导出：`python -m git_diff_analyse export-report-artifacts --evidence output/<run>`
