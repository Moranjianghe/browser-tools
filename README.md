# Browser Tools

本目录已经配置好两套本地浏览器自动化工具：

- `Playwright`：适合稳定、精确、可复现的网页导航、抓取和 PDF 下载。
- `browser-use`：适合复杂网页流程、登录态复用、需要 agent 自主操作的站点。

## 目录结构

- `scripts/`：启动与验证脚本
- `.venv/`：`browser-use` 使用的 Python 虚拟环境
- `profiles/`：共享浏览器用户数据目录
- `downloads/`：下载目录
- `.env.example`：环境变量示例
- `requirements.txt`：Python 依赖清单
- `setup.ps1`：Windows 下的一键初始化脚本

## 首次使用

1. 初始化依赖：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\setup.ps1 -CopyEnv
```

这会自动：

- 创建 `.venv`
- 安装 `requirements.txt` 里的 Python 依赖
- 执行 `npm install`
- 如果当前没有 `.env`，自动从 `.env.example` 复制一份

2. 如果你不想用初始化脚本，也可以手动复制环境变量模板：

```powershell
Copy-Item .env.example .env
```

3. 按需要填写 `.env`：

- 默认已经按 OpenAI / Codex 兼容接口预留好字段，补上 `OPENAI_API_KEY` 即可
- 默认按 `Responses API` 工作，并关闭响应存储以对齐 Codex 桌面配置
- 如果你使用自定义兼容网关，可修改 `OPENAI_BASE_URL`、`BROWSER_USE_MODEL`、`BROWSER_USE_REASONING_EFFORT`
- `CHROME_PATH` 和 `BROWSER_PROFILE_DIR` 都可以留空，脚本会优先使用默认路径
- 如果你准备用 browser-use 自己的模型，改成 `BROWSER_USE_LLM=browser-use` 并填写 `BROWSER_USE_API_KEY`

4. 如果需要登录网站、保留会话、人工过验证码，先启动一个共享 Chrome：

```powershell
npm run chrome:debug
```

这会用 `profiles/shared` 目录启动一个带远程调试端口的真实 Chrome。你可以在里面手工登录一次，后续 `Playwright` 或 `browser-use` 都能复用这套状态。

## 常用命令

### 1. 验证 Playwright 是否正常

```powershell
npm run pw:smoke
```

### 2. 连接到已打开的调试 Chrome

```powershell
npm run pw:cdp -- https://example.com
```

### 3. 检查 browser-use 环境

```powershell
npm run bu:doctor
```

### 4. 运行 browser-use 任务

```powershell
npm run bu:task -- "Open arXiv and find the PDF download link for a paper"
```

如果你准备用 Codex 兼容模型，推荐 `.env` 至少包含：

```powershell
BROWSER_USE_LLM=openai
BROWSER_USE_MODEL=gpt-5.4-mini
BROWSER_USE_REASONING_EFFORT=medium
BROWSER_USE_PREFERRED_SEARCH_ENGINES=google.com,duckduckgo.com
BROWSER_USE_PREFERRED_SOURCES=official websites,company help centers,government pages,academic papers,reputable English-language sources
OPENAI_WIRE_API=responses
OPENAI_DISABLE_RESPONSE_STORAGE=true
OPENAI_BASE_URL=https://www.openclaudecode.cn/v1
OPENAI_API_KEY=你的密钥
```

## 推荐工作流

### 读论文原文、处理登录和验证码

1. 运行 `npm run chrome:debug`
2. 在 Chrome 里手工登录目标网站
3. 需要精确下载和抓取时，用 `Playwright`
4. 需要 agent 自主完成复杂点击流程时，用 `browser-use`

### 注意事项

- 如果共享 Chrome 还开着，`browser-use` 更适合通过 `BROWSER_CDP_URL` 附着到这个会话，而不是再单独抢占同一个 profile 目录。
- `browser-use` 在 Windows 终端下容易遇到编码问题，所以脚本已经自动设置了 `UTF-8` 输出。
- 某些网站即使用真实浏览器也仍可能触发验证码，这时最稳的方式依然是你手工过一次，我再继续接管后续流程。
- 当前本地 `browser-use` 包装器默认按 OpenAI/Codex 兼容接口的 `Responses API` 接入。
- 如果你的兼容网关反而只支持旧的 `chat/completions`，可以把 `.env` 里的 `OPENAI_WIRE_API` 改回 `chat`。
- 默认推荐 `gpt-5.4-mini + medium reasoning`，兼顾稳定性和成本，比较适合网页检索任务。
- 默认不强制禁用任何域名，只通过提示词控制优先级。
- 可以用 `BROWSER_USE_PREFERRED_SEARCH_ENGINES=google.com,duckduckgo.com` 指定浏览器 agent 必须使用搜索引擎时的优先顺序。
- 如果确实要禁用某些域名，再显式设置 `BROWSER_USE_BLOCKED_DOMAINS=...`，或者运行时追加 `--block-domain ...`。
- 可以临时在命令行追加 `--block-domain baidu.com` 或 `--model gpt-5.4-mini` 覆盖本次运行。
- 当前目录是 Windows 优先方案：PowerShell、`.venv\\Scripts\\python.exe`、Chrome/Edge 默认路径都按 Windows 处理。
- 如果要迁移到另一台 Windows 机器，优先复制整个目录后运行 `setup.ps1`，再补 `.env`。
