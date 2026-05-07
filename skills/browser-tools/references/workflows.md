# Browser Tools Workflows

## 路径

- 工具根目录：`<repo-root>`
- Skill 包装器：`~\.codex\skills\browser-tools\scripts\invoke-browser-tools.ps1`
- 共享 profile：`<repo-root>\profiles\shared`
- 下载目录：`<repo-root>\downloads`
- 默认调试端口：`9223`

如果你设置了 `CODEX_HOME`，把 `~\.codex` 替换为 `$env:CODEX_HOME`。

## 安装

在仓库根目录运行：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\install-codex-skill.ps1
```

这个脚本会把 `skills/browser-tools/` 安装到本机 Codex skill 目录，并把包装器里的仓库根路径写成当前 checkout 的实际路径。仓库里的模板文件不会包含用户真实路径。

## 初始化

首次安装或环境损坏时，先在仓库根目录运行：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\setup.ps1 -CopyEnv
```

在运行 `browser-use` 前，至少确认 `.env` 中有这些配置：

```text
OPENAI_API_KEY=
BROWSER_USE_LLM=openai
BROWSER_USE_MODEL=gpt-5.4-mini
BROWSER_USE_REASONING_EFFORT=medium
OPENAI_WIRE_API=responses
OPENAI_DISABLE_RESPONSE_STORAGE=true
```

可按需补充：

- `BROWSER_CDP_URL=http://127.0.0.1:9223`
- `BROWSER_USE_BLOCKED_DOMAINS=...`
- `BROWSER_USE_PREFERRED_SEARCH_ENGINES=google.com,duckduckgo.com`
- `BROWSER_USE_PREFERRED_SOURCES=official websites,company help centers,government pages,academic papers,reputable English-language sources`

## 命令速查

统一通过 skill 包装器调用：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File ~\.codex\skills\browser-tools\scripts\invoke-browser-tools.ps1 pw:smoke
powershell -NoProfile -ExecutionPolicy Bypass -File ~\.codex\skills\browser-tools\scripts\invoke-browser-tools.ps1 chrome:debug
powershell -NoProfile -ExecutionPolicy Bypass -File ~\.codex\skills\browser-tools\scripts\invoke-browser-tools.ps1 chrome:debug https://example.com
powershell -NoProfile -ExecutionPolicy Bypass -File ~\.codex\skills\browser-tools\scripts\invoke-browser-tools.ps1 pw:cdp -- https://example.com
powershell -NoProfile -ExecutionPolicy Bypass -File ~\.codex\skills\browser-tools\scripts\invoke-browser-tools.ps1 bu:doctor
powershell -NoProfile -ExecutionPolicy Bypass -File ~\.codex\skills\browser-tools\scripts\invoke-browser-tools.ps1 bu:task -- "Find the official PDF download link for a paper"
powershell -NoProfile -ExecutionPolicy Bypass -File ~\.codex\skills\browser-tools\scripts\invoke-browser-tools.ps1 bu:task -- --cdp-url http://127.0.0.1:9223 "Open the current logged-in site and export the report"
powershell -NoProfile -ExecutionPolicy Bypass -File ~\.codex\skills\browser-tools\scripts\invoke-browser-tools.ps1 bu:task -- --model gpt-5.4-mini --block-domain baidu.com "Search for the official policy page"
```

## 推荐流程

### 登录、验证码、会话复用

1. 运行 `chrome:debug`。
2. 在真实 Chrome 中手工完成登录或验证码。
3. 精确后续操作优先用 `pw:cdp`。
4. 需要 agent 自主探索时，再用 `bu:task -- --cdp-url http://127.0.0.1:9223 ...`。

共享调试 Chrome 已打开时，优先附着到现有会话，不要再让另一个浏览器实例直接抢同一 profile 目录。

### 论文原文、PDF、稳定页面

1. 先跑 `pw:smoke`。
2. 目标 URL 明确时，优先用 `Playwright` 路径。
3. 需要登录态时，先 `chrome:debug`，再 `pw:cdp`。
4. 下载文件默认落到 `downloads` 目录，必要时再移动到项目目录。

### 自主搜索与复杂多步网页任务

1. 先跑 `bu:doctor`。
2. 给 `bu:task` 写短指令，只放一个主要目标。
3. 超过约 5 个动作时，拆成多个子任务顺序执行。
4. 需要限制来源时，优先用 `--block-domain` 或 `.env` 里的 `BROWSER_USE_BLOCKED_DOMAINS`。

## 故障排查与收尾

任务结束后，手工关闭调试 Chrome 窗口。

如果页面持续跳转、不断开新页，执行：

```powershell
Get-CimInstance Win32_Process |
  Where-Object { $_.CommandLine -match 'browser-use-user-data-dir|playwright_chromiumdev_profile|cliDaemon.js profile-highlight-smoke' } |
  ForEach-Object { Stop-Process -Id $_.ProcessId -Force }
```

如果 `pw:cdp` 连不上，检查端口是否仍在监听：

```powershell
Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue |
  Where-Object { $_.LocalPort -eq 9223 }
```

如果 `browser-use` 输出乱码，优先在当前终端切到 UTF-8 再重试；项目脚本本身已经设置了 `PYTHONUTF8=1` 和 `PYTHONIOENCODING=utf-8`。
