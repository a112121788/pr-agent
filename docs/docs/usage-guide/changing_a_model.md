---
title: "Changing a Model"
sidebar_position: 8
---

## Changing a model in PR-Agent {#changing-a-model-in-pr-agent}

The default model is `gpt-6.1-sol`. The fallback list is `glm-5.3`. Both are set in [`configuration.toml`](https://github.com/the-pr-agent/pr-agent/blob/main/pr_agent/settings/configuration.toml):

```toml
[config]
model = "gpt-6.1-sol"
fallback_models = ["glm-5.3"]
```

Change those two fields to select another model. The model call uses an OpenAI-compatible endpoint. On the host that runs the CLI or the `gitee_app` webhook, set:

```bash
OPENAI__KEY=<your_openai_api_key>
OPENAI__API_BASE=<your_openai_api_base>
```

The same values can live in `.secrets.toml` on the host:

```toml
[openai]
key = "sk-..."
api_base = "https://api.openai.com/v1"
```

`openai.api_base` and `openai.key` are host-controlled. A repository `.pr_agent.toml` or a pull-request comment cannot set them. See [Configuration file](./configuration_options.md#local-configuration-file).

Names that LiteLLM does not know need `config.custom_model_max_tokens` set to the context window, or `get_max_tokens()` fails. Registered names and their windows are in [`pr_agent/algo/__init__.py`](https://github.com/the-pr-agent/pr-agent/blob/main/pr_agent/algo/__init__.py).

To see which model answered a given pull request, enable `config.output_run_details`. See [Showing the agent run details](./additional_configurations.md#showing-the-agent-run-details).

:::note[Provider environment]
LiteLLM's own environment variables still apply for a given model id. If the keys for that id are missing, LiteLLM usually fails to identify the model. Keep process environment and LiteLLM globals stable while requests run. Prefer `OPENAI__API_BASE` over a process-wide `litellm.api_base`.
:::

### GPT-6.1 Sol

`gpt-6.1-sol` is the default. Its context window is 1,050,000 tokens, with a 922,000-token input ceiling and up to 128,000 output tokens. PR-Agent also applies `config.max_model_tokens` unless a tool bypasses that cap.

```toml
[config]
model = "gpt-6.1-sol"
reasoning_effort = "medium" # "low", "medium", "high", "xhigh", "max"
```

The model page lists `low`, `medium` (the default), `high`, `xhigh`, and `max`. `none` is not supported, so PR-Agent clamps a configured `none` to `low`. `minimal` is mapped to `low`, and `max` is mapped to `xhigh` on Azure and OpenRouter routes. On the OpenAI route, temperature is omitted.

This build does not add a separate Azure OpenAI, GitHub Actions, or other-host setup. Point `OPENAI__API_BASE` at the OpenAI-compatible base URL you use, including a gateway that serves `gpt-6.1-sol`.

### Azure {#azure}

This version has no Azure DevOps integration and no Azure OpenAI setup steps. Do not set `config.git_provider` to `azure`. For the model endpoint, set `OPENAI__KEY` and `OPENAI__API_BASE` as shown above. The default model remains `gpt-6.1-sol`, with fallback `glm-5.3`.

### GLM fallback

If the primary model fails, PR-Agent tries each entry in `fallback_models`. The shipped fallback is `glm-5.3`. Keep that id, or replace the list, in the host configuration. The fallback uses the same `OPENAI__KEY` and `OPENAI__API_BASE` when it is called through the OpenAI-compatible route. A provider-specific id needs the environment variables LiteLLM documents for that provider.

## Output token limit

```toml
[config]
max_output_tokens = 0 # 0 = unset (default)
```

Unset, PR-Agent does not send an output limit, and the provider default applies. Some providers cap reasoning models low enough that the visible answer comes back empty. Set `config.max_output_tokens` to a positive value the model supports (for example `16000`). Values below 4096 are raised to 4096. Non-numeric or negative values are ignored. Both cases log a warning.

`gpt-6.1-sol` supports at most 128,000 output tokens, including reasoning tokens. PR-Agent does not clamp this setting to that ceiling. For models with a small window, size `config.max_model_tokens` so the prompt leaves room for the output limit.

## Routing small pull requests to a cheaper model {#routing-small-pull-requests-to-a-cheaper-model}

With routing enabled, a pull request under a size limit uses a cheaper primary model. `config.fallback_models` still applies if that model fails:

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

Rules are checked in order. The first rule whose limits the pull request fits selects the primary model. A pull request that fits no rule uses `config.model`. Size is the number of diff hunks (`max_hunks`) and changed files (`max_files`) left after the `[ignore]` rules.

Routing applies to calls that ask for the regular model: `/review`, `/improve`, `/generate_labels`, and `/add_docs`. Tools that already use `config.model_weak` (`/describe`, `/ask`, `/update_changelog`) are left alone. With `config.output_run_details` enabled, the run details show which model was used.
