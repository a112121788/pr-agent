---
title: "扩展 PR-Agent"
sidebar_position: 9
---

本页面向要扩展模型、Gitee 提供商或工具的贡献者。如果只更换模型，请使用[更换模型](./changing_a_model.md)。正在运行的产品只支持 Gitee：`config.git_provider` 为 `gitee`，Webhook 目标为 `gitee_app`。

## 添加模型 {#adding-a-model}

工具调用经过 LiteLLM（`pr_agent/algo/ai_handlers/litellm_ai_handler.py`）。大多数模型只需要配置：

```toml
[config]
model = "<model-name>"
fallback_models = ["<fallback-model-name>"]
```

在 `pr_agent/settings/configuration.toml` 的 `[config]` 中设置。模型名称放在配置里，不要写进工具代码。随构建提供的默认值是 `gpt-6.1-sol`，备用模型是 `glm-5.3`。OpenAI 兼容路由的主机必须设置 `OPENAI__KEY` 和 `OPENAI__API_BASE`。

行为不同的模型登记在 `pr_agent/algo/__init__.py`。上下文窗口位于其中的 `MAX_TOKENS`。没有条目时请设置 `config.custom_model_max_tokens`，否则 `get_max_tokens()` 会抛出异常。

是否支持 temperature 在运行时通过探测 `litellm.get_supported_openai_params()` 决定（`pr_agent/algo/ai_handlers/litellm_ai_handler.py` 中的 `_litellm_supports_temperature`）。绝不能接收 temperature 的模型列在 `config.no_temperature_models` 中。

用 `PYTHONPATH=. uv run pytest tests/unittest` 验证。

## 添加 Git 提供商 {#adding-a-git-provider}

本发行版交付并文档化的是 Gitee。`pr_agent/git_providers/gitee_provider.py` 中的 `GiteeProvider` 是参考实现。它报告除 `push_code` 以外的全部能力，因此 `/update_changelog` 发表评论，而不是提交。

若要在分叉中增加另一个提供商：

1. 创建 `pr_agent/git_providers/<name>_provider.py`，扩展 `pr_agent/git_providers/git_provider.py` 中的 `GitProvider`。
2. 在 `pr_agent/git_providers/__init__.py` 的 `_BUILTIN_GIT_PROVIDERS` 里，以内置项 `(module_path, class_name)` 登记。内置项在被选中时才懒加载。本构建运行的 ID 是 `gitee`。
3. 在 `[config]` 中用 `git_provider="<name>"` 选中它。本仓库的 Webhook 和文档假定值为 `gitee`。
4. 增加安装页，并在 `docs/sidebars.js` 的 Installation 下登记。当前页面是 [`gitee.md`](../installation/gitee.md)。
5. 用 `provider.is_supported("feature")` 选择行为，不要做具体类型判断。
6. 在 `tests/unittest/test_<name>_provider.py` 增加单元测试。模式见 `tests/unittest/test_gitee_provider.py` 和 `tests/unittest/test_gitee_webhook.py`。在 `pr_agent/settings/.secrets_template.toml` 中列出所需环境变量。

### 从其他包注册提供商 {#registering-a-provider-from-another-package}

提供商不必放在本仓库里。在 PR-Agent 解析提供商之前调用 `register_git_provider`：

```python
from pr_agent.git_providers import register_git_provider

from my_package.forge_provider import ForgeProvider

register_git_provider("forge", ForgeProvider)
```

然后在 `[config]` 中设置 `git_provider="forge"`。该类必须扩展 `GitProvider`。用同一个类注册两次是空操作。在已被占用的 ID 下注册另一个类会抛出异常，因此其他包不能静默替换内置的 `gitee` 提供商。

这里交付的 Webhook 仍然是 `gitee_app` 目标上的 `POST /api/v1/gitee_webhooks`。第三方提供商需要自己的服务入口。

## 添加工具 {#adding-a-tool}

1. 在 `pr_agent/tools/pr_<name>.py` 中实现工具，入口为 `async def run(self)`（模式见 `pr_reviewer.py`）。
2. 在 `pr_agent/settings/configuration.toml` 中增加 `[pr_<tool>]` 节，放入工具要读取的键（模式见 `[pr_reviewer]`）。
3. 在 `pr_agent/settings/` 下增加提示词 TOML，并把它登记到 `pr_agent/config_loader.py` 的 `settings_files=[...]`。未登记的文件不会被加载。
4. TOML 节名必须与工具读取的设置键一致：`pr_reviewer_prompts.toml` 中的 `[pr_review_prompt]` 对应 `pr_reviewer.py` 里的 `get_settings().pr_review_prompt`。
5. 在 `pr_agent/agent/pr_agent.py` 的 `command2class` 中登记工具。然后把它加到帮助界面，否则 `/help` 不会显示：`pr_agent/tools/pr_help_message.py`、`pr_agent/servers/help.py`，以及 `pr_agent/cli.py` 中的命令列表。
6. 在 `docs/docs/tools/index.md` 增加一行，增加页面 `docs/docs/tools/<name>.md`（见 [`review.md`](../tools/review.md)），并在 `docs/sidebars.js` 的 Tools 下登记。
7. 在 `tests/unittest/` 下增加测试，并用 `PYTHONPATH=. uv run pytest tests/unittest` 验证。

会推送提交的工具必须检查 `provider.is_supported("push_code")`。在 Gitee 上该检查为假，工具应改为发表评论。
