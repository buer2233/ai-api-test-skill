# 接口编码风格指南

> 本文件从 `SKILL.md` 中拆分。**AI 在编写任何接口方法或用例代码前必须先 Read 本文件并严格遵守所有规范。**

---

## 编写前必检清单

每次编写代码前，确认以下三条：

1. **风格对齐**：方法看目标文件末尾最后 5 个方法，用例看插入点上下文或末尾最后 5 个用例
2. **接口查重**：优先查 `tools/page_api_index.sqlite3`，以 URL `pure_path` + HTTP method 判断是否已覆盖；路径含 `{1}` 等变量时按匹配规则命中复用，未命中按前置 A 位置新增（详见 SKILL.md 核心原则 #3）
3. **编码校验**：写入后重新读取确认新增片段存在、无成片问号乱码、`python -m py_compile` 通过（详见 SKILL.md 核心原则 #2）

---

## 接口方法编写规范

优先对照目标文件**末尾最后 5 个接口方法**，保持风格一致。

### 方法结构

通常应保持如下风格：

```python
def method_name(self, ETEAMSID, status_code=200, response_code=200, **kwargs):
    """中文说明"""
    # Author: dengwanpeng
    # Create Date: YYYY-MM-DD
    url = "https://{0}/api/...".format(self.base_url)
    payload = {
        ...
    }
    error_msg = kwargs.pop("error_msg", "中文错误说明")
    payload.update(kwargs)
    headers = {"Cookie": f"ETEAMSID={ETEAMSID}"}
    res = requests.request("POST", url, headers=headers, json=payload)
    assert res.status_code == status_code, f"{error_msg},接口<{url}>报错-{res.status_code},reason:{res.reason},text:{res.text}"
    response = res.json()
    assert response.get("code") == response_code, f"{error_msg},接口<{url}>报错-{response}"
    return response
```

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

### 取值规则

- 多层取值优先用 `.get_value`
- 单层取值优先用 `.get()`

---

## 接口用例编写规范

优先对照目标文件**插入点上下文**或**末尾最后 5 个用例**，保持风格一致。

### 用例结构

- 用例名遵循当前仓库既有模式，例如：
  - `test_ebuilder_TFAA_xxx`
  - `test_ebuilder_JBA_xxx`
- 用例注释采用分步骤编号：
  - `# 1. ...`
  - `# 2. ...`
- 用例内统一：
  - `# Author: dengwanpeng`
  - `# Create Date: YYYY-MM-DD`

### 常见编排模式

- 先取前置 fixture / 表单 / 页面 / 数据
- 再初始化组件或接口参数
- 再保存页面/组件
- 再查询设计页预览数据
- 再查询前台预览数据
- 最后断言数量、结构、关键字段、排序/过滤结果

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

### 断言风格

- 数量断言：
  - `assert len(...) == expect_count`
- 接口码断言：
  - `assert res.get("code") == 200`
- 结构断言：
  - `assert isinstance(..., list)`
  - `assert "MindMap" in comps_df["type"].tolist()`
- 数据断言优先用**明确的预期值列表**，尤其是排序和分组场景
