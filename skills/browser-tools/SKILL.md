---
name: browser-tools
description: "Use when Codex needs to operate real websites on a Windows machine through a local checkout of the browser-tools repository, including Playwright navigation, browser-use agent tasks, attaching to a logged-in Chrome via CDP, precise downloads or PDF capture, 登录态复用, 验证码接力, or other local browser automation workflows."
---

# Browser Tools

调用本地 `browser-tools` 仓库里的浏览器工具链。优先用它处理必须落到真实浏览器的任务，不要在需要登录态、验证码或精确下载时退回纯文本抓取。

## 固定入口

先运行仓库里的安装脚本，把这个 skill 安装到本机 Codex skill 目录。安装完成后，统一通过下面的包装器调用：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File ~\.codex\skills\browser-tools\scripts\invoke-browser-tools.ps1 <action> [args...]
```

如果你设置了 `CODEX_HOME`，把上面的 `~\.codex` 换成 `$env:CODEX_HOME`。

这个包装器会在安装时自动绑定当前仓库路径，不需要把绝对路径写进仓库文件。

## 先做体检

在开始复杂任务前，先确认 Playwright 可用：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File ~\.codex\skills\browser-tools\scripts\invoke-browser-tools.ps1 pw:smoke
```

在任务需要 `browser-use` 时，再补一遍环境检查：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File ~\.codex\skills\browser-tools\scripts\invoke-browser-tools.ps1 bu:doctor
```

如果任一步失败，先修环境，不要直接跑长任务。

## 选择执行路径

- 用 `Playwright`：页面结构稳定、目标 URL 已知、需要可复现点击/抓取、下载 PDF。
- 先开 `chrome:debug`：需要登录、保留会话、手工过验证码。
- 用 `pw:cdp`：已经有调试 Chrome，希望在已有登录态上做精确操作。
- 用 `browser-use`：需要自主搜索、跨多页导航、让 agent 决定下一步点击。
- 共享 Chrome 已占用 profile 时，优先 CDP 附着，不要再起一个新浏览器抢同一 profile。

## 常用调用

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File ~\.codex\skills\browser-tools\scripts\invoke-browser-tools.ps1 pw:smoke
powershell -NoProfile -ExecutionPolicy Bypass -File ~\.codex\skills\browser-tools\scripts\invoke-browser-tools.ps1 chrome:debug
powershell -NoProfile -ExecutionPolicy Bypass -File ~\.codex\skills\browser-tools\scripts\invoke-browser-tools.ps1 pw:cdp -- https://example.com
powershell -NoProfile -ExecutionPolicy Bypass -File ~\.codex\skills\browser-tools\scripts\invoke-browser-tools.ps1 bu:doctor
powershell -NoProfile -ExecutionPolicy Bypass -File ~\.codex\skills\browser-tools\scripts\invoke-browser-tools.ps1 bu:task -- "Find the official PDF download link for a paper"
```

给 `bu:task` 写短指令。超过约 5 个动作时，拆成多个子任务。需要登录态时，优先追加 `--cdp-url http://127.0.0.1:9223`，不要复用同一 profile 目录启动第二个浏览器实例。

## 环境前提

- `<repo-root>\.venv` 必须存在。
- 运行 `browser-use` 前，`<repo-root>\.env` 里至少要有 `OPENAI_API_KEY`。
- 未初始化时，先在仓库根目录运行：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\setup.ps1 -CopyEnv
```

## 参考

需要具体命令、典型流程、环境变量或清理命令时，读 `references/workflows.md`。
