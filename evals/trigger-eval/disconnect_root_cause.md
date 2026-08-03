# 触发评估“执行到一半断开”根因分析

## 结论（不是评估逻辑随机崩溃）

完整 22 条 × 3 次 = **66 次** `claude -p` 调用。上一次中断的主因是：

1. **外层工具超时（硬杀）**  
   Claude Code 的 Bash 工具默认/设置了约 **10 分钟**超时。  
   日志显示进程在 `36/66` 左右停止，退出形态为 `Exit code 143`（SIGTERM 类终止），且**没有写出** `full_results.json`。  
   这说明是**父进程/工具层超时杀掉整批 Python**，不是 Python 自己抛异常退出。

2. **单次查询偏慢 + 并发放大总时长**  
   - 实测单次 `claude -p` 到首个 tool 决策约 **28s**（`--max-turns 1` 后）。  
   - 旧配置：`timeout=60`、`num_workers=3`、每 query 3 次。  
   - 粗算：`66 × ~30s / 3 workers ≈ 11 分钟`，已经贴近/超过 10 分钟外层超时。  
   - 一旦 API 变慢或某些 query 等到 60s timeout，总时长更容易突破 10 分钟。

3. **单 query 的 MISS/timeout ≠ 整批断开**  
   旧日志中：
   - 已完成 36 个 job
   - HIT 15 / MISS 21
   - MISS 里 timeout 18、no_signal 3  
   这些是**单次调用超时/无信号**，评估仍会继续。  
   真正导致“整批停掉、无最终报告”的是外层 10 分钟硬杀。

## 次要干扰因素

| 因素 | 影响 | 处理 |
|---|---|---|
| Windows 下 `select()` 不可用于 pipe | skill-creator 原版 `run_eval.py` 直接不可用 | 改用 `run_trigger_eval_win.py` 线程读 stdout |
| Python 找不到 `claude` 可执行文件 | 扩展名脚本无法被 CreateProcess | 改用 `claude.cmd` |
| 无断点续跑 | 超时后 36 条进度丢失 | 增加 checkpoint，每完成 1 job 落盘 |
| 控制台 GBK 编码 | 日志中文乱码/个别 print 编码异常 | runner 强制 UTF-8 reconfigure |

## 本次优化

1. `--max-turns 1`：只等到首次 tool 决策，避免 skill 真正执行业务  
2. `--no-session-persistence`：减少磁盘会话开销  
3. `timeout=90`：给慢请求余量，减少误判 timeout  
4. `num_workers=2`：降低并发争抢/限流  
5. **checkpoint 断点续跑**：`full_results.checkpoint.json`，中断后可接着跑  
6. **增量报告**：每完成 1 job 就刷新 `full_results.json/.md`  
7. 后台长时运行 + 更高外层超时，避免 10 分钟硬杀

## 如何判断下次是否“正常跑完”

- 日志出现 `Results: x/y passed`  
- `jobs_completed == jobs_expected`（期望 66/66）  
- 存在 `full_results.json` 与 `full_results.md`  
- checkpoint 中 jobs 数量 = 66  
