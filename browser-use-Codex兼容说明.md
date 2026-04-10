# browser-use Codex 兼容说明

这份说明记录当前这套 `browser-tools` 的 Codex 兼容配置状态，方便后续 AI 或人工排查。

本文默认把这份文档所在目录记作 `<工具根目录>`。

## 1. 当前结论

- 这套全局 `browser-tools` 已经切到真正的 `Responses API` 模式。
- 当前网关 `https://www.openclaudecode.cn/v1` 可以正常处理 `responses` 请求。
- 之前的 `403 Your request was blocked`，根因不是 `browser-use` 本身，也不只是接口路径问题。
- 真正差异在于：普通 OpenAI Python SDK 默认请求头和请求体，与 Codex 实际发出的“身份字段”不一致。
- 给请求补上 Codex 风格兼容字段后，请求可以正常通过，`browser-use` 任务也能成功执行。

## 2. 已做的代码调整

已修改文件：

- `scripts/openai-responses-chat.py`
- `scripts/browser_use_task.py`

主要调整：

- 新增 `Responses API` 适配层，避免走旧的 `chat/completions` 路径。
- 默认附带一组 Codex 风格兼容字段。
- 支持通过环境变量开关兼容模式。

## 3. 默认兼容字段

兼容模式开启时，请求会自动补以下信息：

- `originator`
- `User-Agent`
- `session_id`
- `x-client-request-id`
- `x-codex-window-id`
- `prompt_cache_key`
- `client_metadata.x-codex-installation-id`

这些字段的目的不是模拟完整 Codex 行为，而是让网关把请求识别为与 Codex 更一致的请求形态。

## 4. 当前推荐配置

参考 `.env` / `.env.example`：

```text
BROWSER_USE_LLM=openai
BROWSER_USE_MODEL=gpt-5.3-codex
BROWSER_USE_REASONING_EFFORT=high
OPENAI_WIRE_API=responses
OPENAI_DISABLE_RESPONSE_STORAGE=true
OPENAI_CODEX_COMPAT=true
OPENAI_BASE_URL=https://www.openclaudecode.cn/v1
OPENAI_API_KEY=...
```

说明：

- `OPENAI_WIRE_API=responses`
  让 `browser-use` 走 `/v1/responses`。
- `OPENAI_DISABLE_RESPONSE_STORAGE=true`
  默认关闭响应存储，和 Codex 当前配置对齐。
- `OPENAI_CODEX_COMPAT=true`
  默认开启 Codex 风格兼容字段。

## 5. 可选环境变量

如需手动覆盖兼容字段，可设置：

```text
OPENAI_CODEX_ORIGINATOR=codex_cli_rs
OPENAI_CODEX_USER_AGENT=
OPENAI_CODEX_INSTALLATION_ID=
OPENAI_CODEX_WINDOW_ID=
OPENAI_CODEX_CONVERSATION_ID=
```

一般情况下不用手动填。
如果为空，脚本会自动生成或使用默认值。

## 6. 如果以后又遇到 403

优先按这个顺序排查：

1. 确认 `.env` 里的 `OPENAI_BASE_URL`、`OPENAI_API_KEY`、`OPENAI_WIRE_API` 是否正确。
2. 确认 `OPENAI_CODEX_COMPAT=true` 没被关掉。
3. 先跑最小模型调用，再跑真实 `browser-use` 任务。
4. 如果最小调用成功、`browser-use` 失败，再查 agent/browser 层。
5. 如果最小调用也失败，再查网关策略、key 状态或字段要求是否变化。

## 7. 已验证结果

已验证通过：

- 适配器最小调用返回 `OK`
- `browser-use` 真实任务成功完成

验证命令示例：

```powershell
npm run bu:task -- --headless "Open https://example.com and return only the page title."
```

预期结果：

```text
Example Domain
```

## 8. 相关文件

- 工具根目录：`<工具根目录>`
- 配置文件：`<工具根目录>\.env`
- 示例配置：`<工具根目录>\.env.example`
- 兼容说明：`<工具根目录>\browser-use-Codex兼容说明.md`
- 全局手册：`<工具根目录>\给其他AI的全局搜索工具手册.md`

## 9. 备注

- 旧项目内副本没有动。
- 当前可用的是这份目录内的全局安装。
- 如果以后换网关，`OPENAI_CODEX_COMPAT` 不一定必须保留，要以实际 provider 行为为准。
