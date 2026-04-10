# 给其他 AI 的全局搜索工具手册

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
BROWSER_USE_MODEL=gpt-5.3-codex
BROWSER_USE_REASONING_EFFORT=high
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

## 5. 推荐工作流

### 场景 A：普通网页查看、验证页面可访问

1. 先运行：

```powershell
.\bt.ps1 pw:smoke
```

2. 如果只是需要稳定打开某个页面、看标题、做简单抓取，优先用 `Playwright`。

### 场景 B：需要登录、验证码、学校资源、付费站点

1. 先启动真实 Chrome：

```powershell
.\bt.ps1 chrome:debug
```

2. 在打开的 Chrome 中手工完成登录或验证码。
3. 后续优先复用这个会话，不要重新起一个抢同一 profile 的浏览器。
4. 精确操作时优先用 `pw:cdp`。
5. 复杂多步任务时再用 `browser-use`，并优先通过 `BROWSER_CDP_URL` 连接到现有会话。

### 场景 C：论文原文、PDF、开放网页材料

1. 优先找原始 PDF、官方页面、开放获取页面。
2. 下载内容默认会落在：

```text
<工具根目录>\downloads
```

3. 如果当前项目需要把下载结果放回项目目录，再单独复制，不要修改这套全局工具本身。

## 6. 什么时候用哪一个

- 任务稳定、页面结构清晰、需要精确复现：优先 `Playwright`
- 任务复杂、需要多轮导航和判断：优先 `browser-use`
- 需要登录站点、验证码、人工过认证：先 `chrome:debug`
- 只想确认环境是否正常：先 `pw:smoke` 或 `bu:doctor`

## 7. 注意事项

- 不要把这套全局工具当成某个项目的内部脚本目录。
- 不要把旧项目内副本和这份全局目录混着写。
- `browser-use` 默认通过兼容 OpenAI/Codex 的 `Responses API` 工作；如果网关只支持旧的 `chat/completions`，把 `.env` 里的 `OPENAI_WIRE_API` 改为 `chat`。
- 如果某个网关只接受普通 OpenAI SDK 风格请求，而不需要 Codex 风格身份字段，把 `.env` 里的 `OPENAI_CODEX_COMPAT` 改为 `false`。
- 某些网站会持续触发验证码，自动化不能保证通过，这时应让用户先手工过一次。
- 共享 profile 正在被真实 Chrome 使用时，优先走 CDP 连接，而不是直接重复占用同一个 profile 目录。
- 全局下载目录是共享的，任务结束后请自行判断是否需要整理或转移文件。

## 8. 可直接复制给其他 AI 的说明

你可以把下面这段直接发给另一个 AI：

```text
这台机器有一套全局可复用的浏览器/搜索工具。
把当前这份手册所在目录记作 <工具根目录>。
不要默认使用旧的项目内副本。

如果当前终端已经在 <工具根目录>，优先直接运行：

.\bt.ps1 pw:smoke
.\bt.ps1 chrome:debug
.\bt.ps1 pw:cdp -- https://example.com
.\bt.ps1 bu:doctor
.\bt.ps1 bu:task -- "your task"

如果当前终端不在 <工具根目录>，就把命令里的 bt.ps1 换成 <工具根目录>\bt.ps1。

Playwright 不需要 API key。
browser-use 需要在 <工具根目录>\.env 中填写 OPENAI_API_KEY。
browser-use 当前默认走 Responses API，并默认关闭响应存储，同时默认开启 Codex 兼容身份字段。
如果网站需要登录或验证码，先运行 chrome:debug，用真实 Chrome 手工登录后再继续自动化。
```
