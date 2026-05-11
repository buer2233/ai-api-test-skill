# 高频经验总结

> 本文件从 `SKILL.md` 中拆分，收录编写过程中积累的高频踩坑经验。AI 在遇到相关场景时可参考，不需每次加载。

---

## 1. 先判断"当前测试类真正用的是谁"

例如测试类里常见：

```python
self.eb_page = EBuilderPagePreviewAPI()
```

这意味着：

- 当前用例可调用的方法，不只来自当前文件
- 还可能来自父类或继承链上的其他 API 文件

## 2. `show_list` 不要想当然

- 有些组件支持 `"所有字段"`
- 有些组件只支持真实字段名
- 思维导图尤其要优先验证 `show_list` 是否必须传单字段标题

## 3. 分组/排序/切换视图场景要拆开初始化再组合

当一个初始化函数无法同时稳定返回多个配置块时，可采用：

- 一次初始化切换视图配置
- 一次初始化分组/排序配置
- 最后组合保存

这是当前项目里验证过的稳妥方案。

## 4. 参数化后要同步修断言和文案

- 不要只加 `orderType`
- 要同步修：
  - `error_msg`
  - 预期数据顺序
  - 升序/降序相关断言

## 5. Windows + 中文路径下 `apply_patch` 要直接小块调用

Codex 在 Windows、中文路径、PowerShell 包装叠加时，容易遇到补丁格式、编码、参数长度、路径转义和 BOM 匹配问题：

- 先用 `Get-Command apply_patch` 看是否解析到临时 `apply_patch.bat`；能直接小补丁改文件即视为可用
- 直接用 `functions.shell` 调 `apply_patch`；若出现“requested via shell”只是当前工具入口警告，不等于补丁失败
- 必须使用 `*** Begin Patch` / `*** Update File` / `*** End Patch` 专用格式，不要直接喂标准 unified diff
- 补丁要小，一次只改 1～2 个用例或一个逻辑块，避免 Windows 命令行参数过长
- 路径尽量用仓库相对路径，减少中文路径在多层 shell 中变成 `???` 或找不到文件
- 避免用 PowerShell `Set-Content -Encoding UTF8` 生成待匹配内容；带 BOM 时可能导致 `Failed to find expected lines`
- 不用 `Get-Content | apply_patch`、`cmd /c "apply_patch < file"`；大补丁先拆分，工具链不可用时再说明原因并用无 BOM UTF-8 脚本写回
