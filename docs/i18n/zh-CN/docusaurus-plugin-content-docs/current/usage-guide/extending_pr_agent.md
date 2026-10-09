---
title: "扩展 PR-Agent"
sidebar_position: 9
---

扩展模型、Git 提供商或工具的贡献者从这里开始。如果只更换
模型，请使用[更换模型](./changing_a_model.md)。

## 添加模型 {#adding-a-model}

工具调用经过 LiteLLM（`pr_agent/algo/ai_handlers/litellm_ai_handler.py`），这是默认处理器。大多数模型只需要配置：

```toml
[config]
model="<model-name>"
fallback_models=["<fallback-model-name>"]
```

在 `pr_agent/settings/configuration.toml` 的 `[config]` 下设置这些项。
把模型名放在配置中，不要放在工具代码里。

行为不同的模型在 `pr_agent/algo/__init__.py` 中注册：
`CLAUDE_EXTENDED_THINKING_MODELS` 用于接受扩展思考的 Claude 模型。对于带提供商前缀别名的 Claude 模型
（裸名称、`anthropic/`、`vertex_ai/`、`bedrock/`），在 `_CLAUDE_MODEL_FAMILIES` 中声明规范的模型族，
以便自动展开到各个注册表。
其他模型可以直接加入对应的列表。

温度支持在运行时通过探测每个模型的
`litellm.get_supported_openai_params()` 决定（见
`pr_agent/algo/ai_handlers/litellm_ai_handler.py` 中的 `_litellm_supports_temperature`）。
绝不能接收 temperature 参数的模型列在
`configuration.toml` 的 `config.no_temperature_models` 中；自适应思考的 Claude
模型（Opus 4.7/4.8 以及 Opus/Sonnet/Fable 5）从不接收该参数。

上下文窗口在 `pr_agent/algo/__init__.py` 的 `MAX_TOKENS` 中注册：
在 `_CLAUDE_MODEL_FAMILIES` 中声明的 Claude 模型族会自动填充其
别名。对于其他模型，把模型名及其
上下文窗口的令牌数加入 `MAX_TOKENS`，或在 `configuration.toml` 中设置 `config.custom_model_max_tokens`。
两者都没有时，`get_max_tokens()` 会抛出异常。

用 `PYTHONPATH=. uv run pytest tests/unittest` 验证。

## 添加 Git 提供商 {#adding-a-git-provider}

实现 `GitProvider` 子类并注册它：

1. 创建 `pr_agent/git_providers/<name>_provider.py`，扩展 `pr_agent/git_providers/git_provider.py` 中的接口（参考实现是 `gitlab_provider.py`）。
2. 把内置提供商以 `(module_path, class_name)` 对加入 `pr_agent/git_providers/__init__.py` 的 `_BUILTIN_GIT_PROVIDERS`。内置提供商在被选中时延迟导入。已使用的键：`github`、`gitlab`、`bitbucket`、`bitbucket_server`、`azure`、`codecommit`、`local`、`gerrit`、`gitea`、`plain-diff`。
3. 在 `pr_agent/settings/configuration.toml` 中通过 `[config]` → `git_provider="<name>"` 选择它。
4. 添加 `docs/docs/installation/<name>.md`（参见 [`gitlab.md`](../installation/gitlab.md)），并在 `docs/sidebars.js` 的 `Installation` 下注册。
5. 用 `provider.is_supported("feature")` 这类能力检查来选择依赖提供商的行为，而不是检查提供商类型。
6. 在 `tests/unittest/test_<name>_provider.py` 下添加单元测试（参见 `test_bitbucket_provider.py`），并在 `pr_agent/settings/.secrets_template.toml` 中列出所需的环境变量。

### 从其他包注册提供商 {#registering-a-provider-from-another-package}

提供商不必位于本仓库。在 PR-Agent 解析提供商之前，从你自己的包调用 `register_git_provider`，例如从启动服务器或封装 CLI 的模块中：

```python
from pr_agent.git_providers import register_git_provider

from my_package.forge_provider import ForgeProvider

register_git_provider("forge", ForgeProvider)
```

然后在 `[config]` 下用 `git_provider="forge"` 选择它。该类必须扩展 `GitProvider`。把同一个类注册两次是空操作；在已被占用的 id 下注册不同的类会抛出异常，因此包不能悄悄替换内置提供商。

## 添加工具 {#adding-a-tool}

1. 在 `pr_agent/tools/pr_<name>.py` 中实现工具类，入口为 `async def run(self)`（参见 `pr_reviewer.py`）。
2. 在 `pr_agent/settings/configuration.toml` 中添加 `[pr_<tool>]` 节，放入该工具读取的选项键（参照 `[pr_reviewer]`）。
3. 在 `pr_agent/settings/` 下添加提示词 TOML，并把它登记到 `pr_agent/config_loader.py` 的 `settings_files=[...]` 列表中——否则不会加载。
4. 让 TOML 节名与工具读取的设置键一致：`pr_reviewer_prompts.toml` 中的 `[pr_review_prompt]` ↔ `pr_reviewer.py` 中的 `get_settings().pr_review_prompt`。
5. 在 `pr_agent/agent/pr_agent.py` 的 `command2class` 中以命令名注册该工具，例如 `"my_tool": PRMyTool`。然后把它加入写死的帮助界面，否则不会出现在 `/help` 中：`pr_agent/tools/pr_help_message.py`、`pr_agent/servers/help.py`，以及 `pr_agent/cli.py` 中的命令列表。
6. 在 `docs/docs/tools/index.md` 的工具列表中加一行，添加页面 `docs/docs/tools/<name>.md`（参见 [`review.md`](../tools/review.md)），并在 `docs/sidebars.js` 的 `Tools` 下注册该页面。
7. 在 `tests/unittest/` 下添加测试，并用 `PYTHONPATH=. uv run pytest tests/unittest` 验证。
