---
title: "附加配置"
sidebar_position: 10
---

## 显示可用配置

PR-Agent 的可用配置存放在<a href="https://github.com/the-pr-agent/pr-agent/blob/main/pr_agent/settings/configuration.toml" target="_blank" rel="noopener noreferrer">这里</a>。
在[工具](../tools/index.md)页面可以找到如何为每个工具使用这些配置的说明。

要把所有可用配置作为评论打印到 PR 上，可以使用以下命令：

```
/config
```

<img src="/img/possible_config1.png" alt="possible_config1" width="512" />

要查看某个工具在应用全部用户设置之后**实际**使用的配置，
授权操作者可以在 `.pr_agent.toml` 中设置 `config.output_relevant_configurations=true`。
评论中提供的参数不能开启这项输出，因为它可能泄露主机侧控制的设置。

<img src="/img/possible_config2.png" alt="possible_config2" width="512" />

### 显示代理运行详情 {#showing-the-agent-run-details}

要查看实际作答的模型、本次运行消耗的 token 数，以及 AI 处理阶段耗时，请启用 `config.output_run_details`：

```
/review --config.output_run_details=true
```

API 费用采集是另一项默认关闭的选项，由 `config.output_run_cost` 控制。同时启用两个标志才会采集费用，并把它加进运行详情部分：

```
/review --config.output_run_details=true --config.output_run_cost=true
```

`config.output_run_details` 仍然是公开输出的闸门：只设置 `config.output_run_cost=true` 会采集运行级费用数据，但绝不会把它加进 PR 评论。

在支持 GitHub Flavored Markdown 的平台上，这会在生成的评论末尾追加一个可折叠部分；在其他平台上，`/review` 和 `/describe` 会以纯文本追加同样的信息：

```
⚙️ Agent run details
- Model: provider/fallback-model (fallback)
- Tokens: 12,340 in / 1,205 out / 13,545 total
- Time cost: 8.2s
- AI calls: 1
- Estimated API cost: $0.08 USD
  - anthropic/claude-opus-5: $0.07 USD
  - anthropic/claude-sonnet-5: $0.01 USD
```

`Model` 显示产出答案的模型；当主模型失败并由备用模型接管时，会标记 `(fallback)`。只有模型提供商报告了用量时才会出现 `Tokens` 行。`AI calls` 统计本次运行中成功的 LLM 调用次数。该标志默认关闭。

`Estimated API cost` 由每次已完成的 LiteLLM 响应及其最终用量同步得出。当响应及其定价数据包含这些信息时，LiteLLM 可以计入缓存读取、缓存写入、推理 token 以及提供商特定的用量类别。多模型运行会给出已知费用的紧凑分解。聚合时保留精确的 `Decimal` 值，而公开的货币输出四舍五入到两位小数；本会四舍五入为零的极小正数会显示为 `<$0.01`，而不是 `$0.00`。如果只有部分成功调用能够定价，总额会标记为 `partial`，并带上已定价的调用次数；如果没有任何调用能够定价，该行会报告 `unavailable`。缺失的定价绝不会渲染成 `$0`。

该金额是基于 LiteLLM 定价数据的估算，不是以提供商发票为准的账单。在用于核算或费用分摊之前，请与提供商的账单记录核对。流式响应只有在最终用量可用之后才会定价；异步回调以及短暂的 `response_cost` 回调元数据不会被当作唯一事实来源。公开部分只包含汇总费用和已配置的模型名称，绝不包含提示词、响应正文、API 密钥或提供商请求 ID。

说明：

- `/improve` 只有在发布摘要评论时才会追加该部分。如果平台不支持 GFM，或者启用了 `pr_code_suggestions.committable_code_suggestions`，`/improve` 会改为发布行内评论，因此不会出现运行详情部分。
- 当 `pr_description.use_description_markers=true` 时，重复运行 `/describe` 会每次累积一块运行详情，因为现有 PR 描述会被保留，只替换标记。

## 从分析中忽略文件 {#ignoring-files-from-analysis}

有时你可能希望把特定文件或目录排除在 PR-Agent 的分析之外。例如，当存在自动生成的文件，或不应该被审查的文件（如供应商代码）时，这会很有用。

可以用以下方法忽略文件或文件夹：

- `IGNORE.GLOB`
- `IGNORE.REGEX`

你可以编辑它们，按 glob 或正则模式忽略文件或文件夹。

### 用法示例

来看一个例子：我们希望从分析中忽略所有扩展名为 `.py` 的文件。

在线使用时，要在某个 PR 中忽略 Python 文件，在 PR 上评论：
`/review --ignore.glob="['*.py']"`

要在所有 PR 中用 `glob` 模式忽略 Python 文件，在配置文件中设置：

```
[ignore]
glob = ['*.py']
```

要在所有 PR 中用 `regex` 模式忽略 Python 文件，在配置文件中设置：

```
[ignore]
regex = ['.*\.py$']
```

`glob` 模式中的 `**/` 段匹配零个或多个目录，因此 `src/**/generated_*.py` 也会忽略 `src/generated_pb.py`，而不仅仅是 `src/api/generated_pb.py`。注意 `*` 仍然会跨越 `/` 匹配，就像上面的 `['*.py']` 那样。

每个忽略 glob 列表最多额外保留 256 个互不相同的零目录正则。包含超过六个独立 `**/` 段、或长度超过 256 个字符的模式不会被展开。已配置的模式，以及前导 `**/` 现有的根级形式，始终保留，并且不计入该上限。被跳过的变体会按每个列表报告一次；仅被这些变体匹配到的文件仍会被分析。

该上限分别适用于 `ignore.glob` 以及每个已启用的 `ignore_language_framework` 列表。完全由星号和分隔符组成的 glob（例如 `**/**/**`）在零目录展开之后可以匹配所有文件。

## 额外指令 {#extra-instructions}

所有 PR-Agent 工具都有一个名为 `extra_instructions` 的参数，用于添加自由文本的额外指令。用法示例：

```
/update_changelog --pr_update_changelog.extra_instructions="Make sure to update also the version ..."
```

## 语言设置

PR-Agent 的默认响应语言是**美式英语**。不过，有些开发团队可能希望用其他语言展示信息。例如，如果把 PR 描述和代码建议设为你们国家的母语，团队工作流可能会更顺畅。

要进行配置，请在配置文件中设置 `response_language` 参数。这会提示模型用指定语言回答。请使用基于 [ISO 3166](https://en.wikipedia.org/wiki/ISO_3166)（国家代码）和 [ISO 639](https://en.wikipedia.org/wiki/ISO_639)（语言代码）的**标准区域设置代码**，来定义语言-国家组合。参见这份[区域设置代码完整列表](https://simplelocalize.io/data/locales/)。

示例：

```toml
[config]
response_language = "it-IT"
```

这会把所有命令的响应语言全局设为意大利语。

> **重要：** 请注意，只有 AI 模型生成的动态文本会翻译成所配置的语言。标签、表头等不属于 AI 模型响应的静态文本仍会保持美式英语。此外，你使用的模型必须对指定语言有良好支持。

[//]: # (## 处理大型 PR)

[//]: # ()

[//]: # (CodiumAI 的默认模式是每个工具一次调用，使用 token 上限为 8000 的 GPT-4。)

[//]: # (该模式在速度、质量与成本之间取得了很好的平衡，可以成功处理大多数 PR。)

[//]: # (当 PR 超过 token 上限时，会采用 [PR 压缩策略]&#40;../core-abilities/index.md&#41;。)

[//]: # ()

[//]: # (不过，对于非常大的 PR，或者你希望优先保证质量而非速度和成本时，有两种可行方案：)

[//]: # (1&#41; [使用上下文更大的模型]&#40;./changing_a_model.md&#41;，例如 GPT-32K 或 claude-100K。该方案适用于所有工具。)

[//]: # (2&#41; 对于 `/improve` 工具，有一种 [“extended” 模式]&#40;../tools/improve.md&#41; &#40;`/improve --extended`&#41;，)

[//]: # (它把 PR 分成多个块，并分别处理每个块。在此模式下，无论使用哪种模型都不会压缩 &#40;但对于大型 PR，可能会发生多次模型调用&#41;)


## 展开 GitLab 子模块 diff

默认情况下，GitLab 合并请求把子模块更新显示为 `Subproject commit` 行。要在 PR-Agent 分析中包含这些子模块的实际文件级变更，请启用：

```toml
[gitlab]
expand_submodule_diffs = true
```

启用后，PR-Agent 会获取并附加来自子模块仓库的 diff。默认值为 `false`，以避免额外的 GitLab API 调用。

`.gitmodules` 中的子模块 URL 可以是绝对地址（`https://`、`ssh://`、`git@host:`），也可以是相对地址（`../group/repo.git`）。相对 URL 会按 git 的方式，相对合并请求的项目路径进行解析。

因为 `.gitmodules` 来自合并请求的 head，目标项目由打开该合并请求的人选定。因此 PR-Agent 会用与授权[同级仓库](#context-from-sibling-repositories)相同的方式授权每个子模块目标：目标必须列在 `config.repo_context_sibling_repos` 中，必须位于合并请求项目自己的顶级命名空间内，并且必须能被触发该命令的用户读取。未通过其中任一检查的目标会被跳过并给出警告，父级 gitlink 变更则保持原样。把每个希望展开的子模块加入允许列表：

```toml
[config]
repo_context_sibling_repos = ["my-group/my-submodule"]
```

## 将审查发布为 GitLab 讨论串

默认情况下，PR-Agent 把 `/review` 摘要发布为普通评论。要改为发布成可解决的讨论串（GitLab discussion），请启用（默认：`false`）：

```toml
[gitlab]
publish_review_as_thread = true
```
- 当 `pr_reviewer.persistent_comment=true`（默认值）时，每次运行都会更新已有的审查讨论串；如果它已被解决，会重新打开，以便刷新后的审查再被看一遍。
- 启用该标志不会把已经以普通评论发布的审查转换成讨论串：它会继续原地更新，而 GitLab 无法把一条评论提升为讨论串。只有在设置该标志之后才第一次运行审查的 MR 才会得到讨论串。
- 将 `pr_reviewer.persistent_comment=false` 可改为在每次运行时新开一条审查讨论串。

## 回复触发命令的 GitLab 讨论

默认情况下，`/review` 和 `/improve` 会发布一条新评论。要在触发该命令的 GitLab 讨论内部回复，请启用（默认：`false`）：

```toml
[gitlab]
reply_to_trigger_comment = true
```

这是可选功能，且仅适用于 GitLab。Webhook 会为顶层的 `/review` 和 `/improve` 评论提供讨论 ID。如果 ID 不可用或回复失败，PR-Agent 会回退为普通评论，以免丢失输出。GitHub Conversation 评论没有兼容的回复端点。

当 `persistent_comment=true`（两个工具的默认值）时，再次运行会更新早先结果首次发布的位置，那可能是另一条讨论；`/review` 还会在新命令的讨论里发布一条指向它的短链接。

## 将 /improve 建议发布为 GitLab 讨论串

默认情况下，PR-Agent 把 `/improve` 建议发布为普通评论。要改为发布成可解决的讨论串（GitLab discussion），请启用（默认：`false`）：

```toml
[gitlab]
publish_improve_as_thread = true
```

- 一次运行如果没有找到建议，会原地编辑该讨论串并解决它，这样状态消息就不会留下一条未解决的讨论串。

## 解决过时的 GitLab 行内讨论串

每条行内建议都锚定在它发布时所针对的 MR head 提交上。当后续推送移动了 head 时，GitLab 会把该讨论串标记为属于过时的 diff 版本：它会渲染为空、失去 `Resolve` 控件，此后只能通过 API 关闭，于是被取代的建议会在长期存在的 MR 上堆积。要让 PR-Agent 在发布新一批行内建议之前解决这些讨论串，请启用（默认：`false`）：

```toml
[gitlab]
resolve_outdated_inline_threads = true
```

只有同时满足以下全部条件时，讨论串才会被解决，因此任何带有人工回复的讨论串都不会被关闭：

- 该讨论串是 PR-Agent 自己打开的，依据正文判断：它带有去重标记（这是证据，并且每条行内审查发现都有），或者它以行内建议发布时使用的 `**Suggestion:**` 开头（这是强提示而非证据，因为人也可能这样输入）。正是这一点避免清掉同一账号手写的评论；这很重要，因为 GitLab 令牌常常属于某个人，而不是专用的机器人用户；
- 其中每条非系统评论都由同一个用户撰写，因此只要有一条人工回复，该讨论串就会被留下。GitLab 系统评论会被忽略，因为标记讨论串已过时的“在 diff 的第 N 版中更改了这一行”评论，作者是执行推送的人；
- 该讨论串尚未解决，并且锚定在 diff 的某一行上；
- 该锚点中记录的 head SHA 与 MR 当前 diff 的 head SHA 不同。

任何无法确认的情况（无法读取的位置、未知的当前 head SHA、无法解析的机器人身份）都会被跳过，而不是被解决。

请注意，锚点记录的 head SHA 在讨论串创建之后不会改变，因此任何早于最新一次推送的 PR-Agent 讨论串都符合条件，包括 GitLab 仍渲染在未变更行上的那些。启用 `config.persistent_inline_comments` 后，下一次运行会重新发布仍然适用的建议，因此效果是解决并重新发布，而不是删除。

## 日志级别

PR-Agent 允许你通过 `log_level` 配置参数控制日志详细程度。这在排查和调试 PR 工作流问题时特别有用。

```
[config]
log_level = "DEBUG"  # Options: "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"
```

默认日志级别是 "DEBUG"，会提供所有操作的详细输出。如果希望日志不那么冗长，可以设置更高的级别，例如 "INFO" 或 "WARNING"。

## 在提供商侧把请求归因到某个 PR

启用 `add_user_to_requests` 后，PR-Agent 会在 OpenAI 兼容的 `user` 请求字段中发送当前命令和 PR URL，形式为紧凑的 JSON 字符串：

```
{"command":"improve","pr_url":"https://gitlab.example.com/group/project/-/merge_requests/171"}
```

按请求记录该字段的提供商（例如 OpenRouter，它在生成详情中将其显示为 `external_user`，并包含在活动导出中）就可以把每个请求及其费用和结果归因到特定的 PR 和命令，而无需按时间戳关联。

```
[config]
add_user_to_requests = true
```

该设置默认关闭，因为它会与模型提供商共享请求归因数据：启用它是操作者的明确选择。

## 与日志可观测性平台集成

使用默认的 LiteLLM AI Handler 时，各种日志可观测性工具可以开箱即用。只需在 `configuration.toml` 中配置 LiteLLM 回调设置，并按照 LiteLLM [文档](https://docs.litellm.ai/docs/)设置环境变量。

例如，要使用 [LangSmith](https://www.langchain.com/langsmith)，可以在 `configuration.toml` 文件中添加以下内容：

```
[litellm]
enable_callbacks = true
success_callback = ["langsmith"]
failure_callback = ["langsmith"]
service_callback = []
```

然后设置以下环境变量：

```
LANGSMITH_API_KEY=<api_key>
LANGSMITH_PROJECT=<project>
LANGSMITH_BASE_URL=<url>
```

要使用 [Langfuse](https://langfuse.com) 跟踪利用率和采用情况（LLM 费用、token 用量、延迟，以及去重后的仓库采用情况），在配置中添加以下内容：

```toml
[litellm]
enable_callbacks = true
success_callback = ["langfuse_otel"]
failure_callback = ["langfuse_otel"]
```

> 注意：请使用 `langfuse_otel`（基于 OpenTelemetry 的集成），而不是旧版 `langfuse` 回调——旧版回调与本项目锁定的 Langfuse 3.x SDK 不兼容。

然后设置以下环境变量：

```
LANGFUSE_HOST=https://cloud.langfuse.com
LANGFUSE_PUBLIC_KEY=<public_key>
LANGFUSE_SECRET_KEY=<secret_key>
```

每次 LLM 调用都会以命令名、Git 平台、PR URL、模型、token 计数和版本作为标签进行追踪——让你全面了解 pr-agent 在各个仓库中的使用情况。

### 通过 LiteLLM 的 OpenTelemetry 集成发送 LLM 遥测 {#llm-telemetry-via-litellms-opentelemetry-integration}

要为 LLM 调用本身发出 OpenTelemetry 追踪和指标——以标准 `gen_ai.*` 语义约定名称记录美元费用、调用时长、首 token 时间，以及输入/输出 token 拆分——请启用 LiteLLM 内置的 `otel` 回调：

```toml
[litellm]
success_callback = ["otel"]
failure_callback = ["otel"]
turn_off_message_logging = true
```

> **请设置 `turn_off_message_logging = true`。** LiteLLM 会把完整的提示词和响应内容附加到回调所发出的内容上，在这里就是整个 PR diff。默认值为 `false`，以保留 Langfuse 和 LangSmith 用户的现有行为。

该集成通过环境变量配置：

```
OTEL_EXPORTER=otlp_http            # or "console", "otlp_grpc"
OTEL_EXPORTER_OTLP_ENDPOINT=https://collector:4318
OTEL_EXPORTER_OTLP_HEADERS=...
OTEL_SERVICE_NAME=pr-agent
LITELLM_OTEL_INTEGRATION_ENABLE_METRICS=true   # metrics are off by default
```

待处理的回调会在 CLI 和 GitHub Action 运行器退出之前刷新，时长受 `callback_timeout_seconds` 限制（参见[自定义回调](#custom-callbacks)）。

### 自定义回调 {#custom-callbacks}

如果把 PR-Agent 嵌入自己的代码，也可以以编程方式注册回调——例如一个记录每次调用的 token 用量和费用的 `litellm.CustomLogger`：

```python
import litellm
from pr_agent import cli

class UsageLogger(litellm.integrations.custom_logger.CustomLogger):
    async def async_log_success_event(self, kwargs, response_obj, start_time, end_time):
        record_usage(kwargs.get("model"), response_obj)

litellm.callbacks = [UsageLogger()]
cli.run_command("<pr_url>", "/review")
```

LiteLLM 会在补全调用已经返回之后异步分发这些回调。PR-Agent 会在 CLI（以及 GitHub Action 运行器）退出之前刷新任何待处理的回调，因此事件循环被拆除时它们不会丢失——无需额外配置。使用 `callback_timeout_seconds` 来限制这次刷新最多可以花多长时间：

```
[litellm]
callback_timeout_seconds = 30 # default
```

## 内置 OpenTelemetry 命令遥测

PR-Agent 可以发出自己的 [OpenTelemetry](https://opentelemetry.io/) 信号，用于跟踪利用率和采用情况。它们覆盖的是**命令**层——每个工具运行的频率、在哪个 Git 平台上、是否成功，以及消耗了多少 token——这些是任何 LLM 层级的集成都无法报告的，因为许多失败发生在任何模型调用之前：

- **追踪**：每个请求一个 span，名称为 `pr_agent <command>`（例如 `pr_agent review`），携带 `pr_agent.command`、`pr_agent.args_count`、`vcs.provider.name`、span 状态，以及失败时有界的 `error.type`。绝不会附加提示词和响应内容。
- **指标**：`pr_agent.commands` 是已执行命令的计数器，按命令和 Git 平台标注。`pr_agent.tokens` 统计消耗的 token，按命令、Git 平台、`pr_agent.fallback_used`（true 或 false）以及 `gen_ai.token.type`（`input`、`output`、`cache_read` 或 `cache_creation`）标注。`pr_agent.ai_calls` 统计成功的模型调用，按命令、Git 平台和 `pr_agent.fallback_used` 标注。零值会被跳过，因此不报告用量的提供商不会增加 token 时间序列（`pr_agent.ai_calls` 仍会计入它们的调用）。

### 两个独立层

命令遥测（本节）和 [LLM 遥测](#llm-telemetry-via-litellms-opentelemetry-integration) 是相互独立的开关，配置也彼此分开，因此可以只启用其中一个，并分别聚合。两者都开启时，LLM span 是同一条追踪中命令 span 的子 span，因此单个命令的模型调用仍然可以归因到该命令。

遥测默认关闭。要启用它，在 `configuration.toml` 中设置：

```toml
[otel]
is_enabled = true
exporter_type = "console" # "console", "otlp", "prometheus", or "none"
service_name = "pr-agent"
environment = "development" # e.g. "development", "staging", "production"
```

要把数据导出到 OpenTelemetry 收集器而不是控制台，请设置 `exporter_type = "otlp"`，并在 `.secrets.toml` 中配置端点和任何身份验证头（它们是密钥——不要放进 `configuration.toml`）：

```toml
[otel]
otlp_endpoint = "http://my-collector:4318"
otlp_headers = "x-honeycomb-team=YOUR_API_KEY" # optional, "key1=value1,key2=value2"
```

导出默认使用基于 HTTP 的 OTLP；`otlp_endpoint` 是基址 URL，`/v1/traces` 和 `/v1/metrics` 路径会自动追加。要改用基于 gRPC 的 OTLP，请安装可选导出器并选择协议——此时端点会按原样使用（gRPC 收集器通常监听 4317 端口）：

```bash
pip install pr-agent[otel-grpc]
```

```toml
[otel]
otlp_protocol = "grpc" # default: "http"
```

这是集群场景推荐的拓扑：让每个 PR-Agent 实例都指向同一个收集器，并在那里聚合。每个进程创建自己的导出器连接；使用 `service_name` 和 `environment` 资源属性在后端把各个实例区分开。

### 暴露原生 Prometheus 指标

如果不向收集器推送，可以设置 `exporter_type = "prometheus"`，在由 gunicorn 提供服务的应用（`github_app`、`gitlab_webhook`、`azuredevops_server_webhook`、`gitea_app`）上暴露原生的 `GET /metrics` 抓取端点。命令、token 和 AI 调用计数器会被转换成 Prometheus 文本格式，并且在抓取时合并每个 gunicorn worker 的值，因此计数器在各个进程 worker 之间仍然正确：

```toml
[otel]
exporter_type = "prometheus"
prometheus_multiproc_dir = "/tmp/pr-agent-prometheus" # shared, writable by every worker
```

1. 该导出器只包含指标：此模式下不会导出命令 span。
2. 只有选中该导出器时才会挂载 `/metrics`，因此默认不会暴露任何内容。它不依赖 OTLP 收集器或端点。
3. gunicorn 会自动注册和注销 worker 的状态文件（`when_ready`/`child_exit`）；在抓取过程中死亡的 worker 只会留下一个过期文件，一旦被标记为死亡就会被忽略。
4. 指标族由第一个数据点的标签集创建。之后不符合该族的属性会被丢弃，缺失的属性会用空字符串回填，因此标签基数漂移不会导致抓取中断。
5. 该导出器随 PR-Agent 一起提供（它依赖 `prometheus-client`）；不需要额外的包。像抓取任何导出器一样抓取它：

```yaml
scrape_configs:
  - job_name: pr-agent
    static_configs:
      - targets: ["pr-agent:3000"]
```

隐私控制（默认都关闭）：

- `include_pr_url = true` 会把 PR URL 附加到 span。默认关闭，因为 URL 会暴露私有仓库名。
- `include_error_details = true` 会把异常消息和被拒绝的命令文本附加到错误 span。默认关闭，因为这些内容可能嵌入 PR URL、仓库名或其他特定于请求的文本。有界值（异常类名和错误类别）始终会被附加。

说明：

- 遥测配置是**进程级**的：它在启动时从全局配置或环境中读取一次，不能通过 `.pr_agent.toml` 按仓库启用或重新配置。在多租户服务器中，遥测是共享的进程资源——请在部署该进程的地方配置它。
- PR-Agent 保持自己的 OpenTelemetry provider，并且从不注册进程全局的那一个，因此把 PR-Agent 嵌入已经使用 OpenTelemetry 的应用不会干扰宿主的遥测。待处理的 span 和指标会在进程退出时自动刷新。
- 每次 OTLP 导出调用都受 `otlp_timeout` 限制（默认 3 秒，含重试），因此无法访问的收集器不能挂起 CLI 退出或请求完成。对于较慢的收集器可以提高它，代价是最坏情况下停顿更长。
- 如果设置了 `exporter_type = "otlp"` 但没有配置端点，遥测会完全禁用（失败时关闭）——它绝不会回退到另一个导出器，因此缺失的密钥不会把遥测重定向到进程日志。
- 当 `exporter_type = "prometheus"` 时，`prometheus_multiproc_dir` 必须是每个 worker 都可写的共享目录；它默认为 `/tmp/pr-agent-prometheus`。在非 gunicorn（单进程）部署中，导出器不需要它，只会提供该进程自己的注册表。
- **无服务器部署**（例如 AWS Lambda webhook）受支持：缓冲的 span 和指标会在每个已处理请求结束时强制刷新，因为被冻结的执行环境会停止后台导出线程，并且在被回收时不会运行退出处理程序。不需要额外配置。

## 为 PR-Agent 引入每个仓库的上下文文件 {#bringing-per-repo-context-files-to-pr-agent}

`支持的平台：GitHub、GitLab、Gitea、Bitbucket、Azure DevOps、Local`

要给 PR-Agent 的工具提供额外的项目上下文，可以让它把仓库说明文件——例如 [AGENTS.md](https://agents.md/) 或 [CLAUDE.md](https://www.anthropic.com/engineering/claude-code-best-practices)——包含进 `/review`、`/describe` 和 `/improve` 工具的提示词。

默认情况下，PR-Agent 会在仓库根目录查找 `AGENTS.md` 文件：

```toml
[config]
repo_context_files = ["AGENTS.md"]
```

你可以列出任意相对仓库的路径。默认从仓库的**默认分支**读取这些文件，因此只会使用已合并的可信内容，PR 无法影响用来审查它的指引。缺失的文件会被静默跳过。把该选项设为空列表即可完全禁用此功能：

```toml
[config]
repo_context_files = ["AGENTS.md", "CLAUDE.md", "docs/conventions.md"]
```

:::note[从哪个分支读取这些文件]
默认情况下（`repo_context_from_default_branch = true`），说明文件从仓库的**默认分支**读取——单一可信来源——因此 PR 及其目标分支都不能改变用来审查它的指引。这与 Qodo Merge 读取这些文件的方式一致。

将 `repo_context_from_default_branch = false` 可改为从 PR 的**目标（基）分支**读取。这会尊重特定于分支的说明（例如发布分支，或自带 `AGENTS.md` 的堆叠 PR），代价是信任能够写入该目标分支的人。即便如此，也绝不会从 PR 自己的 head 读取文件。

本地 Git 平台没有单独的默认分支，因此它始终从已提交的目标分支（作为 `--pr_url` 传入的分支）读取说明文件，而绝不会从 `HEAD` 或未提交的变更读取。

```toml
[config]
repo_context_from_default_branch = false
```
:::

为了限制发送给模型的这部分上下文的数量，`repo_context_max_lines`（默认 `500`）会限制渲染行的总数，包括包裹标签。超出预算的内容会被安全截断：

```toml
[config]
repo_context_max_lines = 500
```

### 来自同级仓库的上下文 {#context-from-sibling-repositories}

主机操作者必须首先在部署配置中批准仓库：

```toml
[config]
repo_context_sibling_repos = ["my-group/library"]
repo_context_max_sibling_files = 5
```

只批准那些内容可以出现在消费方仓库审查中的仓库。
此允许列表和获取上限不能由仓库设置或评论参数更改。
空的允许列表会禁用同级读取。

消费方仓库随后可以在其 `.pr_agent.toml` 中，以结构化的 `repo_context_files` 条目选择文件：

```toml
[config]
repo_context_files = [
    "AGENTS.md",
    {repo_id = "my-group/library", file_path = "src/api.py"},
]
```

在 GitHub 上使用 `owner/repository`，在 GitLab 上使用完整项目路径。GitLab 也接受字符串形式的数字项目 ID，前提是同一标识符位于主机允许列表中。解析后的仓库必须与当前仓库共享所属命名空间：GitHub 所有者或 GitLab 顶级群组，包括位于不同子群组中的项目。重命名或重定向后的路径必须在两处设置中更新为其规范名称。

同级文件始终来自它们的默认分支，并与本地文件共享 `repo_context_max_lines`。私有和内部仓库还要求请求者有访问权限。评论参数完全不能覆盖 `repo_context_files`；仓库的 `.pr_agent.toml` 仍然可以设置它。

## 忽略 PR 中的自动命令 {#ignoring-automatic-commands-in-prs}

PR-Agent 允许你根据多种条件自动忽略某些 PR：

- 具有特定标题的 PR（使用正则匹配）
- 特定分支之间的 PR（使用正则匹配）
- 来自特定仓库的 PR（使用正则匹配）
- 并非来自特定文件夹的 PR
- 包含特定标签的 PR
- 由特定用户打开的 PR

标题、作者、标签、仓库、源分支和目标分支的 `ignore_*` 规则也适用于 `/review` 和 `/ask` 等评论命令，以及 CLI 的 `--pr_url` 运行。在这些路径中，`ignore_pr_authors` 匹配的是 **PR 作者**，而不是发布命令的人。被忽略的 CLI 请求会成功退出，且不运行工具。纯 diff 的 CLI 输入（`--diff-file` 和 `--stdin`）没有 PR 元数据，不受这些规则排除。

### 忽略特定标题的 PR

要忽略标题类似 "[Bump]: ..." 的 PR，可以在 `configuration.toml` 文件中添加以下内容：

```toml
[config]
ignore_pr_title = ["\\[Bump\\]"]
```

其中 `ignore_pr_title` 是用于匹配希望忽略的 PR 标题的正则模式列表。默认值是 `ignore_pr_title = ["^\\[Auto\\]", "^Auto"]`。

默认的 `^Auto` 模式也会匹配 "Autoscaling fix" 这样的普通标题。因为标题规则现在也适用于手动命令，这类 PR 上的 `/review`、`/ask` 以及 CLI `--pr_url` 命令会被跳过。如果不希望如此，请在配置中设置更窄的 `ignore_pr_title` 模式，或使用 `ignore_pr_title = []`。被跳过的请求会被记录日志，且不会运行工具或发布命令反应。

### 忽略特定分支之间的 PR

要忽略来自特定源分支或目标分支的 PR，可以在 `configuration.toml` 文件中添加以下内容：

```toml
[config]
ignore_pr_source_branches = ['develop', 'main', 'master', 'stage']
ignore_pr_target_branches = ["qa"]
```

其中 `ignore_pr_source_branches` 和 `ignore_pr_target_branches` 是用于匹配希望忽略的源分支和目标分支的正则模式列表。
它们并不互斥，可以一起使用，也可以分开使用。

### 忽略来自特定仓库的 PR

要忽略来自特定仓库的 PR，可以在 `configuration.toml` 文件中添加以下内容：

```toml
[config]
ignore_repositories = ["my-org/my-repo1", "my-org/my-repo2"]
```

其中 `ignore_repositories` 是用于匹配希望忽略的仓库的正则模式列表。当你有多个仓库并希望把其中某些排除在分析之外时，这很有用。


### 忽略并非来自特定文件夹的 PR

要只允许特定文件夹（大型单体仓库中经常需要），请设置：

```
[config]
allow_only_specific_folders=['folder1','folder2']
```

对于上述配置，只有当 PR 变更包含文件路径中带有 'folder1' 或 'folder2' 的文件时，才会触发自动反馈

### 忽略包含特定标签的 PR

要忽略包含特定标签的 PR，可以在 `configuration.toml` 文件中添加以下内容：

```
[config]
ignore_pr_labels = ["do-not-merge"]
```

其中 `ignore_pr_labels` 是一组标签；当 PR 中存在这些标签时，该 PR 会被忽略。

### 忽略来自特定用户的 PR

PR-Agent 会尝试自动识别并忽略由机器人创建的拉取请求，方式包括：

- GitHub 原生的机器人检测系统
- 基于名称的模式匹配

虽然这种检测相当可靠，但可能无法覆盖所有情况，尤其是当：

- 机器人注册为普通用户账号
- 机器人名称不符合常见模式

为了补充自动机器人检测，你可以手动指定要忽略的用户。在 `configuration.toml` 文件中添加以下内容，以忽略来自特定用户的 PR：

```
[config]
ignore_pr_authors = ["my-special-bot-user", ...]
```

其中 `ignore_pr_authors` 是希望忽略的用户名正则列表。

:::note
有一种特定情况，机器人会收到自动响应——当它们生成的 PR 带有_失败的测试_时。
:::

### 按语言/框架忽略生成文件

要自动排除由特定语言或框架生成的文件，可以在 `configuration.toml` 文件中添加以下内容：

```
[config]
ignore_language_framework = ['protobuf', ...]
```

可以在 [`generated_code_ignore.toml`](https://github.com/the-pr-agent/pr-agent/blob/main/pr_agent/settings/generated_code_ignore.toml) 中查看自动生成文件的模式列表。
匹配这些 glob 模式的文件会自动从 PR Agent 分析中排除。

### 受限模式 {#restricted-mode}

在 GitHub/GitLab 权限有限的情况下运行 PR-Agent 时，将 `restricted_mode` 设为 `true`，以便优雅地跳过需要更高访问权限的操作（例如推送更新日志变更）：

```toml
[config]
restricted_mode = true
```

在受限模式下，最低工作流权限为：

```yaml
permissions:
  issues: write
  pull-requests: write
```

在显式的 `permissions:` 块中，任何未列出的范围（例如 `contents`）都会被设为 `none`，因此你不需要授予 `contents`——受限模式会跳过所有需要 `contents: write` 的操作。所有工具（`/review`、`/describe`、`/improve` 等）只需 `pull-requests: write` 即可继续正常工作。

> **注意：** 只有在存在 `permissions:` 块时（如上所示）这一点才成立。如果完全省略 `permissions:` 块，实际默认值由仓库/组织的 GitHub Actions 设置决定，可能会授予更宽的访问权限。
