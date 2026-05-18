# capture - 抓包底座使用指引

> 目标读者：首次使用本 Skill 的测试同学；零 mitmproxy 基础也能跟完。

## 1. 环境准备

### 1.1 Python

```bat
python --version
```

需要 3.8 及以上。

### 1.2 安装 mitmproxy

```bat
pip install mitmproxy
```

安装后验证：

```bat
mitmdump --version
```

如看到 `Mitmproxy: x.y.z` 即成功。

## 2. 首次启动（手动）

### 2.1 双击 `start.bat`

或命令行：

```bat
cd api-test-E10\capture
mitmdump -s capture_addon.py --listen-port 12138
```

### 2.2 看到以下日志表示成功

```
[api-test-E10] self.baseurl = weapp.mulinquan.cn
[api-test-E10] self.prefixes = ['/api/', '/sapi/', ...]
[api-test-E10] self.jsonl_path = ...\api_test_dwp_temp\latest.jsonl
Proxy server listening at *:12138
```

**如果 `self.baseurl = <empty>`**：说明没找到 `E10自动化/接口自动化测试/config.py`，或其 `RunConfig.baseurl` 被注释。请手动打开 config.py 确认当前启用的 baseurl 没被井号注释。
启动成功后，addon 会通过 `skill_utils/common_function.py` 的通用配置更新方法，把当前解析到的 `RunConfig.baseurl` 同步写入 skill 根目录 `config.json` 的 `baseurl` 字段，便于后续工具读取当前抓包环境。

## 3. 安装 CA 证书（关键一步）

mitmproxy 需要把根证书装到 Windows 受信任根，才能解密 HTTPS。

### 3.1 下载证书

1. 启动 mitmdump（步骤 2）
2. 浏览器配置代理到 `127.0.0.1:12138`（步骤 4）
3. 浏览器访问 `http://mitm.it`
4. 点击 **Windows** 图标，下载 `mitmproxy-ca-cert.p12`

### 3.2 安装到"本地计算机"

1. 双击 `mitmproxy-ca-cert.p12`
2. 选择 **本地计算机**（不是"当前用户"）
3. 一路下一步
4. 在"证书存储"页选择 **将所有的证书都放入下列存储** → **浏览** → **受信任的根证书颁发机构** → 确定
5. 完成 → 导入成功

### 3.3 验证

浏览器访问任意 HTTPS 站点，应无"证书不受信任"告警。

## 4. 配置浏览器代理

### 推荐方式：Chrome + SwitchyOmega 插件

1. Chrome 扩展市场安装 SwitchyOmega
2. 新建情景模式"mitm"
   - 代理协议：HTTP
   - 代理服务器：`127.0.0.1`
   - 端口：`12138`
3. 需要抓包时切到"mitm"模式，不需要时切回"直接连接"

### 备选方式：Windows 系统代理

**Windows 设置 → 网络和 Internet → 代理 → 手动代理设置**：
- 地址：`127.0.0.1`
- 端口：`12138`
- 开启

**注意**：系统代理会影响所有 HTTP 客户端，包括 pip、git、部分桌面应用；用完请关闭。

## 5. 验证抓包通链

1. 代理已开（步骤 4）
2. mitmdump 运行中（步骤 2）
3. 浏览器打开被测环境，完成一次任意业务操作
4. 查看 `api_test_dwp_temp/latest.jsonl`：
   - 在项目根目录（含 `E10自动化` 的目录）下执行：`type api_test_dwp_temp\latest.jsonl`
   - 若看到多行 JSON 即成功

每行 JSON 关键字段：

| 字段 | 含义 |
|---|---|
| `ts` / `epoch` | 捕获时间 |
| `method` / `url` / `path` | HTTP 请求 |
| `req_headers` | 请求头（Cookie/Authorization 已摘要） |
| `req_body` | 请求体（文本） |
| `status` | HTTP 状态码 |
| `resp_body` | 响应体（二进制已跳过） |
| `body_skipped` / `skip_reason` | 二进制/编码响应标记 |
| `is_login` | 登录/登出接口标记 |

## 6. AI 协助模式（推荐）

配好证书和浏览器代理后，直接对 Claude Code 说：

> "帮我启动 api-test-E10 抓包"

AI 会：
1. 运行 `tools/check_capture_server.py` 检查 12138
2. 未启动则调用 `start.bat`
3. 启动后等待端口 LISTENING
4. 告诉你抓包服务的 `self.baseurl`、`self.prefixes`、`self.jsonl_path`，以及"抓包已就绪，请在浏览器操作"

如需强制清理旧进程并重启，直接对 AI 说“重启抓包服务”。AI 会执行 `capture/restart.bat`：先停止 `12138` 端口进程，等待 1 秒，再重新启动 `capture_addon.py`。

**AI 无法代劳的两步**（GUI 操作）：
- 双击证书完成 Windows 信任弹窗
- 浏览器安装 SwitchyOmega 插件

## 7. 扩展过滤前缀

默认抓以下路径前缀：

```
/api/  /sapi/  /base/  /papi/  /ipconfigrec/  /tenantlogo/  /app/
```

如需新增，编辑 `allowed_prefixes.txt`，每行一个。

**修改后要重启 mitmdump**（推荐运行 `restart.bat`，或 Ctrl+C 停止后重新运行 `start.bat`）。

## 8. 停止抓包

方式 A：mitmdump 窗口内按 `Ctrl+C`
方式 B：双击 `stop.bat`
方式 C：让 AI 运行 `stop.bat`

## 9. FAQ

**Q：`pip install mitmproxy` 报错 SSL？**
A：你机器可能已开着代理。先关代理再装，或用公司内网 pip 源。

**Q：`start.bat` 闪退？**
A：命令行运行 `mitmdump -s capture_addon.py --listen-port 12138` 看具体报错；通常是 Python 环境或 mitmproxy 版本问题。

**Q：12138 已被占用？**
A：`stop.bat` 释放；如占用方不是 mitmdump，查 `netstat -ano | findstr :12138` 看 PID，自行判断是否该终止。

**Q：证书装了但仍告警？**
A：99% 是装到了"当前用户"而非"本地计算机"。重做步骤 3.2。

**Q：抓不到 `/oa/second` 下的请求？**
A：打开 `E10自动化/接口自动化测试/config.py`，确认 `RunConfig.baseurl` 匹配你浏览器访问的域名；addon 只记录与 baseurl 匹配的请求。

**Q：HTTPS 站点访问报错？**
A：证书没装好，或代理没开，或 mitmdump 没启动。三者都要满足。

**Q：抓包里能看到我的 Cookie 吗？**
A：`req_headers` 里的 Cookie/Authorization 被摘要（前 20 字符 + 长度），不落全量。但响应体不做摘要——定期清 `latest.jsonl`。

**Q：文件下载接口的响应体也被抓了吗？**
A：Content-Type 为二进制类型（octet-stream、pdf、zip、image/* 等）时，addon 自动跳过 body，只记录 `<BINARY_SKIPPED: ...>`，并打 `body_skipped: true`。AI 生成草稿时会提示你这类接口需手动处理。

## 10. 运行时文件与清理

| 文件 | 说明 | 是否纳入 git |
|---|---|---|
| `api_test_dwp_temp/latest.jsonl` | 抓包落盘（项目内） | 否 |
| `tools/page_api_index.sqlite3` | 全局接口覆盖文档（skill 内） | 是 |
| `api_test_dwp_temp/capture_selection.md` | 勾选草稿（项目内） | 否 |

`api_test_dwp_temp/` 目录在首次运行工具时自动创建于当前项目根目录下。
建议每次用例编写完后删除 `latest.jsonl`，避免敏感业务数据长期沉淀。

