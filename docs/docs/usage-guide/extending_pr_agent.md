---
title: "Extending PR-Agent"
sidebar_position: 9
---

This page is for contributors who extend a model, the Gitee provider, or a tool. To only change the model, use [Changing a model](./changing_a_model.md). The running product is Gitee-only: `config.git_provider` is `gitee`, and the webhook target is `gitee_app`.

## Adding a model {#adding-a-model}

Tool calls go through LiteLLM (`pr_agent/algo/ai_handlers/litellm_ai_handler.py`). Most models need only configuration:

```toml
[config]
model = "<model-name>"
fallback_models = ["<fallback-model-name>"]
```

Set these under `[config]` in `pr_agent/settings/configuration.toml`. Keep model names in configuration, not in tool code. The shipped defaults are `gpt-6.1-sol` and fallback `glm-5.3`. The host must set `OPENAI__KEY` and `OPENAI__API_BASE` for the OpenAI-compatible route.

Models that behave differently are registered in `pr_agent/algo/__init__.py`. Context windows live in `MAX_TOKENS` there. Without an entry, set `config.custom_model_max_tokens`, or `get_max_tokens()` raises.

Temperature support is decided at runtime by probing `litellm.get_supported_openai_params()` (`_litellm_supports_temperature` in `pr_agent/algo/ai_handlers/litellm_ai_handler.py`). Models that must never receive temperature are listed in `config.no_temperature_models`.

Verify with `PYTHONPATH=. uv run pytest tests/unittest`.

## Adding a git provider {#adding-a-git-provider}

This distribution ships and documents Gitee. `GiteeProvider` in `pr_agent/git_providers/gitee_provider.py` is the reference implementation. It reports every capability except `push_code`, so `/update_changelog` publishes a comment instead of committing.

To add another provider in a fork:

1. Create `pr_agent/git_providers/<name>_provider.py`, extending `GitProvider` in `pr_agent/git_providers/git_provider.py`.
2. Add the built-in to `_BUILTIN_GIT_PROVIDERS` in `pr_agent/git_providers/__init__.py` as a `(module_path, class_name)` pair. Built-ins import lazily when selected. `gitee` is the id this build runs.
3. Select it with `git_provider="<name>"` under `[config]`. The webhook and docs in this tree assume `gitee`.
4. Add an installation page and register it under Installation in `docs/sidebars.js`. The current page is [`gitee.md`](../installation/gitee.md).
5. Choose behavior with `provider.is_supported("feature")`, not with a concrete type check.
6. Add unit tests under `tests/unittest/test_<name>_provider.py`. `tests/unittest/test_gitee_provider.py` and `tests/unittest/test_gitee_webhook.py` are the patterns. List required environment variables in `pr_agent/settings/.secrets_template.toml`.

### Registering a provider from another package {#registering-a-provider-from-another-package}

A provider does not have to live in this repository. Call `register_git_provider` before PR-Agent resolves the provider:

```python
from pr_agent.git_providers import register_git_provider

from my_package.forge_provider import ForgeProvider

register_git_provider("forge", ForgeProvider)
```

Then set `git_provider="forge"` under `[config]`. The class must extend `GitProvider`. Registering the same class twice is a no-op. Registering a different class under an id that is already taken raises, so a package cannot replace the built-in `gitee` provider silently.

The webhook that ships here is still `POST /api/v1/gitee_webhooks` on the `gitee_app` target. A third-party provider needs its own server entrypoint.

## Adding a tool {#adding-a-tool}

1. Implement the tool in `pr_agent/tools/pr_<name>.py` with an `async def run(self)` entry point (`pr_reviewer.py` is the pattern).
2. Add a `[pr_<tool>]` section in `pr_agent/settings/configuration.toml` for the keys the tool reads (`[pr_reviewer]` is the pattern).
3. Add a prompt TOML under `pr_agent/settings/` and register it in `settings_files=[...]` in `pr_agent/config_loader.py`. Unregistered files are not loaded.
4. Match the TOML section name to the settings key the tool reads: `[pr_review_prompt]` in `pr_reviewer_prompts.toml` matches `get_settings().pr_review_prompt` in `pr_reviewer.py`.
5. Register the tool in `command2class` in `pr_agent/agent/pr_agent.py`. Then add it to the help surfaces or it will not show up in `/help`: `pr_agent/tools/pr_help_message.py`, `pr_agent/servers/help.py`, and the command list in `pr_agent/cli.py`.
6. Add a row in `docs/docs/tools/index.md`, a page `docs/docs/tools/<name>.md` (see [`review.md`](../tools/review.md)), and register the page under Tools in `docs/sidebars.js`.
7. Add tests under `tests/unittest/` and verify with `PYTHONPATH=. uv run pytest tests/unittest`.

A tool that pushes commits must check `provider.is_supported("push_code")`. On Gitee that check is false, and the tool should publish a comment instead.
