---
title: "用法与自动化"
sidebar_position: 5
---

## 本地仓库（CLI） {#local-repo-cli}

从本地克隆的 PR-Agent 仓库（CLI）运行时，会使用你的本地配置文件。
通过 CLI 调用不同工具的示例：

- **审查**：       `python -m pr_agent.cli --pr_url=<pr_url>  review`
- **描述**：     `python -m pr_agent.cli --pr_url=<pr_url>  describe`
- **改进**：      `python -m pr_agent.cli --pr_url=<pr_url>  improve`
- **提问**：          `python -m pr_agent.cli --pr_url=<pr_url>  ask "Write me a poem about this PR"`
- **更新变更日志**：      `python -m pr_agent.cli --pr_url=<pr_url>  update_changelog`

上面的命令假定 `pr_agent` 包可以被导入——请使用 `uv sync` 创建的虚拟环境，或安装 PR-Agent。

`<pr_url>` 是相关 PR 的 URL（例如：[#50](https://github.com/the-pr-agent/pr-agent/pull/50)）。

**说明：**

1. 除了编辑本地配置文件，你也可以把可在仓库级配置的值加到命令行来修改它们：

```
python -m pr_agent.cli --pr_url=<pr_url>  /review --pr_reviewer.extra_instructions="focus on the file: ..."
```

主机侧控制的值，包括平台身份验证、TLS 和端点设置，会在命令参数中被拒绝。详情参见[配置选项](./configuration_options.md#local-configuration-file)。

2. 你可以在 `configuration.toml` 中设置，从而在本地打印结果而不发布它们：

```
[config]
publish_output=false
verbosity_level=2
```

这在调试或试用不同工具时很有用。

3. **Git 平台**：配置文件中的 [git_provider](https://github.com/the-pr-agent/pr-agent/blob/main/pr_agent/settings/configuration.toml) 字段决定 PR-Agent 将使用的 GIT 平台。目前支持以下平台：
`github` **（默认）**、`gitlab`、`bitbucket`、`azure`、`codecommit`、`local` 和 `gitea`。

4. 对于需要让失败请求返回非零进程状态的脚本，请启用工具错误传播：

```bash
python -m pr_agent.cli --pr_url=<pr_url> review --config.propagate_tool_errors=true
```

当 `config.propagate_tool_errors=true` 时，如果被传播的工具错误导致请求失败，或者工具即使成功返回也记录了一次失败，已安装的 `pr-agent` 命令、`python -m pr_agent.cli` 以及可自定义的 pip 脚本都会以状态 1 退出。在后一种情况下，CLI 会记录一条警告，说明这次非零退出。

工具错误传播默认关闭，对这些工具失败保留现有的状态 0 行为。Argparse 的解析和用法错误仍然以状态 2 退出。

### CLI 健康检查

要验证 PR-Agent 是否已正确配置，可以从仓库根目录运行此健康检查命令：

```bash
python -m tests.health_test.main
```

如果健康检查通过，你会在运行结束时看到以下输出：

```
========
Health test passed successfully
========
```

在运行健康检查之前，请确保你已经：

- 配置了[LLM 提供商](./changing_a_model.md)
- 在配置文件中添加了有效的 GitHub 令牌

## 在线用法 {#online-usage}

在线用法是指通过 PR 上的[评论](https://github.com/the-pr-agent/pr-agent/pull/229#issuecomment-1695021901)调用 PR-Agent 工具。
通过评论调用不同工具的命令：

- **审查**：       `/review`
- **描述**：     `/describe`
- **改进**：      `/improve`  （Bitbucket 上可用 `/improve_code`，因为 `/improve` 有时会被保留）
- **提问**：          `/ask "..."`
- **更新变更日志**：      `/update_changelog`

要编辑某个配置值，只需在任意命令后添加 `--config_path=<value>`。
例如，如果要编辑 `review` 工具的配置，可以运行：

```
/review --pr_reviewer.extra_instructions="..." --pr_reviewer.require_score_review=false
```

[配置文件](https://github.com/the-pr-agent/pr-agent/blob/main/pr_agent/settings/configuration.toml)中的大多数值都可以用同样的方式编辑。主机侧控制的设置，包括平台连接位置和凭据，不能通过 PR 评论更改。评论 `/config` 可查看可用配置列表。

## PR-Agent 自动反馈 {#pr-agent-automatic-feedback}

### 禁用所有自动反馈

要方便地禁用 PR-Agent 的全部自动反馈（GitHub App、GitLab Webhook、BitBucket App、Azure DevOps Webhook），在配置文件中设置：

```toml
[config]
disable_auto_feedback = true
```

当该参数设为 `true` 时，打开新 PR 或向已打开的 PR 推送新代码时，PR-Agent 不会运行任何自动工具（如 `describe`、`review`、`improve`）。

### GitHub App

:::note[PR-Agent 的配置]
这些设置适用于自托管的 GitHub App、GitLab webhook 和 Bitbucket App 部署。
:::

#### 打开新 PR 时 GitHub App 的自动工具 {#github-app-automatic-tools-when-a-new-pr-is-opened}

[github_app](https://github.com/the-pr-agent/pr-agent/blob/main/pr_agent/settings/configuration.toml) 部分定义 GitHub App 的专用配置。

配置参数 `pr_commands` 定义打开新 PR 时将**自动运行**的工具列表：

```toml
[github_app]
pr_commands = [
    "/describe",
    "/review",
    "/improve",
]
```

这意味着当新 PR 被打开/重新打开或标记为可供审查时，PR-Agent 会运行 `describe`、`review` 和 `improve` 工具。

**草稿 PR：**

默认情况下，草稿 PR 不会纳入自动工具，但你可以在配置文件中把 `feedback_on_draft_pr` 参数设为 `true` 来改变这一点。
启用后，把 PR 标记为就绪不会第二次运行 `pr_commands`。
因为该设置可以按仓库覆盖，草稿 PR 事件（包括每次由推送引起的 `synchronize` 事件）在被跳过之前仍会获取仓库配置。

```toml
[github_app]
feedback_on_draft_pr = true
```

**更改默认工具参数：**

你可以用[配置文件](./configuration_options.md)的三种选项之一覆盖默认工具参数：**本地**、**全局**或**外部 URL**。
例如，如果配置文件包含：

```toml
[pr_description]
generate_ai_title = true
```

每次运行 `describe` 工具（包括自动运行）时，PR 标题都会由 AI 生成。


**自动运行的参数：**

你可以使用 `--config_path=<value>` 参数，专门为自动运行自定义配置。
这些命令参数会在加载仓库之前应用，因此可以控制这次加载，并在之后再次应用，使命令值优先于仓库设置。
例如，要只为新打开的 PR 修改 `review` 工具设置，请使用：

```toml
[github_app]
pr_commands = [
    "/describe",
    "/review --pr_reviewer.extra_instructions='focus on the file: ...'",
    "/improve",
]
```

#### 推送操作的自动工具（向已打开的 PR 提交）

除了在 PR 打开时运行自动工具，PR-Agent 也可以响应推送到已打开 PR 的新代码。这对 **GitHub App** 和 **GitHub Action** 部署都有效。

配置开关 `handle_push_trigger` 可用于启用此功能。
配置参数 `push_commands` 定义有新代码推送到 PR 时将**自动运行**的工具列表。

```toml
[github_app]
handle_push_trigger = true
push_commands = [
    "/describe",
    "/review",
]
```

对于 GitHub Action，设置会从 `github_action_config.*` 回退到 `github_app.*`，因此你可以设置其中任一节。

这意味着当有新代码推送到 PR 时，PR-Agent 会按指定参数运行 `describe` 和 `review` 工具。

### GitHub Action

`GitHub Action` 是触发 PR-Agent 工具的另一种方式，使用与 `GitHub App` 不同的配置机制。<br>
你可以在 `.github/workflows/pr_agent.yml` 文件的 env 部分下添加环境变量，来配置 `GitHub Action` 的设置。

:::tip[Fork/贡献支持]
要支持来自 fork 仓库的 PR，请使用 `pull_request_target` 事件而不是 `pull_request`。完整示例和安全注意事项见[fork 贡献指南](../installation/github.md#using-with-pull_request_target-forkcontribution-support)。
:::

具体来说，先设置以下环境变量：

```yaml
      env:
        OPENAI_KEY: ${{ secrets.OPENAI_KEY }} # Make sure to add your OpenAI key to your repo secrets
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }} # Make sure to add your GitHub token to your repo secrets
        github_action_config.auto_review: "true" # enable\disable auto review
        github_action_config.auto_describe: "true" # enable\disable auto describe
        github_action_config.auto_improve: "true" # enable\disable auto improve
        github_action_config.pr_actions: '["opened", "reopened", "ready_for_review", "review_requested"]'
```

`github_action_config.auto_review`、`github_action_config.auto_describe` 和 `github_action_config.auto_improve` 用于启用/禁用在打开新 PR 时运行的自动工具。
如果未设置，默认配置是在打开新 PR 时三个工具全部自动运行。

`github_action_config.pr_actions` 用于配置哪些 `pull_requests` 事件会触发已启用的自动标志。
如果未设置，默认配置是 `["opened", "reopened", "ready_for_review", "review_requested"]`。
把 `"synchronize"` 加入此列表，会在向已打开的 PR 推送新提交时启用自动工具。你还必须把 `synchronize` 加入工作流的 `pull_request: types:` 列表。

`github_action_config.handle_push_trigger` 控制 synchronize 事件是否运行推送命令（默认 `false`）。如果未在 `github_action_config` 下设置，设置会回退到 `github_app.*`。由于它默认为 `false`，synchronize 是可选的——你必须显式启用它，方法是把 `"synchronize"` 加入 `pr_actions`，或设置 `handle_push_trigger = true`。

`github_action_config.push_commands` 定义启用 `handle_push_trigger` 时，哪些工具会在 synchronize 事件上运行（回退到 `github_app.push_commands`）。

`github_action_config.push_trigger_ignore_merge_commits`（默认 `true`）会在推送包含合并提交时跳过处理，避免在点击 “Update branch” 时产生重复审查。

`github_action_config.push_trigger_ignore_bot_commits`（默认 `true`）会在推送作者是机器人时跳过处理，避免在自动提交上重复运行。

`github_action_config.fail_on_tool_errors`（默认 `true`）会在工具记录了一次被吞掉的失败时（默认 `propagate_tool_errors = false` 的情况），让 Action 以非零状态退出，而不是在没有得到审查的拉取请求上以绿色结束。把它设为 `false` 可恢复先前忽略已记录工具失败的行为。请在工作流配置中设置它；`/review --github_action_config.fail_on_tool_errors=false` 这类评论参数会被拒绝。

#### 提交 GitHub 审查后的自动工具

GitHub App 可以在人工审查者提交原生 GitHub 审查之后运行已配置的工具。这是可选的：`review_commands` 默认为空。默认情况下，只有由 `User` 类型的审查作者以 `changes_requested` 状态提交的审查才会触发这些命令。这一保守默认避免在仓库中大量的 `commented` 审查上运行；需要不同工作流时，请显式设置 `review_states` 或 `review_author_types`。

```toml
[github_app]
review_states = ["changes_requested"]
review_author_types = ["User"]
review_commands = [
    "/improve",
]
```

事件必须是 `submitted`；已编辑或已驳回的审查不会触发工具。审查作者的 `user.type` 必须匹配 `review_author_types`，后者默认为 `User`，从而防止机器人审查触发命令。现有的仓库过滤、草稿 PR 处理、资格检查以及 `config.disable_auto_feedback` 仍然适用。审查文本不会被当作命令；每个已配置的命令都带着正常的拉取请求上下文运行。

对于 GitHub Action，请把审查事件加入工作流，并配置等价的设置。存在对应项时，`github_action_config.*` 会覆盖相应的 `github_app.*` 设置。

```yaml
on:
  pull_request_review:
    types: [submitted]

env:
  github_action_config.review_states: '["changes_requested"]'
  github_action_config.review_author_types: '["User"]'
  github_action_config.review_commands: '["/improve"]'
```

`github_action_config.enable_output` 用于启用/禁用 GitHub Actions 的[输出参数](https://docs.github.com/en/actions/creating-actions/metadata-syntax-for-github-actions#outputs-for-docker-container-and-javascript-actions)（默认是 `true`）。
审查结果以 JSON 输出到 `steps.{step-id}.outputs.review` 属性。
JSON 结构等同于 [pr_reviewer_prompts.toml](https://github.com/the-pr-agent/pr-agent/blob/main/pr_agent/settings/pr_reviewer_prompts.toml) 中定义的 yaml 数据结构。

`github.publish_as_check_run` 控制是否把工具输出（review、describe、improve）发布为 GitHub Check Run，而不是 PR 评论（默认是 `false`）。启用后，结果会出现在 PR 的 “Checks” 标签页。工作流 YAML 中需要 `checks: write` 权限。在 GitHub App 上，每个自动命令会在工具运行之前把 check run 打开为进行中，这样作者在任何输出出现之前就能看到 PR-Agent 已经接手该拉取请求；当分块命令运行时，该进行中的 run 还会显示已分析的块数，例如 `PR-Agent is running /review analyzed 2 of 3 chunks`。该 run 会以工具的输出完成，或者在命令没有完成时标记为失败。

请注意，你可以通过向 `.github/workflows/pr_agent.yml` 添加环境变量，或在仓库根目录使用 `.pr_agent.toml` [配置文件](./configuration_options.md#global-configuration-file)，来提供额外的配置参数。

例如，你可以设置环境变量 `pr_description.publish_labels=false`，或添加内容如下的 `.pr_agent.toml` 文件：

```toml
[pr_description]
publish_labels = false
```

以防止 PR-Agent 在运行 `describe` 工具时发布标签。

#### 启用在 PR 中使用命令

你可以配置 GitHub Actions 工作流，使其在 `issue_comment` [事件](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#issue_comment)（`created` 和 `edited`）上触发。

GitHub Actions 工作流配置示例：

```yaml
on:
  issue_comment:
    types: [created, edited]
```

配置之后，就可以通过在 PR 上评论来调用 PR-Agent。

#### 快速参考：在 GitHub Actions 中配置模型

关于在 GitHub Actions 中配置不同模型（Gemini、Claude、Azure OpenAI 等）的详细分步示例，请参见安装指南中的[配置示例](../installation/github.md#configuration-examples)部分。

**常见模型配置模式：**

- **OpenAI**：设置 `config.model: "<openai-model>"` 和 `OPENAI_KEY`
- **Gemini**：设置 `config.model: "gemini/gemini-3.8-flash"` 和 `GOOGLE_AI_STUDIO.GEMINI_API_KEY`（不需要 `OPENAI_KEY`）
- **Claude**：设置 `config.model: "anthropic/claude-opus-5"` 和 `ANTHROPIC.KEY`（不需要 `OPENAI_KEY`）
- **Azure OpenAI**：设置 `OPENAI.API_TYPE: "azure"`、`OPENAI.API_BASE` 和 `OPENAI.DEPLOYMENT_ID`
- **本地模型**：设置 `config.model: "ollama/model-name"` 和 `OLLAMA.API_BASE`

**环境变量格式：**

- 用点（`.`）分隔节和键：`config.model`、`pr_reviewer.extra_instructions`
- 布尔值用字符串：`"true"` 或 `"false"`
- 数组用 JSON 字符串：`'["item1", "item2"]'`

完整的模型配置细节见[在 PR-Agent 中更换模型](changing_a_model.md)。

### GitLab Webhook

设置好 GitLab webhook 之后，要控制打开新 MR 时自动运行哪些命令，可以像 GitHub App 那样，在配置文件中设置 `pr_commands` 参数：

```toml
[gitlab]
pr_commands = [
    "/describe",
    "/review",
    "/improve",
]
```

草稿 MR 默认会被跳过。在 `[gitlab]` 下设置 `feedback_on_draft_pr = true` 可启用自动反馈。
启用后，把 MR 标记为就绪不会第二次运行 `pr_commands`。
因为该设置可以按仓库覆盖，草稿 MR 事件在被跳过之前仍会获取仓库配置。
对于基于环境变量的部署，请设置 `GITLAB__FEEDBACK_ON_DRAFT_PR=true`。

GitLab webhook 也可以响应推送到已打开 MR 的新代码。
配置开关 `handle_push_trigger` 可用于启用此功能。
配置参数 `push_commands` 定义有新代码推送到 MR 时将**自动运行**的工具列表。

```toml
[gitlab]
handle_push_trigger = true
push_commands = [
    "/describe",
    "/review",
]
```

请注意，要使用 'handle_push_trigger' 功能，你还需要给 GitLab webhook 授予 “Push events” 范围。

GitLab webhook 也可以响应机器人被指定为已打开 MR 的审查者。
配置开关 `handle_reviewer_assignment` 可用于启用此功能。
配置参数 `reviewer_commands` 定义机器人被加入 MR 审查者时将**自动运行**的工具列表。

```toml
[gitlab]
handle_reviewer_assignment = true
reviewer_commands = [
    "/review",
]
```

这些命令只在机器人被新加入审查者列表时运行，因此在不更改审查者的情况下重新保存 MR 不会再次运行它们。
机器人由 `gitlab.personal_access_token` 背后的用户标识，因此必须设置该令牌，此功能才能工作。
草稿 MR 以及匹配[忽略设置](additional_configurations.md#ignoring-automatic-commands-in-prs)的 MR 会被跳过。

### BitBucket App

与 GitHub App 类似，从 BitBucket App 运行 PR-Agent 时，会首先加载默认的[配置文件](https://github.com/the-pr-agent/pr-agent/blob/main/pr_agent/settings/configuration.toml)。

通过把本地 `.pr_agent.toml` 文件上传到仓库默认分支的根目录，你可以自定义支持仓库级覆盖的参数。请注意，需要在创建 PR 之前上传 `.pr_agent.toml`，配置才会生效。

平台端点设置由主机控制。[本地配置指南](./configuration_options.md#local-configuration-file)中列出的端点键，如果设置在仓库本地的 `.pr_agent.toml` 中会被忽略，必须在主机上配置。

例如，如果本地 `.pr_agent.toml` 文件包含：

```toml
[pr_reviewer]
extra_instructions = "Answer in japanese"
```

每次调用 `/review` 工具时，都会使用你在本地配置文件中设置的额外指令。

请注意，除其他限制外，BitBucket 为应用提供的速率限制相对较低（每小时最多 1000 次请求），并且不提供用于跟踪实际速率限制用量的 API。
如果 PR-Agent 没有响应，你可能需要在配置文件中设置：`bitbucket_app.avoid_full_files=true`。
这将阻止 PR-Agent 获取完整文件内容，而只使用 diff 内容。这会减少对 BitBucket 的请求次数，代价是准确度略有下降，因为动态上下文将不再适用。

对于自托管的 BitBucket App 部署，`bitbucket_app.request_timeout` 会为卸载出去的 BitBucket HTTP 请求同时设置连接超时和响应读取空闲超时，单位是正数秒。它默认为 `30`，并从主机级配置或 `BITBUCKET_APP__REQUEST_TIMEOUT` 环境变量读取；仓库的 `.pr_agent.toml` 覆盖不适用于这一主机资源限制。

#### BitBucket 自托管 App 的自动工具

要控制打开新 PR 时自动运行哪些命令，可以在配置文件中设置 `pr_commands` 参数：
具体来说，设置以下值：

```toml
[bitbucket_app]
pr_commands = [
    "/review",
    "/improve --pr_code_suggestions.committable_code_suggestions=true --pr_code_suggestions.suggestions_score_threshold=7",
]
```

请注意，我们专门为 bitbucket 设置，建议使用：`--pr_code_suggestions.suggestions_score_threshold=7`，这也是我们为 bitbucket 设置的默认值。
由于该平台只支持行内代码建议，我们希望限制建议数量，只呈现有限的数量。

要让 BitBucket App 响应对 PR 的每次**推送**，请设置（例如）：

```toml
[bitbucket_app]
handle_push_trigger = true
push_commands = [
    "/describe",
    "/review",
]
```

### Azure DevOps 平台 {#azure-devops-provider}

要使用 Azure DevOps 平台，请在 configuration.toml 中使用以下设置：

```toml
[config]
git_provider="azure"
```

Azure DevOps 平台支持 [PAT 令牌](https://learn.microsoft.com/en-us/azure/devops/organizations/accounts/use-personal-access-tokens-to-authenticate?view=azure-devops&tabs=Windows)或 [DefaultAzureCredential](https://learn.microsoft.com/en-us/azure/developer/python/sdk/authentication-overview#authentication-in-server-environments) 身份验证。
PAT 创建更快，但内置了过期日期，并且 API 调用会使用用户身份。
使用 DefaultAzureCredential 时，你可以使用托管身份或服务主体，它们更安全，并且会（通过 AAD）为该代理创建单独的 ADO 用户身份。

如果选择了 PAT，可以在 .secrets.toml 中赋值。
如果选择了 DefaultAzureCredential，可以直接指定 AZURE_CLIENT_SECRET 等额外环境变量，
也可以使用托管身份/az cli（用于本地开发），无需任何额外配置。
无论哪种情况，都必须在 .secrets.toml 中指定 'org' 值：

```
[azure_devops]
org = "https://dev.azure.com/YOUR_ORGANIZATION/"
# pat = "YOUR_PAT_TOKEN" needed only if using PAT for authentication
```

#### Azure DevOps Webhook

要控制打开新 PR 时自动运行哪些命令，可以像 GitHub App 那样，在配置文件中设置 `pr_commands` 参数：

```toml
[azure_devops_server]
pr_commands = [
    "/describe",
    "/review",
    "/improve",
]
```

### Gitea Webhook

设置好 Gitea webhook 之后，要控制打开新 MR 时自动运行哪些命令，可以像 GitHub App 那样，在配置文件中设置 `pr_commands` 参数：

```toml
[gitea]
pr_commands = [
    "/describe",
    "/review",
    "/improve",
]
```
