---
title: "用法与自动化"
sidebar_position: 5
---

本构建只支持 Gitee。请按 [Gitee 集成指南](../installation/gitee.md) 安装 Webhook。服务镜像是 `ecloud-tcr.tencentcloudcr.com/ecloud_project/pr-agent:latest`，构建目标为 `gitee_app`。

## 本地仓库（CLI） {#local-repo-cli}

本地运行使用启动 CLI 的那台机器上的配置。将 `config.git_provider` 设为 `gitee`，并传入 Gitee 拉取请求 URL（`https://gitee.com/<owner>/<repo>/pulls/<number>`）。

```bash
CONFIG__GIT_PROVIDER=gitee \
GITEE__PERSONAL_ACCESS_TOKEN=<personal_access_token> \
OPENAI__KEY=<your_openai_api_key> \
OPENAI__API_BASE=<your_openai_api_base> \
uv run python -m pr_agent.cli --pr_url=<pr_url> review
```

同一组环境变量也适用于其他工具：

- **审查**：`uv run python -m pr_agent.cli --pr_url=<pr_url> review`
- **描述**：`uv run python -m pr_agent.cli --pr_url=<pr_url> describe`
- **改进**：`uv run python -m pr_agent.cli --pr_url=<pr_url> improve`
- **提问**：`uv run python -m pr_agent.cli --pr_url=<pr_url> ask "Write me a poem about this PR"`
- **更新变更日志**：`uv run python -m pr_agent.cli --pr_url=<pr_url> update_changelog`

请使用 `uv sync` 创建的虚拟环境，或任何可以导入 `pr_agent` 包的环境。`<pr_url>` 必须是 Gitee 拉取请求。其他 Git 托管平台不会被接受。

`/update_changelog` 只发表评论。Gitee 没有 `push_code` 能力，因此 PR-Agent 不会提交 `CHANGELOG.md`。

**说明：**

1. 可在仓库级配置的值也可以写在命令行上：

```bash
uv run python -m pr_agent.cli --pr_url=<pr_url> review --pr_reviewer.extra_instructions="focus on the file: ..."
```

主机控制的值会被拒绝。这包括 `GITEE__PERSONAL_ACCESS_TOKEN`、`GITEE__WEBHOOK_SECRET`、`gitee.api_base`、`gitee.skip_ssl_verification`、`gitee.ssl_ca_cert`，以及 `openai.api_base` 这类模型端点设置。见[本地配置文件](./configuration_options.md#local-configuration-file)。

2. 若只在本地打印结果、不在拉取请求上发表评论，请设置：

```toml
[config]
publish_output = false
verbosity_level = 2
```

3. `git_provider` 必须是 `gitee`（`CONFIG__GIT_PROVIDER=gitee`）。本构建不会选择其他提供商。

4. 如果脚本需要在工具失败时以非零状态退出，请打开错误传播：

```bash
uv run python -m pr_agent.cli --pr_url=<pr_url> review --config.propagate_tool_errors=true
```

当 `config.propagate_tool_errors=true` 时，若传播的工具错误导致请求失败，或者工具记录了失败却仍然成功返回，`pr-agent` 和 `python -m pr_agent.cli` 会以状态 1 退出。后一种情况 CLI 会记录一条警告。该开关默认关闭，因此这些失败仍以 0 退出。argparse 的用法错误仍以 2 退出。

## 在线用法 {#online-usage}

在线用法是在 Gitee 拉取请求上发表评论。评论只有在以 `/` 开头时才会被处理。

- **审查**：`/review`
- **描述**：`/describe`
- **改进**：`/improve`
- **提问**：`/ask "..."`
- **更新变更日志**：`/update_changelog`

`/update_changelog` 把生成的变更日志作为评论发表，不会推送提交。

在命令后追加 `--<section>.<key>=<value>`，可以只对这一次运行覆盖可在仓库级配置的设置：

```text
/review --pr_reviewer.extra_instructions="..." --pr_reviewer.require_score_review=false
```

主机控制的设置不能通过评论修改，包括 Gitee 令牌、Webhook 密钥、TLS 设置和模型端点。评论 `/config` 可以列出允许修改的设置。完整列表见[配置参考](./configuration_reference.md)。

## Gitee Webhook {#gitee-webhook}

Webhook 服务器是 `gitee_app` 目标。它监听：

```text
POST /api/v1/gitee_webhooks
```

用下面的主机环境运行发布镜像：

```bash
CONFIG__GIT_PROVIDER=gitee
GITEE__PERSONAL_ACCESS_TOKEN=<personal_access_token>
GITEE__WEBHOOK_SECRET=<webhook_secret>
OPENAI__KEY=<your_openai_api_key>
OPENAI__API_BASE=<your_openai_api_base>
```

`GITEE__WEBHOOK_SECRET` 是必需的。密钥为空时，每个 Webhook 都会以 HTTP 403 被拒绝。在 Gitee 仓库中，把 Webhook URL 设为 `https://<PR_AGENT_HOSTNAME>/api/v1/gitee_webhooks`，使用同一个密钥，并订阅拉取请求和评论事件。推送事件不会运行命令。

PR-Agent 在解析 JSON 正文之前检查签名。

| 请求头 | 作用 |
| --- | --- |
| `X-Gitee-Timestamp` | Gitee 发送的 Unix 时间戳，单位为毫秒。 |
| `X-Gitee-Token` | 对 `<timestamp>\n<secret>` 做 HMAC-SHA256 后的 Base64。 |

签名内容是时间戳、一个换行，然后是 Webhook 密钥。与服务器时钟相差超过一小时的时间戳会被拒绝。签名不正确时返回 HTTP 401。

### 默认模式 {#github-app}

新打开的拉取请求会运行 `/describe`、`/review` 和 `/improve`。这是本构建的默认模式。评论只有在以 `/` 开头时才会运行，并且只运行该条命令。

### 打开拉取请求时运行的命令 {#github-app-automatic-tools-when-a-new-pr-is-opened}

`gitee.pr_commands` 是拉取请求打开时运行的命令列表。未设置时为：

```toml
[gitee]
pr_commands = [
    "/describe",
    "/review",
    "/improve",
]
```

在主机配置或仓库的 [`.pr_agent.toml`](./configuration_options.md#local-configuration-file) 里修改该列表，即可改变自动运行的工具。空列表表示打开时不运行任何命令。写在命令上的参数只作用于那一次自动运行：

```toml
[gitee]
pr_commands = [
    "/describe",
    "/review --pr_reviewer.extra_instructions='focus on the file: ...'",
    "/improve",
]
```

`[pr_description]` 这类工具默认值对自动运行和评论都生效。例如 `generate_ai_title = true` 会让每一次 `/describe` 都生成标题。

Gitee 从拉取请求的目标分支读取 `.pr_agent.toml`。推送事件会被忽略，因此向已打开的拉取请求推送新提交不会再次自动运行。需要再次运行时，在拉取请求上发表评论。

## 自动反馈 {#pr-agent-automatic-feedback}

本构建里的自动反馈就是上面的“打开拉取请求”命令列表。没有 GitHub App、GitHub Action、GitLab pipeline、Bitbucket 应用或 Azure DevOps Webhook 需要配置。

要停止自动命令，把 `gitee.pr_commands` 设为 `[]`。以 `/` 开头的评论命令仍然会运行。[其他配置](./additional_configurations.md#ignoring-automatic-commands-in-prs) 中的忽略规则会同时跳过自动运行，以及标题、作者、标签、分支或仓库匹配的评论命令。
