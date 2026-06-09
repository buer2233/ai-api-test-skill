# 接口编码风格指南

> 本文件从 `SKILL.md` 中拆分。**AI 在编写任何接口方法或用例代码前必须先 Read 本文件并严格遵守所有规范。**

---

## 编写前必检清单

每次编写代码前，确认以下四条：

1. **风格对齐**：接口方法编写不参考上下文，严格遵守本文件的接口方法编写规范。接口用例编写看插入点上下文或末尾最后 5 个用例
2. **接口查重**：优先查 `tools/page_api_index.sqlite3`，以 URL `pure_path` + HTTP method 判断是否已覆盖；路径含 `{1}` 等变量时按匹配规则命中复用，未命中按新增前置门禁指定位置新增（详见 SKILL.md 核心原则 #3）
3. **真实返回**：抓包生成接口用例需要先看抓包 / cURL / pytest 的实际 response body；没有真实返回时不凭空补断言
4. **编码校验**：写入后重新读取确认新增片段存在、无成片问号乱码、`python -m py_compile` 通过（详见 SKILL.md 核心原则 #2）
5. **查找已实现接口方法**：查找已实现的接口方法时,优先查 .claude/skills/api-test-E10/tools/page_api_index.sqlite3(api_methods 表,按
  ▎ api_url/api_name/api_desc 检索),而非全仓库 grep。
---

## 接口方法编写规范

### 方法结构

必须严格按照下面的格式编写接口方法，不能参考现在已有上下文的接口方法。

```python
def method_name(self, ETEAMSID, status_code=200, **kwargs):
    """中文说明"""
    # Author: Author
    # Create Date: YYYY-MM-DD
    # IsAI: True
    url = f"https://{self.base_url}/api/..."
    payload = {
        ...
    }
    error_msg = kwargs.pop("error_msg", "中文错误说明")
    payload.update(kwargs)
    headers = {"Cookie": f"ETEAMSID={ETEAMSID}"}
    res = requests.request("POST", url, headers=headers, json=payload)
    assert res.status_code == status_code, f"{error_msg},接口<{url}>报错-{res.status_code},reason:{res.reason},text:{res.text}"
    return res.json()
```

### 返回值规则

返回值按实际 response body 选择，参考示例即可：

```python
# JSON 且有内容
return res.json()

# 纯文本 / HTML / 非 JSON
return res.text

# 可能空返回
return res.json() if res.text else res.text
```

复用已有接口方法时，先确认它返回的是完整 `response`、`response.json()`、还是 `response.get("data")`。

### 方法命名

- 方法名保持**短、稳、清晰**
- 优先体现：模块 + 资源 + 动作
- 不把整条业务中文全拼进方法名
- 忽略无意义层级：`api`、`bs`、`web`、`common` 等
- 优先沿用仓库已有前缀风格，如：`ebPage`、`ebApp`、`intdevice`
- 示例：
  - `/api/bs/ebuilder/page/config/update` → `ebPage_config_update`
  - `/api/intdevice/common/browser/data/useModuleBrowser` → `intdevice_useModuleBrowser_data`

### payload 规则

- 默认值优先直接写在 `payload` 中
- 非必要不要把简单默认值提升为方法参数
- AI 生成的可自定义值（名称、标题、描述等）必须加 `ai` 前缀，例如：`"ai" + strftime("%Y%m%d%H%M%S")`

### 取值规则

- 多层取值优先用 `.get_value`
- 单层取值优先用 `.get()`

---

## 接口用例编写规范

- 优先对照目标文件**插入点上下文**或**末尾最后 5 个用例**，保持风格一致。
- 新增的接口自动化用例不能写成单接口用例；必须依据已有参考接口用例、抓包数据、cURL、Java Controller 源码等材料进行深入分析，梳理前置准备、核心操作、后置校验等完整调用链路，生成符合真实业务测试流程的完整接口自动化测试用例。

### 用例结构

- 用例名遵循当前仓库既有模式，例如：
  - `test_ebuilder_TFAA_xxx`
  - `test_ebuilder_JBA_xxx`
- 同一功能点连续新增多个用例且目标文件无固定编号模式时，使用两字母后缀：`AA`、`AB`、`BA`、`BB`
- 用例注释采用分步骤编号：
  - `# 1. ...`
  - `# 2. ...`
- 用例内统一：
  - `# Author: Author`
  - `# Create Date: YYYY-MM-DD`
  - `# IsAI: True`

### 常见编排模式

- 先取前置 fixture / 表单 / 页面 / 数据
- 实际的用例执行步骤
- 最后断言数量、结构、关键字段、排序/过滤结果
- 正常场景优先使用管理员凭证，例如：`ETEAMSID = self.ETEAMSID_admin`
- Cookie / token 不硬编码，复用项目已有登录 fixture 或 API

### 参数化

- 参数化优先采用：

```python
@pytest.mark.parametrize(
    "param1, param2, msg",
    (
            (...),
            (...)
    ),
    ids=(...)
)
```

- 当参数化影响断言时，`error_msg` 和预期值也必须同步参数化，不允许写死"升序"等固定文案
- `ids` 必须使用英文，禁止中文

### 断言风格

- 断言前先看真实 response body，按以下优先级选择：

| 返回特征 | 断言示例 |
|---|---|
| 有 `code` | `assert res.get("code") == 200` |
| 无 `code`，有 `msg` | `assert res.get("msg")` |
| 无 `code` / `msg`，有 `message` | `assert res.get("actionMsg", {}).get("message") == "删除成功"` |
| 以上都没有 | `assert res` |

- 数量断言：
  - `assert len(...) == expect_count`
- 接口码断言：
  - `assert res.get("code") == 200`
- 结构断言：
  - `assert isinstance(..., list)`
  - `assert "MindMap" in comps_df["type"].tolist()`
- 数据断言优先用**明确的预期值列表**，尤其是排序和分组场景
- 嵌套字段按实际路径断言：

```python
assert res.get("actionMsg", {}).get("code") == 100
assert res.get("data", {}).get("actionMsg", {}).get("message") == "Successfully"
assert res.get("resultJson", {}).get("data", {}).get("expressSql") == exp_sql
```

- 非 JSON 返回按实际文本 / 空响应断言，不使用 `.get()`
- 断言异常提示统一用 f-string，并带上接口返回：`f"接口说明, 接口异常{res}"`
