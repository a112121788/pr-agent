---
title: "附加配置"
sidebar_position: 10
---

这些设置适用于 Gitee PR-Agent。Webhook 和 CLI 见[用法与自动化](./automations_and_usage.md)。安装步骤见 [Gitee 集成指南](../installation/gitee.md)。

## 显示可用配置

默认值在 [`configuration.toml`](https://github.com/the-pr-agent/pr-agent/blob/main/pr_agent/settings/configuration.toml)。[工具](../tools/index.md)页面说明每个工具如何使用它们。渲染后的列表是[配置参考](./configuration_reference.md)。

在拉取请求上评论：

```text
/config
```

要附上工具实际使用的设置，操作者需在 `.pr_agent.toml` 或主机配置里设置 `config.output_relevant_configurations=true`。评论不能打开它，因为该段落可能显示主机控制的值。

### 显示代理运行详情 {#showing-the-agent-run-details}

要记录实际回答的模型、token 数量以及模型阶段耗时，请启用 `config.output_run_details`：

```text
/review --config.output_run_details=true
```

API 费用收集是另一个默认关闭的选项。两个开关都打开时，估算值会出现在运行详情里：

```text
/review --config.output_run_details=true --config.output_run_cost=true
```

`config.output_run_details` 是公开发布的闸门。只设置 `config.output_run_cost=true` 会收集费用，但不会把它写进评论。

在 Gitee 上，如果评论使用 GitHub 风味 Markdown，该段落会以可折叠块追加；否则为纯文本：

```text
⚙️ Agent run details
- Model: provider/fallback-model (fallback)
- Tokens: 12,340 in / 1,205 out / 13,545 total
- Time cost: 8.2s
- AI calls: 1
- Estimated API cost: $0.08 USD
```

`Model` 是产生回答的模型。当 `glm-5.3` 失败并由 `gpt-6.1-sol`（或其他备用模型）接手时，会标成 `(fallback)`。只有提供商报告了用量时才出现 `Tokens`。金额是根据 LiteLLM 价格数据做的估算，不是账单。公开段落只包含汇总费用和模型名称，不包含提示词、响应或 API 密钥。

`/improve` 只在发表汇总评论时追加该段落。只发行内建议时不会带上它。当 `pr_description.use_description_markers=true` 时，重复的 `/describe` 每次运行都会再累加一块。

## 从分析中忽略文件 {#ignoring-files-from-analysis}

用下面两项跳过生成文件或第三方文件：

- `IGNORE.GLOB`
- `IGNORE.REGEX`

只对一次命令忽略 Python 文件：

```text
/review --ignore.glob="['*.py']"
```

对所有拉取请求忽略它们：

```toml
[ignore]
glob = ['*.py']
```

或使用正则：

```toml
[ignore]
regex = ['.*\.py$']
```

`**/` 段匹配零个或多个目录，因此 `src/**/generated_*.py` 也会忽略 `src/generated_pb.py`。`*` 仍然可以跨越 `/`，所以 `['*.py']` 会忽略每一个 Python 文件。

每个 glob 列表最多额外保留 256 条零目录正则。独立 `**/` 段超过六个，或长度超过 256 个字符的模式不会被展开。已配置的模式，以及前导 `**/` 的根级形式，始终保留。只会被被跳过的变体匹配到的文件仍会进入分析。

## 额外指令 {#extra-instructions}

每个工具都接受 `extra_instructions`。例如：

```text
/update_changelog --pr_update_changelog.extra_instructions="Make sure to update also the version ..."
```

在 Gitee 上，`/update_changelog` 仍然只发表评论。提供商不支持 `push_code`，额外指令也不能促成一次提交。

## 语言设置

`response_language` 的随构建默认值是 `zh-CN`。用 [ISO 3166](https://en.wikipedia.org/wiki/ISO_3166) 和 [ISO 639](https://en.wikipedia.org/wiki/ISO_639) 的区域代码可以改变模型撰写文字的语言。[区域代码列表](https://simplelocalize.io/data/locales/)可供查阅。

```toml
[config]
response_language = "zh-CN"
```

只有模型生成的文字会被翻译。静态标签和表头保持发行时的语言。所用模型必须支持该区域设置。

## 日志级别

```toml
[config]
log_level = "DEBUG" # "DEBUG"、"INFO"、"WARNING"、"ERROR"、"CRITICAL"
```

默认是 `DEBUG`。Webhook 进程若要更安静，请使用 `INFO` 或 `WARNING`。

## 在提供商侧把请求归因到某个拉取请求

启用 `add_user_to_requests` 后，PR-Agent 会在 OpenAI 兼容的 `user` 字段里发送命令和拉取请求 URL：

```text
{"command":"improve","pr_url":"https://gitee.com/owner/repo/pulls/171"}
```

会保存该字段的提供商就可以把费用归因到某次拉取请求，而不必对照时间戳。该设置默认关闭，因为它会把 URL 分享给模型提供商。

```toml
[config]
add_user_to_requests = true
```

## 与日志可观测性平台集成

使用默认 LiteLLM 处理程序时，LiteLLM 回调可以直接工作。在 `configuration.toml` 里配置它们，并按 LiteLLM [文档](https://docs.litellm.ai/docs/)设置环境变量。

LangSmith 示例：

```toml
[litellm]
enable_callbacks = true
success_callback = ["langsmith"]
failure_callback = ["langsmith"]
service_callback = []
```

```bash
LANGSMITH_API_KEY=<api_key>
LANGSMITH_PROJECT=<project>
LANGSMITH_BASE_URL=<url>
```

Langfuse 示例（使用 `langfuse_otel`，不要使用旧的 `langfuse` 回调）：

```toml
[litellm]
enable_callbacks = true
success_callback = ["langfuse_otel"]
failure_callback = ["langfuse_otel"]
```

```bash
LANGFUSE_HOST=https://cloud.langfuse.com
LANGFUSE_PUBLIC_KEY=<public_key>
LANGFUSE_SECRET_KEY=<secret_key>
```

追踪会带上命令、Git 提供商（`gitee`）、拉取请求 URL、模型、token 数量和版本作为标签。

### 通过 LiteLLM 的 OpenTelemetry 集成发送 LLM 遥测 {#llm-telemetry-via-litellms-opentelemetry-integration}

要为模型调用本身发出 OpenTelemetry 追踪和指标，请启用 LiteLLM 的 `otel` 回调：

```toml
[litellm]
success_callback = ["otel"]
failure_callback = ["otel"]
turn_off_message_logging = true
```

请设置 `turn_off_message_logging = true`。否则 LiteLLM 可能附上提示词和响应，而这里面包含拉取请求 diff。

```bash
OTEL_EXPORTER=otlp_http
OTEL_EXPORTER_OTLP_ENDPOINT=https://collector:4318
OTEL_EXPORTER_OTLP_HEADERS=...
OTEL_SERVICE_NAME=pr-agent
LITELLM_OTEL_INTEGRATION_ENABLE_METRICS=true
```

未完成的回调会在 CLI 退出前刷新，时长受 `callback_timeout_seconds` 限制（见[自定义回调](#custom-callbacks)）。

### 自定义回调 {#custom-callbacks}

如果把 PR-Agent 嵌进自己的代码，可以注册 `litellm.CustomLogger`：

```python
import litellm
from pr_agent import cli

class UsageLogger(litellm.integrations.custom_logger.CustomLogger):
    async def async_log_success_event(self, kwargs, response_obj, start_time, end_time):
        record_usage(kwargs.get("model"), response_obj)

litellm.callbacks = [UsageLogger()]
cli.run_command("<pr_url>", "/review")
```

LiteLLM 在补全返回之后才运行回调。PR-Agent 会在 CLI 退出前刷新它们。用下面的值限制等待时间：

```toml
[litellm]
callback_timeout_seconds = 30 # 默认
```

## 内置 OpenTelemetry 命令遥测

PR-Agent 可以发出自己的命令层信号。它们覆盖在任何模型调用之前就失败的运行：

- **追踪**：每个请求一个 span，名为 `pr_agent <command>`，带有 `pr_agent.command`、`pr_agent.args_count`、`vcs.provider.name`、span 状态，以及失败时有界的 `error.type`。不会附上提示词和响应正文。
- **指标**：`pr_agent.commands`、`pr_agent.tokens` 和 `pr_agent.ai_calls`，按命令和 Git 提供商标签。token 序列还使用 `gen_ai.token.type`。零值会被跳过。

命令遥测和 [LLM 遥测](#llm-telemetry-via-litellms-opentelemetry-integration) 是分开的开关。两者都打开时，模型 span 是命令 span 的子节点。

```toml
[otel]
is_enabled = true
exporter_type = "console" # "console"、"otlp"、"prometheus" 或 "none"
service_name = "pr-agent"
environment = "production"
```

若要发给收集器，把 `exporter_type` 设为 `"otlp"`，并把端点写进 `.secrets.toml`：

```toml
[otel]
otlp_endpoint = "http://my-collector:4318"
otlp_headers = "x-honeycomb-team=YOUR_API_KEY"
```

默认使用 HTTP。`/v1/traces` 和 `/v1/metrics` 会追加到 `otlp_endpoint`。若用 gRPC，请安装 `pr-agent[otel-grpc]` 并设置 `otlp_protocol = "grpc"`。

如果 `exporter_type = "otlp"` 但没有配置端点，遥测会被关闭，不会回退到其他导出器。

### 暴露 Prometheus 指标

把 `exporter_type` 设为 `"prometheus"`，即可在 `gitee_app` 的 gunicorn 进程上提供 `GET /metrics`。抓取时会合并各 worker 的值：

```toml
[otel]
exporter_type = "prometheus"
prometheus_multiproc_dir = "/tmp/pr-agent-prometheus"
```

只有选中该导出器时才会挂载 `/metrics`。`prometheus_multiproc_dir` 必须能被每个 worker 写入。单进程运行时，导出器直接提供该进程自己的注册表，不需要这个目录。

```yaml
scrape_configs:
  - job_name: pr-agent
    static_configs:
      - targets: ["pr-agent:3000"]
```

隐私控制默认都关闭：

- `include_pr_url = true` 会把拉取请求 URL 放到 span 上。
- `include_error_details = true` 会把异常消息放到错误 span 上。异常类名始终会附上。

遥测是进程级的。它在启动时读取一次，不能由仓库的 `.pr_agent.toml` 打开。每次 OTLP 导出都受 `otlp_timeout` 限制（默认 3 秒）。

## 仓库上下文文件 {#bringing-per-repo-context-files-to-pr-agent}

PR-Agent 可以把仓库说明文件（例如 [AGENTS.md](https://agents.md/)）加进 `/review`、`/describe` 和 `/improve` 的提示词。

```toml
[config]
repo_context_files = ["AGENTS.md"]
```

路径相对于仓库。默认从仓库的**默认分支**读取（`repo_context_from_default_branch = true`），因此拉取请求不能提供用来审查自己的说明。缺少的文件会被跳过。把列表设为 `[]` 可以完全关闭该功能。

把 `repo_context_from_default_branch` 设为 `false` 后，改为从拉取请求的目标分支读取。文件仍然绝不会从源分支读取。

`repo_context_max_lines`（默认 `500`）限制渲染行数，包含包裹标签。

### 来自同级仓库的上下文 {#context-from-sibling-repositories}

宿主必须先批准仓库，使用方仓库才能选择其中的文件：

```toml
[config]
repo_context_sibling_repos = ["my-org/library"]
repo_context_max_sibling_files = 5
```

允许列表和获取上限只属于主机。允许列表为空时，不会读取同级仓库。使用方的 `.pr_agent.toml` 随后可以使用结构化条目：

```toml
[config]
repo_context_files = [
    "AGENTS.md",
    {repo_id = "my-org/library", file_path = "src/api.py"},
]
```

请使用 `所有者/仓库`。同级仓库必须与当前仓库属于同一个所有者。同级文件来自它们的默认分支，并与本地文件共享 `repo_context_max_lines`。评论参数不能覆盖 `repo_context_files`。

## 忽略拉取请求中的自动命令 {#ignoring-automatic-commands-in-prs}

PR-Agent 可以按以下条件跳过拉取请求：

- 标题（正则）
- 源分支或目标分支（正则）
- 仓库（正则）
- 没有改到的目录
- 标签
- 作者

标题、作者、标签、仓库、源分支和目标分支规则也适用于 `/review`、`/ask` 这类评论命令，以及 CLI 的 `--pr_url` 运行。`ignore_pr_authors` 匹配的是**拉取请求作者**，不是发表评论的人。被忽略的 CLI 请求会成功退出，且不运行工具。

### 标题

```toml
[config]
ignore_pr_title = ["\\[Bump\\]"]
```

默认值是 `["^\\[Auto\\]", "^Auto"]`。`^Auto` 也会匹配 “Autoscaling fix” 这类普通标题，这些拉取请求的手动命令同样会被跳过。如果这不是预期行为，请收窄模式，或设置 `ignore_pr_title = []`。

### 分支

```toml
[config]
ignore_pr_source_branches = ['develop', 'main', 'master', 'stage']
ignore_pr_target_branches = ["qa"]
```

两个列表互不依赖。每一项都是正则。

### 仓库

```toml
[config]
ignore_repositories = ["my-org/my-repo1", "my-org/my-repo2"]
```

### 目录

```toml
[config]
allow_only_specific_folders = ['folder1', 'folder2']
```

只有变更路径包含其中一个目录时，才会运行自动反馈。

### 标签

```toml
[config]
ignore_pr_labels = ["do-not-merge"]
```

### 作者

```toml
[config]
ignore_pr_authors = ["my-special-bot-user"]
```

每一项都是与作者用户名匹配的正则。

### 按语言或框架忽略生成文件

```toml
[config]
ignore_language_framework = ['protobuf']
```

模式列在 [`generated_code_ignore.toml`](https://github.com/the-pr-agent/pr-agent/blob/main/pr_agent/settings/generated_code_ignore.toml)。

## 变更日志输出

Gitee 不能 `push_code`。即使 `pr_update_changelog.push_changelog_changes` 为 true，`/update_changelog` 也只生成变更日志并作为拉取请求评论发表。不会创建提交，也不需要任何 Git 托管平台的工作流文件。
