# 一、使用前准备
## claude code安全提醒
<!-- 这是一张图片，ocr 内容为： -->
![](https://cdn.nlark.com/yuque/0/2026/png/29548917/1778233651697-6e5eeda9-9b4b-4ee0-bcff-1219ab4555cb.png)

**<font style="color:#000000;background-color:#FCE75A;">claude官方提醒</font>**

1.  Claude可能会犯错误，您应该经常检查Claude的响应，特别是在运行代码时。

2. 由于提示注入的风险，只对你信任的代码使用它更多详细信息请参见：[https://code.claude.com/docs/en/security](https://code.claude.com/docs/en/security)

## 开源包被投毒的风险案例
1. LiteLLM投毒（<font style="background-color:#FCE75A;">我们公司遇到的安全事故</font>）

[https://mp.weixin.qq.com/s/gVxO9vNYu1gNvHnD9mPFsg](https://mp.weixin.qq.com/s/gVxO9vNYu1gNvHnD9mPFsg)

2. axios投毒（<font style="background-color:#FCE75A;">我朋友电脑使用龙虾安装环境中招，导致需要整机重装系统</font>）

[https://mp.weixin.qq.com/s/IBf3K2pbP9cKrJjpzddynA](https://mp.weixin.qq.com/s/IBf3K2pbP9cKrJjpzddynA)  
- <font style="background-color:#FCE75A;">这两个案例都是黑客向使用量很高的最新版本的开源包投毒。而使用AI帮我们安装环境时，AI都会默认安装最新版本的依赖包。这就导致使用AI遇到这种风险的概率更高，这也提醒我们使用AI需要谨慎。</font>

## 适用环境
|  | 建议要求 |
| --- | --- |
| 操作系统 | Windows 10 / Windows 11 |
| IDE | PyCharm |
| Python | 3.8 及以上 |
| 账号 | DeepSeek 开发者账号 |
| 工具 | Claude Code、CC Switch、PyCharm CC GUI 插件 |
| Skill | `api-test-dwp` |


## 需要提前准备的信息
请先准备以下内容，后续步骤会用到：

+ DeepSeek 开发者账号。
+ DeepSeek API Key。
+ `api-test-dwp` Skill 所在路径，例如：`C:\Users\admin\.claude\skills\api-test-dwp`。

# 二、工具和账号配置
## 1. 安装 Claude Code（Windows）
### 1.1 安装前检查 Node.js，版本需要在22以上
1. 打开 PowerShell。
2. 执行：

```powershell
node -v
```

3. 如果能看到版本号，例如 `v20.x.x`，说明 Node.js 已安装。
4. 如果提示未识别 `node` 命令，请先安装 Node.js：
    - 下载地址：`https://nodejs.org/`
    - 建议安装 LTS 版本。
    - 安装完成后重新打开 PowerShell，再执行 `node -v` 验证。

#### 重装Node.js到22以上的方法
##### **第一步：安装 nvm-windows（仅首次需要）**
1. **卸载现有 Node.js**：为避免冲突，先去“控制面板” -> “程序和功能”中卸载你当前的 Node.js v18.14.2。
2. **下载安装**：
    - 访问 [nvm-windows 的 GitHub 发布页](https://github.com/coreybutler/nvm-windows/releases)。
    - 下载 `nvm-setup.exe` 文件。
    - 运行安装程序，一路默认选项即可（它会自动配置环境变量）。

##### **第二步：使用 nvm 命令升级（以后的日常操作）**
安装完成后，打开一个新的 **命令提示符 (CMD)** 或 **PowerShell**，执行以下命令：

**查看可安装的版本**（可选）：

```bash
nvm list available
```

这会列出所有可用的版本，你可以选择最新版或有特殊需求的版本。

**安装最新版 Node.js**（直接复制下面这一整行）：

```bash
nvm install latest
```

如果你想安装最新的长期支持版（LTS，更稳定），可以用：`nvm install lts`。

**切换并使用新版本**：

```bash
nvm use latest
```

**设置为默认版本**（可选）：

```bash
nvm alias default latest
```

设置后，以后每次打开终端都会自动使用这个最新版本，<font style="background-color:#FBF5CB;">还需要注意nvm安装的node.js跟以前默认安装的node。js路径不一样，在进行CCG配置时需要修改。</font>

### 1.2 安装 Claude Code
1. 打开 PowerShell。
2. 执行安装命令：

```powershell
npm install -g @anthropic-ai/claude-code
```

3. 安装完成后执行：

```powershell
claude --version
```

4. 如果能看到 Claude Code 版本号，说明安装成功。
5. 如果报错找不到命令，大概率是未添加环境变量，需要找到claude.cmd的安装位置并添加到环境变量。

<!-- 这是一张图片，ocr 内容为： -->
![](https://cdn.nlark.com/yuque/0/2026/png/29548917/1778298753088-3fd7dbdf-6db9-45ce-960f-a9c91b56217e.png)

### 1.3 Claude Code的首次配置
1. 修改_**C:\Users\admin****.****claude\settings.json**_(没有文件可手动新建)

```json
{
  "env": {
    "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": 1
  }
}
```

2. **C:\Users\admin**目录下点击打开隐藏项目,并修改**.claude.json** (没有文件可手动新建),目的是绕过claude的登录检查

```json
{
  "hasCompletedOnboarding": true
}
```

3. 修改完成后在任何目录使用powershell执行命令：claude，能正常进入界面就是成功了。

## 2. 安装 CC Switch
CC Switch 用于管理 Claude Code 的不同模型服务配置，本文使用它配置 DeepSeek。

### 2.1 下载 Windows 安装包
1. 打开浏览器访问：

```latex
https://github.com/farion1231/cc-switch/releases/tag/v3.14.1
```

2. 页面打开后，拉到最下面的 `Assets` 区域。
3. 也可以在页面中直接搜索：

```latex
CC-Switch-v3.14.1-Windows.msi
```

4. 点击 `CC-Switch-v3.14.1-Windows.msi` 下载。

### 2.2 安装 CC Switch
1. 双击下载的 `CC-Switch-v3.14.1-Windows.msi`。
2. 按安装向导点击下一步。
3. 安装路径如无特殊要求，保持默认即可。
4. 安装完成后，在开始菜单或桌面快捷方式中打开 CC Switch。

### 2.3 验证 CC Switch 可用
1. 打开 CC Switch。
2. 确认能看到配置列表或新增配置入口。
3. 如果打不开，记录报错截图：`【待补充：本机报错信息】`。

## 3. 在 PyCharm 中安装 CC GUI 插件
CC GUI 插件用于在 PyCharm 中调用 Claude Code / CC Switch 配置，方便直接在项目内编写接口自动化用例。

### 3.1 打开 PyCharm 插件市场
1. 打开 PyCharm。
2. 打开接口自动化项目。
3. 进入菜单：
    - `File` → `Settings`
    - 或使用快捷键 `Ctrl + Alt + S`
4. 在左侧选择：
    - `Plugins`
5. 切换到：
    - `Marketplace`

### 3.2 搜索并安装 CC GUI
1. 在插件搜索框输入：

<!-- 这是一张图片，ocr 内容为： -->
![](https://cdn.nlark.com/yuque/0/2026/png/29548917/1778230873830-2d18afe1-85c8-4b1a-a16c-210e847eaf94.png)

2. 找到对应插件后点击 `Install`。
3. 安装完成后，按 PyCharm 提示重启 IDE。
4. 重启后检查 PyCharm 侧边栏、底部工具窗口或菜单中是否出现 CC GUI 入口。
5. 检查node.js是否配置,并且版本大于等于22

<!-- 这是一张图片，ocr 内容为： -->
![](https://cdn.nlark.com/yuque/0/2026/png/29548917/1778298831446-51101824-e214-4046-a5a7-896b05615088.png)

6. 检查SDK是否安装,且版本建议更新到最新版本

<!-- 这是一张图片，ocr 内容为： -->
![](https://cdn.nlark.com/yuque/0/2026/png/29548917/1778298967974-23739758-3349-4716-a45b-1f46b2ed4e07.png)

## 4. 注册并配置 DeepSeek 开发者账号
### 4.1 注册 DeepSeek 开发者账号
1. 打开浏览器访问：

```latex
https://platform.deepseek.com/
```

2. 点击注册或登录。
3. 按页面提示完成手机号、邮箱或第三方账号登录。
4. 登录后进入 DeepSeek 开发者控制台。

### 4.2 创建 API Key
1. 在 DeepSeek 开发者控制台中找到 API Key 管理入口。
2. 创建新的 API Key。
3. 创建后立即复制并保存 API Key。
4. 请勿把 API Key 提交到 Git、发到群聊或写进测试代码。

## 5. 将 DeepSeek 配置到 CC Switch
### 5.1 DeepSeek 配置
+ 配置信息参考[https://api-docs.deepseek.com/zh-cn/quick_start/agent_integrations/claude_code](https://api-docs.deepseek.com/zh-cn/quick_start/agent_integrations/claude_code)
+ 配置截图参考：

<!-- 这是一张图片，ocr 内容为： -->
![](https://cdn.nlark.com/yuque/0/2026/png/29548917/1778231260675-c66536e0-a3d8-4fc4-a027-7499bf1f3e7e.png)

### 5.2 验证 Claude Code 使用 DeepSeek
1. 打开 PowerShell。
2. 进入自己的接口自动化项目目录：

```powershell
cd D:\workSpace_001\test-automation
```

3. 启动 Claude Code：

```powershell
claude
```

4. 输入简单问题验证，例如：

```latex
你好，你是什么模型。
```

5. 如果能正常回复，说明 Claude Code + CC Switch + DeepSeek 链路可用。
6. 执行初始化命令生成CLAUDE.md文件

```latex
/init
```

### 5.3 常见问题
**问题：401 / Unauthorized**  
处理：检查 API Key 是否复制完整，是否有多余空格，DeepSeek 账号是否可用。

**问题：模型不存在**  
处理：检查模型名是否填写为 `deepseek-chat` 或团队指定模型名。

# 三、接口自动化用例编写
## 1. 准备 `api-test-dwp` Skill
### 1.1 手动复制Skill 文件到claude目录下
```powershell
dir C:\Users\admin\.claude\skills\api-test-dwp
```

### 1.2 确认接口自动化项目结构
1. 用 PyCharm 打开接口自动化项目。
2. 确认项目中存在接口自动化目录，例如：

```latex
E10自动化\接口自动化测试
```

3. 确认 `config.py` 中当前启用的 `RunConfig.baseurl` 与浏览器访问的被测环境域名一致。

### 1.3 在 Claude Code / CC GUI 中触发 Skill
在 CC GUI 对话中说明要使用 `api-test-dwp` Skill，例如：

```latex
请使用 api-test-dwp Skill 帮我编写接口自动化用例。
```

如果你的环境需要显式引用 Skill 路径，可补充：

```latex
Skill 路径：C:\Users\admin\.claude\skills\api-test-dwp
```

## 2. 使用 CC GUI 编写接口自动化用例
### 2.1 打开 CC GUI
1. 打开 PyCharm。
2. 打开接口自动化项目。
3. 打开 CC GUI 工具窗口
4. <font style="color:#000000;">CC GUI设置-供应商管理-选择</font>**<font style="color:#000000;">使用本地配置信息</font>**
5. <font style="color:#000000;">CC GUI设置-SKD依赖,确认</font>**<font style="color:#000000;">Claude Code SDK可用</font>**

### 2.2 每次编写用例前必须提供 5 项任务信息
正式新增或修改接口方法、接口用例前，必须先把下面 5 项发给 AI。缺任意一项，Skill 会要求你补充。

```markdown
# 本次任务信息
- `[接口方法文件]` = `填写接口方法所在文件路径`（无新增时填：当前用例无新增接口）
- `[接口方法位置]` = `填写接口方法新增位置，例如：文件末尾 / 第123行后 / 某方法后`（无新增时填：当前用例无新增接口）
- `[接口用例文件]` = `填写接口用例所在文件路径`
- `[接口用例位置]` = `填写接口用例新增位置，例如：文件末尾 / 第456行插入 / 某用例后 / 完善某用例`
- `[用例名]` = `填写本次新增用例的完整中文功能名称`
```

### 2.3 重要填写规则
+ `[接口方法文件]` 与 `[接口方法位置]` 必须同时填写真实内容，或同时填写 `当前用例无新增接口`。
+ 不能保留 `填写接口方法所在文件路径` 这类占位符原文。
+ `[用例名]` 要写完整中文功能名，不要只写英文缩写或简单编号。
+ 如果是纯查询、检查环境、启动抓包，不需要填写 5 项任务信息。
+ 一旦进入“新增 / 修改接口方法或用例”阶段，必须补齐 5 项任务信息。

## 3. 三种用例编写方式总览
`api-test-dwp` Skill 支持三种方式：

| 方式 | 名称 | 适合场景 | 需要你提供 |
| --- | --- | --- | --- |
| 方式 1 | 抓包驱动 | 新接口多、业务链路复杂、希望从真实 UI 操作生成用例 | 抓包环境、UI 操作、勾选接口 |
| 方式 2 | 参考已有用例 | 已有相似用例，只需仿写、改参数、改断言 | 参考用例路径或函数名、差异点 |
| 方式 3 | cURL 手工 | 抓包不可用、接口数量少、能手动复制请求响应 | cURL、响应体、业务说明 |


如果你没有指定方式，Skill 会让你回复 `1`、`2` 或 `3` 选择。

## 4. 方式 1：抓包驱动编写用例
抓包服务的完整教程请以本仓库文件为准：[`capture/README.md`](./capture/README.md)。该文件包含 Python、mitmproxy、证书安装、浏览器代理、抓包验证、停止抓包等完整步骤。

### 4.1 方式 1 适用场景
+ 需要覆盖一条完整业务链路。
+ 页面操作会触发多个接口。
+ 不确定哪些接口需要新增方法。
+ 希望 AI 从真实请求中识别新接口、已实现接口和特殊接口。

### 4.2 首次使用前配置抓包环境
按 `capture/README.md` 完成以下事项：

1. 确认 Python 版本：

```powershell
python --version
```

2. 安装 mitmproxy：

```powershell
pip install mitmproxy
```

3. 验证 mitmproxy：

```powershell
mitmdump --version
```

4. 启动抓包：

```powershell
cd C:\Users\admin\.claude\skills\api-test-dwp\capture
mitmdump -s capture_addon.py --listen-port 12138
```

5. 配置浏览器代理：
    - 地址：`127.0.0.1`
    - 端口：`12138`
6. 访问 `http://mitm.it` 下载并安装 Windows 证书。
7. 证书必须安装到：
    - `本地计算机`
    - `受信任的根证书颁发机构`
8. 打开被测系统完成一次操作，确认生成抓包数据。

### 4.3 方式 1 提示词填写步骤
#### 步骤 1：先发送任务信息
在 CC GUI 中发送：

```markdown
请使用 api-test-dwp Skill，按方式1：抓包驱动，帮我编写接口自动化用例。

# 本次任务信息
- `[接口方法文件]` = `E10自动化/接口自动化测试/page_api/【待补充：接口方法文件】.py`
- `[接口方法位置]` = `文件末尾`
- `[接口用例文件]` = `E10自动化/接口自动化测试/test_case/【待补充：接口用例文件】.py`
- `[接口用例位置]` = `文件末尾`
- `[用例名]` = `【待补充：完整中文用例名】`
```

#### 步骤 2：让 AI 检查或启动抓包
继续发送：

```latex
请检查 api-test-dwp 抓包服务是否已启动；如果未启动，请帮我启动抓包服务。
```

#### 步骤 3：你在浏览器中完成业务操作
1. 确认浏览器代理已切到 `127.0.0.1:12138`。
2. 打开被测系统。
3. 按用例需要完成一遍 UI 操作。
4. 操作完成后回到 CC GUI。
5. 发送：

```latex
我已经操作完成，请继续读取抓包结果并生成勾选草稿。
```

#### 步骤 4：勾选需要生成用例的接口
AI 会生成勾选草稿，通常位置类似：

```latex
api_test_dwp_temp/capture_selection.md
```

你需要：

1. 打开勾选草稿。
2. 保留需要写入用例的接口为 `[x]`。
3. 不需要的接口改成 `[ ]`。
4. 保存文件。
5. 回到 CC GUI 发送：

```latex
我已经完成接口勾选，请按勾选结果生成接口方法和 pytest 用例，并执行最小范围验证。
```

#### 步骤 5：根据 AI 反馈补充信息
如果 AI 提示以下内容，请按提示补充：

+ 某个接口是否需要复用已有方法。
+ 某个字段断言规则不明确。
+ 某个接口响应体过大或为二进制。
+ 登录态、租户、组织、用户、流程数据需要你确认。

### 4.4 方式 1 完整提示词模板
```markdown
请使用 api-test-dwp Skill，按方式1：抓包驱动，帮我编写接口自动化用例。

# 本次任务信息
- `[接口方法文件]` = `E10自动化/接口自动化测试/page_api/【待补充】.py`
- `[接口方法位置]` = `文件末尾`
- `[接口用例文件]` = `E10自动化/接口自动化测试/test_case/【待补充】.py`
- `[接口用例位置]` = `文件末尾`
- `[用例名]` = `【待补充：完整中文功能名称】`

请先检查抓包服务状态；如果未启动，请启动抓包服务。等我在浏览器完成业务操作并回复“继续”后，再读取抓包结果、生成勾选草稿，并按我勾选的接口生成接口方法和 pytest 用例。
```

## 5. 方式 2：参考已有用例编写
### 5.1 方式 2 适用场景
+ 已经有相似业务用例。
+ 新用例只是改页面、改参数、改断言。
+ 不需要新增接口方法。
+ 同一类用例需要批量铺开。

### 5.2 方式 2 提示词填写步骤
#### 步骤 1：找到参考用例
在 PyCharm 中找到你想参考的已有用例，记录：

+ 参考用例文件路径。
+ 参考用例函数名。
+ 新旧用例差异点。

示例：

```latex
参考用例文件：E10自动化/接口自动化测试/test_case/【待补充】.py
参考用例函数：test_【待补充】
差异点：把【待补充旧功能】改为【待补充新功能】，断言【待补充】字段。
```

#### 步骤 2：判断是否新增接口方法
如果完全复用已有接口方法：

```markdown
- `[接口方法文件]` = `当前用例无新增接口`
- `[接口方法位置]` = `当前用例无新增接口`
```

如果需要新增接口方法，则填写真实文件和位置。

#### 步骤 3：发送方式 2 提示词
```markdown
请使用 api-test-dwp Skill，按方式2：参考已有用例，帮我编写接口自动化用例。

# 本次任务信息
- `[接口方法文件]` = `当前用例无新增接口`
- `[接口方法位置]` = `当前用例无新增接口`
- `[接口用例文件]` = `E10自动化/接口自动化测试/test_case/【待补充：目标用例文件】.py`
- `[接口用例位置]` = `【待补充：文件末尾 / 某用例后 / 第几行后】`
- `[用例名]` = `【待补充：完整中文用例名】`

参考用例文件：`E10自动化/接口自动化测试/test_case/【待补充：参考用例文件】.py`
参考用例函数：`test_【待补充：参考函数名】`

新用例与参考用例的差异：
1. 【待补充：差异点1】
2. 【待补充：差异点2】
3. 【待补充：断言要求】

请先阅读参考用例和相关接口方法，按现有编码风格仿写，不要改动无关代码。完成后执行最小范围 pytest 验证。
```

#### 步骤 4：按 AI 提问补充业务差异
AI 可能会要求补充：

+ 新用例使用的数据来源。
+ 是否需要前置创建数据。
+ 是否需要清理数据。
+ 断言字段和预期值。
+ 是否复用参考用例中的 fixture。

请根据实际业务回复，不确定的内容可以明确写：

```latex
该字段我不确定，请先按参考用例保持一致，无法判断的位置留 TODO 或向我确认后再写。
```

### 5.3 方式 2 完整提示词模板
```markdown
请使用 api-test-dwp Skill，按方式2：参考已有用例，帮我编写接口自动化用例。

# 本次任务信息
- `[接口方法文件]` = `当前用例无新增接口`
- `[接口方法位置]` = `当前用例无新增接口`
- `[接口用例文件]` = `E10自动化/接口自动化测试/test_case/【待补充】.py`
- `[接口用例位置]` = `文件末尾`
- `[用例名]` = `【待补充：完整中文功能名称】`

参考用例文件：`E10自动化/接口自动化测试/test_case/【待补充】.py`
参考用例函数：`test_【待补充】`

请仿照参考用例新增一个用例，差异如下：
1. 【待补充】
2. 【待补充】
3. 【待补充】

要求：
- 保持现有接口方法调用风格。
- 不修改无关代码。
- 如果发现已有接口方法可复用，优先复用。
- 完成后运行当前用例文件中新增用例的最小范围 pytest。
```

## 6. 方式 3：cURL 手工编写
### 6.1 方式 3 适用场景
+ 抓包服务暂时不可用。
+ 抓包数据太多，不方便筛选。
+ 接口数量较少，可以手动复制 cURL。
+ 你已经从浏览器 DevTools、Apifox、Postman 或其他工具拿到了请求和响应。

### 6.2 获取 cURL 和响应体
#### 从 Chrome DevTools 获取 cURL
1. 打开 Chrome。
2. 按 `F12` 打开开发者工具。
3. 切换到 `Network` 面板。
4. 勾选 `Preserve log`，避免页面跳转后请求丢失。
5. 在页面上完成业务操作。
6. 找到目标接口请求。
7. 右键请求。
8. 选择：
    - `Copy`
    - `Copy as cURL` 或 `Copy as cURL (bash)`
9. 打开请求的 `Response` 或 `Preview`，复制接口响应体。

### 6.3 方式 3 提示词填写步骤
#### 步骤 1：整理接口信息
每个接口建议按以下格式整理：

```latex
## 接口 1：【待补充：接口用途】

### cURL
【待补充：粘贴 cURL】

### 响应体
【待补充：粘贴响应体】
```

如果有多个接口，按 `接口 1`、`接口 2`、`接口 3` 依次排列。

#### 步骤 2：发送方式 3 提示词
```markdown
请使用 api-test-dwp Skill，按方式3：cURL 手工，帮我编写接口自动化用例。

# 本次任务信息
- `[接口方法文件]` = `E10自动化/接口自动化测试/page_api/【待补充：接口方法文件】.py`
- `[接口方法位置]` = `文件末尾`
- `[接口用例文件]` = `E10自动化/接口自动化测试/test_case/【待补充：接口用例文件】.py`
- `[接口用例位置]` = `文件末尾`
- `[用例名]` = `【待补充：完整中文用例名】`

下面是本次用例涉及的接口 cURL 和响应体，请解析请求方法、URL、参数、请求体和响应断言，生成接口方法和 pytest 用例。

## 接口 1：【待补充：接口用途】

### cURL
【待补充：粘贴 cURL】

### 响应体
【待补充：粘贴响应体】

## 接口 2：【可选，待补充】

### cURL
【待补充：粘贴 cURL】

### 响应体
【待补充：粘贴响应体】

要求：
- 优先检查是否已有相同 URL 的接口方法，已有则复用。
- 新增接口方法时按项目现有 page_api 风格编写。
- 用例断言请基于响应体中的稳定字段，不要断言时间戳、随机 ID 等不稳定字段。
- 不明确的业务字段请先向我确认，不要乱写。
- 完成后执行最小范围 pytest 验证。
```

#### 步骤 3：补充字段说明
如果 cURL 或响应中有业务字段不容易判断，请额外补充说明，例如：

```markdown
字段说明：
- `name`：本次创建的数据名称，需要使用随机后缀避免重复。
- `status`：预期为启用状态。
- `id`：由前一个接口返回，后续接口需要复用。
- `createTime`：动态时间，不需要强断言。
```

### 6.4 方式 3 完整提示词模板
```markdown
请使用 api-test-dwp Skill，按方式3：cURL 手工，帮我编写接口自动化用例。

# 本次任务信息
- `[接口方法文件]` = `E10自动化/接口自动化测试/page_api/【待补充】.py`
- `[接口方法位置]` = `文件末尾`
- `[接口用例文件]` = `E10自动化/接口自动化测试/test_case/【待补充】.py`
- `[接口用例位置]` = `文件末尾`
- `[用例名]` = `【待补充：完整中文功能名称】`

业务目标：
【待补充：本用例要验证什么】

接口链路：
1. 【待补充：第一步接口用途】
2. 【待补充：第二步接口用途】
3. 【待补充：最终断言】

## 接口 1：【待补充】

### cURL
【待补充】

### 响应体
【待补充】

字段说明：
- 【待补充】

请先按 URL 查找是否已有接口方法；已有则复用，没有再新增。请按现有项目风格生成接口方法和 pytest 用例，不要改动无关代码。遇到不明确字段请先问我。
```

## 7. 编写完成后的验证步骤
### 7.1 最小范围运行 pytest
AI 完成代码后，通常会运行最小范围测试。你也可以手动执行：

```powershell
pytest E10自动化\接口自动化测试\test_case\【待补充：用例文件】.py -k "【待补充：用例函数关键字】"
```

### 7.2 如果测试失败
把失败日志完整发给 CC GUI，并说明：

```latex
这是刚才新增用例的 pytest 失败日志，请使用 api-test-dwp Skill 按真实报错修复，只修改本次相关代码，不要改动无关用例。
```

### 7.3 验证通过后检查改动
1. 在 PyCharm 中查看 Git 变更。
2. 确认只修改了本次相关文件。
3. 确认没有提交运行期产物，例如：
    - `capture/latest.jsonl`
    - `api_test_dwp_temp/`
    - `capture_selection.md`
4. 确认新增用例名称、断言和测试数据符合预期。

## 8. 推荐使用流程
首次配置时按以下顺序执行：

1. 安装 Node.js。
2. 安装 Claude Code。
3. 安装 CC Switch。
4. 在 DeepSeek 平台注册账号并创建 API Key。
5. 在 CC Switch 中新增 DeepSeek 配置。
6. 在 PyCharm 中安装 CC GUI 插件。
7. 打开接口自动化项目。
8. 在 CC GUI 中验证 AI 可正常回复。
9. 确认 `api-test-dwp` Skill 可触发。
10. 首次使用方式 1 时，按 `capture/README.md` 配置 mitmproxy、证书和浏览器代理。
11. 按本教程“三、接口自动化用例编写”的第 4、5、6 节选择一种方式编写用例。
12. 执行最小范围 pytest 验证。

日常编写用例时按以下顺序执行：

1. 打开 PyCharm 和 CC GUI。
2. 明确本次用例要写到哪个文件、哪个位置。
3. 准备 5 项任务信息。
4. 选择方式 1、方式 2 或方式 3。
5. 按对应模板发送提示词。
6. 根据 AI 提问补充业务细节。
7. 查看生成代码。
8. 运行或确认 AI 已运行最小范围 pytest。
9. 处理失败日志直到通过。
10. 检查 Git 变更，避免提交运行期产物。

## 9. 常见问题
### 9.1 Claude Code 能打开，但 CC GUI 不可用
处理步骤：

1. 确认 PyCharm 已安装 CC GUI 插件。
2. 重启 PyCharm。
3. 检查插件入口：`View` → `Tool Windows`。
4. 确认 CC Switch 已切换到 DeepSeek 配置。
5. 仍失败时记录错误：`【待补充：错误截图或日志】`。

### 9.2 AI 没有按 `api-test-dwp` 规范执行
处理：在提示词开头明确写：

```latex
请使用 api-test-dwp Skill，并严格按 SKILL.md 的前置必填信息和三种编写方式执行。
```

### 9.3 提示缺少任务信息
处理：检查是否完整填写了 5 项：

+ `[接口方法文件]`
+ `[接口方法位置]`
+ `[接口用例文件]`
+ `[接口用例位置]`
+ `[用例名]`

如果不新增接口方法，前两项必须同时填写 `当前用例无新增接口`。

### 9.4 抓包服务启动失败
处理：按 `capture/README.md` 排查，重点检查：

+ Python 是否安装。
+ `mitmdump --version` 是否可用。
+ `12138` 端口是否被占用。
+ 证书是否安装到 `本地计算机` 的 `受信任的根证书颁发机构`。
+ 浏览器代理是否为 `127.0.0.1:12138`。

### 9.5 不知道选哪种编写方式
建议：

+ 有真实页面操作、新链路复杂：优先选方式 1。
+ 有非常相似的已有用例：优先选方式 2。
+ 只有接口请求和响应，没有抓包环境：选方式 3。

## 10. 附录：可直接复制的启动检查提示词
```markdown
请使用 api-test-dwp Skill，帮我检查当前接口自动化环境是否可用。

请检查：
1. 当前项目结构是否符合接口自动化项目要求。
2. 是否能找到 `E10自动化/接口自动化测试/config.py`。
3. 当前 `RunConfig.baseurl` 是否可读取。
4. `api-test-dwp` Skill 相关工具是否存在。
5. 如果我要使用方式1，请检查抓包服务是否运行。

这次只是环境检查，不新增或修改用例。
```

