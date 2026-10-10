---
title: "更换模型"
sidebar_position: 8
---

## 在 PR-Agent 中更换模型 {#changing-a-model-in-pr-agent}

默认模型是 `glm-5.3`。备用列表是 `gpt-6.1-sol`。两者都写在 [`configuration.toml`](https://github.com/the-pr-agent/pr-agent/blob/main/pr_agent/settings/configuration.toml) 中：

```toml
[config]
model = "glm-5.3"
fallback_models = ["gpt-6.1-sol"]
```

修改这两个字段即可更换模型。模型调用使用 OpenAI 兼容端点。在运行 CLI 或 `gitee_app` Webhook 的主机上设置：

```bash
OPENAI__KEY=<your_openai_api_key>
OPENAI__API_BASE=<your_openai_api_base>
```

同样的值也可以写在主机上的 `.secrets.toml` 里：

```toml
[openai]
key = "sk-..."
api_base = "https://api.openai.com/v1"
```

`openai.api_base` 和 `openai.key` 由主机控制。仓库的 `.pr_agent.toml` 或拉取请求评论不能设置它们。见[配置文件](./configuration_options.md#local-configuration-file)。

LiteLLM 不认识的名称需要把 `config.custom_model_max_tokens` 设为上下文窗口，否则 `get_max_tokens()` 会失败。已注册的名称和窗口见 [`pr_agent/algo/__init__.py`](https://github.com/the-pr-agent/pr-agent/blob/main/pr_agent/algo/__init__.py)。

要查看某次拉取请求实际由哪个模型回答，请启用 `config.output_run_details`。见[显示代理运行详情](./additional_configurations.md#showing-the-agent-run-details)。

:::note[提供商环境变量]
某个模型 ID 仍然需要 LiteLLM 自己的环境变量。缺少这些键时，LiteLLM 通常无法识别该模型。请求进行期间，请保持进程环境变量和 LiteLLM 全局值稳定。请使用 `OPENAI__API_BASE`，不要使用进程级的 `litellm.api_base`。
:::

### GPT-6.1 Sol

`gpt-6.1-sol` 是备用模型。它的上下文窗口为 1,050,000 token，输入上限为 922,000 token，输出最多 128,000 token。除非某个工具绕过该上限，PR-Agent 还会应用 `config.max_model_tokens`。

```toml
[config]
model = "gpt-6.1-sol"
reasoning_effort = "medium" # "low"、"medium"、"high"、"xhigh"、"max"
```

该模型页面列出的是 `low`、`medium`（默认）、`high`、`xhigh` 和 `max`。不支持 `none`，因此 PR-Agent 会把配置的 `none` 钳制为 `low`。`minimal` 会映射为 `low`。在 Azure 和 OpenRouter 路由上，`max` 会映射为 `xhigh`。在 OpenAI 路由上会省略 temperature。

本构建不另附 Azure OpenAI、GitHub Actions 或其他托管平台的安装步骤。把 `OPENAI__API_BASE` 指向你使用的 OpenAI 兼容基址，包括提供 `gpt-6.1-sol` 的网关。

### Azure {#azure}

本版本没有 Azure DevOps 集成，也没有 Azure OpenAI 的操作步骤。不要把 `config.git_provider` 设为 `azure`。模型端点请按上文设置 `OPENAI__KEY` 和 `OPENAI__API_BASE`。默认模型是 `glm-5.3`，备用模型是 `gpt-6.1-sol`。

### GLM 默认模型

默认模型是 `glm-5.3`，上下文窗口为 1,000,000 token。主模型失败时，PR-Agent 会依次尝试 `fallback_models`。随构建提供的备用模型是 `gpt-6.1-sol`。在主机配置里保留该 ID，或替换整个列表。备用模型走 OpenAI 兼容路由时，使用同一组 `OPENAI__KEY` 和 `OPENAI__API_BASE`。特定提供商的模型 ID 需要 LiteLLM 为该提供商记录的环境变量。

## 输出 token 限制

```toml
[config]
max_output_tokens = 0 # 0 = 不设置（默认）
```

未设置时，PR-Agent 不发送输出上限，由提供商自己的默认值决定。有些提供商把推理模型的上限设得很低，可见回答会变成空的。把 `config.max_output_tokens` 设为该模型支持的正数（例如 `16000`）。低于 4096 的值会被抬到 4096。非数字或负数会被忽略。这两种情况都会记录警告。

`gpt-6.1-sol` 最多支持 128,000 个输出 token，其中包含推理 token。PR-Agent 不会把该设置钳制到这个上限。对于窗口较小的模型，请调整 `config.max_model_tokens`，让提示词为输出上限留出空间。

## 将小型拉取请求路由到更便宜的模型 {#routing-small-pull-requests-to-a-cheaper-model}

启用路由后，低于大小限制的拉取请求会使用更便宜的主模型。如果该模型失败，`config.fallback_models` 仍然生效：

```toml
[model_routing]
enable = true

[[model_routing.rules]]
max_hunks = 3
model = "glm-5.3"

[[model_routing.rules]]
max_hunks = 15
max_files = 6
model = "gpt-6.1-sol"
```

规则按顺序检查。第一个限制能容纳该拉取请求的规则会选定主模型。没有任何规则匹配时使用 `config.model`。大小是应用 `[ignore]` 规则之后剩余的 diff hunk 数（`max_hunks`）和变更文件数（`max_files`）。

路由只作用于请求常规模型的调用：`/review`、`/improve`、`/generate_labels` 和 `/add_docs`。已经使用 `config.model_weak` 的工具（`/describe`、`/ask`、`/update_changelog`）不受影响。启用 `config.output_run_details` 后，运行详情会显示实际使用的模型。
