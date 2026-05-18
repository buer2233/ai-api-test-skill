# 核心原则详细执行规则

> 本文件是 `SKILL.md` 「核心原则」章节的详细执行规则。**何时 Read 本文件**：
> - 不确定某条原则在具体场景下的判定边界时
> - 触发原则 #3（先复用，后新增）需要看完整 sqlite 索引维护流程时
> - 触发原则 #5（测试必须闭环）需要看 pytest 工作目录/PYTHONPATH/上报口径时
> - 排查"接口方法返回 `response` vs `response.get('data')`"等高频踩坑时
>
> SKILL.md 保留每条原则一句话纲领；本文件补充完整规则细节。

---

## 1. 最小必要改动

- 只在用户指定位置插入或追加
- 不大面积覆盖原文件
- 不擅自重构无关代码
- 不因为局部问题整体改造公共逻辑

---

## 2. UTF-8 与中文安全优先

- 所有目标文件必须按 `utf-8` 读取，并按 `utf-8` 写回
- 不依赖终端中文显示判断文件内容是否正确
- 写入中文后必须至少做一次真实校验：
  - 重新读取文件确认新增片段存在
  - 检查新增片段中不存在成片问号乱码
  - 检查新增中文仍为正常文本
- 如果发现中文异常，先区分是终端显示乱码，还是文件真实内容损坏

---

## 3. 先复用，后新增

### 查重流程

- 新增接口方法前，先按 **URL 的 pure_path** 搜索仓库内是否已有实现
- **优先使用 `tools/page_api_index.sqlite3`**（由 `scan_page_api.py` 生成，纳入版本管理）：
  - 按 `api_url` + `method` 命中即视为已实现；路径含 `{1}` 等变量时按 `skill_utils/api_path_match.py` 的规则匹配
  - 索引条目包含 `api_name`、`api_desc`、`Author`、`Create Date`、`Update Date`、`method`、`class`、`bases`，可判断方法来源
  - 索引时效由前置 0 hook 自动管理（7 天阈值，详见 `doc/preflight_gates.md`「前置必跑 0」）；AI 不再单独判断 24 小时；只在自己手工新增了接口方法后，仍需立即跑一次 `scan_page_api.py` 刷新
- 索引不可用时回退到 grep 搜索，覆盖 `.format()` / `+` 拼接 / f-string 三种 URL 写法
- 搜索范围不要只看当前文件，也要考虑父类、兄弟 API 文件、被当前测试类实例实际继承的 API 类

### 命中与未命中的分支

- 如果 URL 已实现：
  - 直接复用已有方法
  - 用例中按已有调用方式调用
- 如果 URL 未实现：
  - 才新增方法
  - **新增方法后必须同步运行 `tools/scan_page_api.py` 刷新 `tools/page_api_index.sqlite3`**，确保全局索引保持最新

### `tools/page_api_index.sqlite3` 更新方式

1. **扫描新增**：运行 `tools/scan_page_api.py`——库为空时全量重建（id 从 1 起）；库非空时全量扫描后按 `Create Date` 取最近 30 天，与现有 `(api_url, method)` 比对，仅追加新接口
2. **强制重建**：`python tools/scan_page_api.py --full` 清空并重写整表，id 重新从 1 编号
3. **规则扩展**：URL 抽取在 `scan_page_api.py` 的 `URL_EXTRACT_RULES` 追加；HTTP method 抽取在 `REQUEST_METHOD_RULES` 追加（已覆盖 `requests.xxx(...)`、`requests.request("METHOD", ...)`、`self.send_msg("get"/"post", ...)`）；URL 抓包匹配在 `skill_utils/api_path_match.py` 追加

---

## 4. 以真实返回为准

- 断言必须基于**真实接口返回**与**真实运行结果**
- 如果参考结构与实际返回不一致，必须改断言，不要硬套经验
- 要特别警惕"接口方法返回 `response`"与"接口方法返回 `response.get("data")`"这两种不同风格

---

## 5. 测试必须闭环

- 完成代码后必须执行 `pytest`，**默认必须跑到新增用例通过才算完成**（除非用户在当前对话中明确强调不需要跑 pytest）
- 执行前先确认工作目录与 `PYTHONPATH`：
  - 工作目录：`\test-automation\E10自动化\接口自动化测试`
  - `PYTHONPATH`：`\test-automation\E10自动化\接口自动化测试;\test-automation\E10自动化\接口自动化测试\test_case`
- 记录执行目录、`PYTHONPATH`、执行命令、关键日志、报错信息、最终结果
- 如果失败，必须根据真实报错定位并修复，直到通过
- 如果最终通过依赖特定工作目录或 `PYTHONPATH`，必须明确说明
- 如果因为环境问题无法通过，必须区分**代码问题** vs **环境/网络/登录/会话问题**并明确上报用户
