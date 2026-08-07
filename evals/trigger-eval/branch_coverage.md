# api-test-E10 触发评估测试集说明

## 评估目标（当前阶段）

1. **整体触发成功率**：description 能否让模型在“该用 skill 时触发 / 不该用时不触发”
2. **分支路径触发成功率**：覆盖新增 4 路 + 维护 4 路 + 工具/边界 + 近邻负例

> 本阶段**只做触发评估**，不做完整执行链路（不真正写用例、不跑抓包闭环）。

触发 runner 的超时、无信号和进程错误会标记为 `INCONCLUSIVE`，不会作为负例参与准确率分母；报告同时给出 `assessed` 和 `inconclusive`，避免把 Windows/网络波动误判为技能缺陷。

## 测试集结构

| 类型 | 数量 | 说明 |
|---|---:|---|
| Should Trigger | 18 | 应触发本 skill |
| Should NOT Trigger | 9 | 近邻负例（故意带相关关键词） |
| **合计** | **27** | |

## 分支路径覆盖（Should Trigger）

| 分支 ID | 路径 | Eval IDs | 说明 |
|---|---|---|---|
| `new/capture_driven` | 新增-抓包驱动 | 1 | 明确 12138 / 抓包 |
| `new/reference_case` | 新增-参考已有用例 | 2 | 指定参考用例 + 差异点 |
| `new/curl_manual` | 新增-cURL手工 | 3 | 贴 cURL + 响应 + 任务信息 |
| `new/java_controller` | 新增-Java/Jacoco | 4, 5 | 本地 Controller + Jacoco URL |
| `maintenance/capture_driven` | 维护-抓包驱动 | 6 | 维护任务信息 + 抓包 |
| `maintenance/reference_case` | 维护-参考已有用例 | 7 | 断言/参数化风格对齐 |
| `maintenance/curl_manual` | 维护-cURL手工 | 8 | 定点修 payload |
| `maintenance/pytest_driven` | 维护-pytest报错驱动 | 9 | 自行执行并修到通过 |
| `utility/url_dedup` | 工具-URL查重 | 10 | description 明确覆盖场景 |
| `utility/encoding_fix` | 工具-编码修复 | 11 | UTF-8 / 乱码 |
| `new_or_maintenance/parametrize` | 参数化补齐 | 12 | 补参数化+断言同步 |
| `new/api_tpl` | 新增-API-TPL驱动 | 23, 24, 25 | 方式5 api-landing 模版落地 |
| `new_or_maintenance/generic_new` | 新增-通用补齐（非方式5） | 27 | ai-result 通用补齐，不走方式5 |
| `maintenance/refactor_existing` | 边界-整理已有用例 | 21 | 维护边界，期望触发 |
| `utility/pytest_inventory` | 边界-pytest摸底 | 22 | 只摸底不改代码，期望触发 |

## 负例设计原则（Should NOT Trigger）

负例**故意**带 `pytest` / `接口` / `mitmproxy` / `E10自动化` / `报告` 等关键词，避免“完全无关”的假阴性测试：

| 分支 ID | Eval IDs | 易混淆点 |
|---|---|---|
| `negative/ui_automation` | 13 | E10 但 UI/Selenium |
| `negative/unit_test` | 14 | pytest 但纯单元 |
| `negative/frontend` | 15 | `/api` 但前端 axios |
| `negative/ci_config` | 16 | “接口自动化 job” 但只改 Jenkinsfile |
| `negative/tool_howto` | 17 | mitmproxy 科普，不写用例 |
| `negative/ui_pageobject` | 18 | E10自动化 但 UI PageObject |
| `negative/backend_sql` | 19 | 业务表变更，不动测试 |
| `negative/report_style` | 20 | 报告但 Allure/UI |
| `negative/api_tpl_readonly` | 26 | api-landing 但只读查看不落地 |

## 指标怎么算

### 1) 整体触发成功率

对每条 query 跑 N 次（`run_loop` / `run_eval` 默认 3 次），得到 trigger rate ∈ [0,1]。

- **正例准确率 (Trigger Recall)** = 正例中判定为触发的比例
- **负例准确率 (Non-trigger Precision 侧)** = 负例中判定为不触发的比例
- **Overall Accuracy** = 已获得明确触发结论的 query 中 “预测==标注” 的比例；超时/无信号的 query 进入 `INCONCLUSIVE`，不计入该分母

### 2) 分支路径触发成功率

对每个 `branch` 聚合其下属 query 的平均 trigger rate：

```text
branch_trigger_rate(branch) = mean(trigger_rate(q) for q in branch)
```

建议重点盯：

- 9 条主执行路径（new×5 + maintenance×4）是否都能稳定 > 0.8
- 边界正例 21/22 是否误伤为不触发
- 近邻负例 13–20 是否被关键词误触发

## 文件位置

本目录已并入 skill 内：`api-test-E10/evals/trigger-eval/`。

| 文件 | 用途 |
|---|---|
| `evals/trigger_eval_set.json` | 标准触发评估输入（run_loop 兼容，仅 query + should_trigger） |
| `evals/trigger-eval/trigger_eval_set.json` | 带 id/branch/category 的完整版 |
| `evals/trigger-eval/branch_coverage.md` | 本说明 |
| `evals/trigger-eval/eval_review.html` | 人工审阅页 |
| `evals/trigger-eval/run_trigger_eval_win.py` | Windows 兼容触发评估 runner（支持 checkpoint） |
| `evals/trigger-eval/full_results.md` | 最近一次完整触发评估报告 |

## 下一步

1. 你在 HTML 审阅页里改 query / 切换 should_trigger / 增删条目
2. Export 后把结果同步回 `evals/trigger_eval_set.json` 与本目录 annotated 版
3. 确认后可跑（Windows 推荐本目录 runner）：

```bash
cd "D:/workSpace_001/test-automation/.claude/skills/api-test-E10/evals/trigger-eval"
python run_trigger_eval_win.py \
  --eval-set "../trigger_eval_set.json" \
  --annotated-set "./trigger_eval_set.json" \
  --skill-path "D:/workSpace_001/test-automation/.claude/skills/api-test-E10" \
  --project-root "D:/workSpace_001/test-automation" \
  --output "./full_results.json" \
  --checkpoint "./full_results.checkpoint.json" \
  --num-workers 2 \
  --timeout 90 \
  --runs-per-query 3 \
  --verbose
```
