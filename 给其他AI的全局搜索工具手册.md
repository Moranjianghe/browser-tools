# 给其他 AI 的全局搜索工具手册（优化版）

这台机器已经安装了一套项目无关、可跨项目复用的本地搜索/浏览工具。

如果你是另一个 AI，请优先使用这套全局工具，不要默认去找旧的项目目录版本。

本文默认把这份手册所在目录记作 `<工具根目录>`。

## 1. 全局安装位置

- 工具目录：当前这份手册所在目录，也就是 `<工具根目录>`
- 配置文件：`<工具根目录>\.env`
- PowerShell 启动器：`<工具根目录>\bt.ps1`
- 命令包装器：`<工具根目录>\browser-tools.cmd`
- 共享浏览器 profile：默认是 `<工具根目录>\profiles\shared`
- 下载目录：默认是 `<工具根目录>\downloads`
- browser-use 虚拟环境：默认是 `<工具根目录>\.venv`
- 默认远程调试端口：`9223`

说明：

- 这套工具与具体业务项目无关。
- 即使当前工作目录在别的仓库，也可以直接调用它。
- 目录里可能还存在旧项目内副本，但不要混用路径。

## 2. 已配置好的工具

### Playwright

适合：

- 打开网页
- 精确点击和导航
- 下载 PDF
- 连接已登录的真实 Chrome

### browser-use

适合：

- 多步网页任务
- 复杂站点导航
- 让 agent 自主搜索、点开、提取内容

## 3. 推荐调用方式

如果当前终端已经在 `<工具根目录>`：

```powershell
.\bt.ps1 pw:smoke
.\bt.ps1 chrome:debug
.\bt.ps1 pw:cdp -- https://example.com
.\bt.ps1 bu:doctor
.\bt.ps1 bu:task -- "Open arXiv and find the PDF download link for a paper"
```

如果当前终端不在 `<工具根目录>`：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File <工具根目录>\bt.ps1 pw:smoke
powershell -NoProfile -ExecutionPolicy Bypass -File <工具根目录>\bt.ps1 chrome:debug
powershell -NoProfile -ExecutionPolicy Bypass -File <工具根目录>\bt.ps1 pw:cdp -- https://example.com
powershell -NoProfile -ExecutionPolicy Bypass -File <工具根目录>\bt.ps1 bu:doctor
powershell -NoProfile -ExecutionPolicy Bypass -File <工具根目录>\bt.ps1 bu:task -- "your task"
```

也可以直接调用：

```powershell
<工具根目录>\browser-tools.cmd pw:smoke
<工具根目录>\browser-tools.cmd chrome:debug
```

## 4. 当前默认配置

当前建议的 `.env` 关键项是：

```text
# CHROME_PATH=
# BROWSER_PROFILE_DIR=
REMOTE_DEBUGGING_PORT=9223
BROWSER_USE_LLM=openai
BROWSER_USE_MODEL=gpt-5.4-mini
BROWSER_USE_REASONING_EFFORT=medium
OPENAI_WIRE_API=responses
OPENAI_DISABLE_RESPONSE_STORAGE=true
OPENAI_CODEX_COMPAT=true
OPENAI_BASE_URL=https://www.openclaudecode.cn/v1
OPENAI_API_KEY=
```

注意：

- `Playwright` 不依赖 API key，可以直接使用。
- `browser-use` 运行 agent 任务前，需要先在 `.env` 里填入 `OPENAI_API_KEY`。
- `browser-use` 当前默认走 `Responses API`，并默认关闭响应存储，以对齐 Codex 的配置方式。
- `browser-use` 默认会附带一组 Codex 风格的兼容身份字段，包括 `originator`、`User-Agent`、`session_id`、`x-codex-window-id`、`prompt_cache_key`、`client_metadata`，以兼容只放行 Codex 风格请求的网关。
- 如果 `CHROME_PATH` 留空，脚本会优先尝试系统默认的 Chrome / Edge 安装路径。
- 如果 `BROWSER_PROFILE_DIR` 留空，脚本会默认使用 `<工具根目录>\profiles\shared`。

## 5. 推荐流程（优化版）

### 步骤 0：每次任务前先体检（必做）

```powershell
.\bt.ps1 pw:smoke
.\bt.ps1 bu:doctor
```

只要这两步任一步失败，不要直接跑复杂任务，先修环境。

### 步骤 1：先选执行路径，不要混跑

- 页面结构稳定、目标明确：优先 `Playwright`
- 需要登录态复用：先 `chrome:debug`，再 `pw:cdp` 或 `bu:task -- --cdp-url ...`
- 需要自主探索、多轮导航：再上 `browser-use`

### 步骤 2：browser-use 任务要“短指令、分段跑”

- 单次任务只放一个主要目标，避免把“搜索+比对+写总结”塞进一次运行。
- 如果任务超过 5 个动作，拆成多个 `bu:task` 子任务。
- 优先先跑可验证的小任务，再跑长任务。

示例：

```powershell
.\bt.ps1 bu:task -- "Find the official sustainability report page for brand X"
.\bt.ps1 bu:task -- "Open that page and extract worker wage commitments"
```

### 步骤 3：涉及登录/验证码时的最稳流程

1. `.\bt.ps1 chrome:debug`
2. 在真实 Chrome 手工登录一次
3. 精确抓取优先 `.\bt.ps1 pw:cdp -- <URL>`
4. 复杂流程才用 `browser-use`，并尽量附着已有会话（`--cdp-url`）

### 步骤 4：任务结束后做收尾（必做）

1. 如果开过 `chrome:debug`，手工关闭该调试 Chrome 窗口。
2. 如果出现“页面还在自己跳转/不断开新页”，执行清理命令：

```powershell
Get-CimInstance Win32_Process |
  Where-Object { $_.CommandLine -match 'browser-use-user-data-dir|playwright_chromiumdev_profile|cliDaemon.js profile-highlight-smoke' } |
  ForEach-Object { Stop-Process -Id $_.ProcessId -Force }
```

3. 可选复查（确认相关调试端口已释放）：

```powershell
Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue |
  Where-Object { $_.LocalPort -in @(9223,52410,52715,62158) }
```

## 6. 场景化建议

### 场景 A：普通网页查看、验证可访问

1. `.\bt.ps1 pw:smoke`
2. 优先用 `Playwright` 做打开页面、标题检查、简单抓取

### 场景 B：登录、验证码、学校资源、付费站点

1. `.\bt.ps1 chrome:debug`
2. 手工完成登录/验证码
3. 后续复用同一会话，不要重复抢同一 profile
4. 精确操作优先 `pw:cdp`
5. 复杂多步任务再上 `browser-use`

### 场景 C：论文原文、PDF、开放网页材料

1. 优先找原始 PDF、官方页面、开放获取页面
2. 下载默认落在 `<工具根目录>\downloads`
3. 需要放回项目目录时，单独复制，不要改全局工具

## 7. 什么时候用哪一个

- 任务稳定、页面结构清晰、需要精确复现：优先 `Playwright`
- 任务复杂、需要多轮导航和判断：优先 `browser-use`
- 需要登录站点、验证码、人工过认证：先 `chrome:debug`
- 只想确认环境是否正常：先 `pw:smoke` 或 `bu:doctor`

## 8. 注意事项（补强）

- 不要把这套全局工具当成某个项目的内部脚本目录。
- 不要把旧项目内副本和这份全局目录混着写。
- `browser-use` 默认通过兼容 OpenAI/Codex 的 `Responses API` 工作；如果网关只支持旧的 `chat/completions`，把 `.env` 里的 `OPENAI_WIRE_API` 改为 `chat`。
- 如果某个网关只接受普通 OpenAI SDK 风格请求，而不需要 Codex 风格身份字段，把 `.env` 里的 `OPENAI_CODEX_COMPAT` 改为 `false`。
- 某些网站会持续触发验证码，自动化不能保证通过，这时应让用户先手工过一次。
- 共享 profile 正在被真实 Chrome 使用时，优先走 CDP 连接，而不是直接重复占用同一个 profile 目录。
- 全局下载目录是共享的，任务结束后请自行判断是否需要整理或转移文件。
- 外层调用如果设置了硬超时，可能导致子进程来不及优雅退出；此时请执行“步骤 4 收尾”里的清理命令。

## 9. 常见故障速查

- `bu:task` 无输出卡住：先 `Ctrl+C`，再跑一次 `bu:doctor`，必要时降级成分段任务。
- Chrome 不断弹新页面：执行“步骤 4 收尾”的进程清理命令。
- CDP 连不上：确认 `chrome:debug` 还在运行，且端口 `9223` 正在监听。
- 编码乱码：优先把当前终端输出编码切到 UTF-8 再重试。

## 10. 可直接复制给其他 AI 的说明

你可以把下面这段直接发给另一个 AI：

```text
这台机器有一套全局可复用的浏览器/搜索工具。
把当前这份手册所在目录记作 <工具根目录>。
不要默认使用旧的项目内副本。

执行顺序建议：
1) 先体检：.\bt.ps1 pw:smoke 和 .\bt.ps1 bu:doctor
2) 再执行任务：优先 Playwright；复杂多步再用 browser-use
3) 任务后收尾：关闭调试 Chrome；异常时清理 browser-use/playwright 残留进程

常用命令：
.\bt.ps1 chrome:debug
.\bt.ps1 pw:cdp -- https://example.com
.\bt.ps1 bu:task -- "your task"

如果当前终端不在 <工具根目录>，把命令里的 bt.ps1 换成 <工具根目录>\bt.ps1。

Playwright 不需要 API key。
browser-use 需要在 <工具根目录>\.env 里填写 OPENAI_API_KEY。
如果网站需要登录或验证码，先 chrome:debug，用真实 Chrome 手工登录后再继续自动化。
```
