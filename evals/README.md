# api-test-E10 Evals

本目录存放 `api-test-E10` 的触发评估测试集与运行产物。

## 结构

```
evals/
├── README.md
├── trigger_eval_set.json          # 标准触发集（query + should_trigger，兼容 skill-creator run_loop）
├── workflow_eval_set.json         # 执行契约集（分流、必读文档、产物与副作用）
├── validate_eval_set.py            # workflow_eval_set.json 的无网络校验器
├── git_readiness_check.py          # 只读 Git 提交阻断项检查器
└── trigger-eval/                  # 触发评测工作区（原 api-test-E10-workspace/trigger-eval）
    ├── trigger_eval_set.json      # 带 id / branch / category 的完整版
    ├── branch_coverage.md         # 分支覆盖与指标说明
    ├── eval_review.html           # 人工审阅页
    ├── run_trigger_eval_win.py    # Windows 兼容 runner（checkpoint 续跑）
    ├── full_results.md            # 最近一次完整报告（本地生成，默认忽略）
    ├── full_results.json           # 最近一次完整报告（本地生成，默认忽略）
    └── ...                        # 日志 / checkpoint / smoke 等运行产物
```

## 当前阶段目标

1. 整体触发成功率（该触发 / 不该触发）
2. 不同分支执行路径触发成功率（新增 4 路 + 维护 4 路 + 工具/边界 + 负例）
3. 触发后的流程契约：任务类型/方式分流、门禁文档读取、交付物和禁止副作用

## Workflow 契约评估

`workflow_eval_set.json` 不直接调用模型，作为人工评审或后续自动 grader 的稳定输入。每条记录都固定了任务分支、必须读取的文档、预期交付物、必须做到和禁止副作用，避免只用关键词判断技能质量。

先运行静态校验：

```bash
python validate_eval_set.py
```

该校验会检查 JSON schema、ID 唯一性、必读文档存在性，以及新增/维护四路、工具边界和负例分支是否齐全。

提交前运行只读审计：

```bash
python git_readiness_check.py --repo-root "D:/workSpace_001/test-automation"
```

审计不会删除或修改文件；发现明文账号文件、运行时产物或不符合规范的技能名时返回非零退出码，并且不会打印凭据内容。

## 快速重跑

在 skill 根目录或本 `trigger-eval` 目录执行：

```bash
cd ".claude/skills/api-test-E10/evals/trigger-eval"
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

> 说明：skill-creator 自带 `run_eval.py` 在 Windows 上因 `select()` 限制不可用，请优先用 `run_trigger_eval_win.py`。

触发 runner 会把超时、无信号和进程错误标记为 `INCONCLUSIVE`，不再把基础设施问题折算成“不触发”。`accuracy` 只在有明确触发/不触发结论的样本上计算，同时单独报告不确定数量。
