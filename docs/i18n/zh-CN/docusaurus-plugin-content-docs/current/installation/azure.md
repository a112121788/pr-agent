---
title: "Azure DevOps 集成"
sidebar_position: 7
---

## Azure DevOps 流水线 {#azure-devops-pipeline}

你可以使用预构建的 Action Docker 镜像，把 PR-Agent 作为 Azure DevOps 流水线运行。
在仓库中添加以下文件，路径为 `azure-pipelines.yml`：

```yaml
# Opt out of CI triggers
trigger: none

# Configure PR trigger
# pr:
#   branches:
#     include:
#     - '*'
#   autoCancel: true
#   drafts: false

# NOTE for Azure Repos Git:
# Azure Repos does not honor YAML pr: triggers. Configure Build Validation
# via Branch Policies instead (see note below). You can safely omit pr:.

stages:
- stage: pr_agent
  displayName: 'PR Agent Stage'
  jobs:
  - job: pr_agent_job
    displayName: 'PR Agent Job'
    pool:
      vmImage: 'ubuntu-latest'
    container:
      image: pragent/pr-agent:latest
      options: --entrypoint ""
    variables:
      - group: pr_agent
    steps:
    - script: |
        echo "Running PR Agent action step"

        # Construct PR_URL
        PR_URL="${SYSTEM_COLLECTIONURI}${SYSTEM_TEAMPROJECT}/_git/${BUILD_REPOSITORY_NAME}/pullrequest/${SYSTEM_PULLREQUEST_PULLREQUESTID}"
        echo "PR_URL=$PR_URL"

        # Extract organization URL from System.CollectionUri
        ORG_URL=$(echo "$(System.CollectionUri)" | sed 's/\/$//') # Remove trailing slash if present
        echo "Organization URL: $ORG_URL"

        export azure_devops__org="$ORG_URL"
        export config__git_provider="azure"

        pr-agent --pr_url="$PR_URL" describe
        pr-agent --pr_url="$PR_URL" review
        pr-agent --pr_url="$PR_URL" improve
      env:
        azure_devops__pat: $(azure_devops_pat)
        openai__key: $(OPENAI_KEY)
      displayName: 'Run PR-Agent'
```

此脚本会在每个新的合并请求上运行 PR-Agent，并执行 `improve`、`review` 和 `describe` 命令。
注意，你需要在 Azure DevOps 流水线设置中导出 `azure_devops__pat` 和 `OPENAI_KEY` 变量（Pipelines -> Library -> + Variable group）：

<img src="/img/azure_devops_pipeline_secrets.png" alt="PR-Agent" width="468" />

请确保为 `pr_agent` 变量组授予流水线权限。

> 请注意，Azure Pipelines 不支持由拉取请求评论触发工作流。如果你找到可行方案，欢迎贡献到我们的[议题跟踪器](https://github.com/the-pr-agent/pr-agent/issues)

### Azure Repos Git 的拉取请求触发器与生成验证

Azure Repos Git 不会为流水线使用 YAML 的 `pr:` 触发器。请改为在目标分支上配置生成验证（Build Validation），以便为拉取请求运行 PR Agent 流水线：

1. 进入项目设置 → 仓库 → 分支。
2. 选择目标分支并打开分支策略。
3. 在生成验证下添加一条策略：
   - 选择 PR Agent 流水线（即上面的 `azure-pipelines.yml`）。
   - 将其设为必需。
4. 从 YAML 中删除 `pr:` 小节（Azure Repos Git 不需要它）。

这一区别专门适用于 Azure Repos Git。GitHub 和 Bitbucket Cloud 等其他提供商可以使用基于 YAML 的拉取请求触发器。

## 从 CLI 使用 Azure DevOps

要使用 Azure DevOps 提供商，请在 configuration.toml 中使用以下设置：

```toml
[config]
git_provider="azure"
```

Azure DevOps 提供商支持 [PAT 令牌](https://learn.microsoft.com/en-us/azure/devops/organizations/accounts/use-personal-access-tokens-to-authenticate?view=azure-devops&tabs=Windows)或 [DefaultAzureCredential](https://learn.microsoft.com/en-us/azure/developer/python/sdk/authentication-overview#authentication-in-server-environments) 身份验证。
PAT 创建更快，但有内置过期时间，并且 API 调用会使用该用户身份。
使用 DefaultAzureCredential 时，你可以使用托管标识或服务主体，它们更安全，并会（通过 AAD）为代理创建单独的 ADO 用户身份。

如果选择 PAT，可以在 .secrets.toml 中赋值。
如果选择 DefaultAzureCredential，可以直接指定 AZURE_CLIENT_SECRET 等额外环境变量，
也可以使用托管标识 / az cli（用于本地开发），无需任何额外配置。
无论哪种情况，都必须在 .secrets.toml 中指定 `org` 值：

```toml
[azure_devops]
org = "https://dev.azure.com/YOUR_ORGANIZATION/"
# pat = "YOUR_PAT_TOKEN" needed only if using PAT for authentication
```

## Azure DevOps Webhook

要从 Azure webhook 触发，你需要手动
[添加 webhook](https://learn.microsoft.com/en-us/azure/devops/service-hooks/services/webhooks?view=azure-devops)。
使用「Pull request created」类型来触发审查，或使用「Pull request commented on」来触发受支持的
`/<command> <args>` 评论。评论事件需要 API v2.0。

也可以不使用斜杠命令、直接向代理提问。在拉取请求评论或行评论的开头提及 PR-Agent 所使用的 Azure DevOps 身份。PR-Agent 会从它先前的评论中发现该身份，在同一讨论串中回答，并使用现有讨论串作为上下文。`hi agent` 这类通用短语不会触发回复。

在 PR-Agent 尚未在该拉取请求上发过言之前的第一次提及，或当它的 Azure DevOps 身份发生变化时，
请配置一个稳定身份（GUID/ID、唯一名称或描述符）。身份过渡期间可以使用列表：

```toml
[azure_devops_server]
agent_identity = "<agent identity>"
```

Webhook 身份验证是必需的。创建一对用户名/密码，并在服务器和 Azure DevOps webhook 的基本身份验证设置中配置相同的值。Azure DevOps 会在每次请求中发送这些凭据：

```toml
[azure_devops_server]
webhook_username = "<basic auth user>"
webhook_password = "<basic auth password>"
```

如果任一设置缺失或为空，服务器会以 HTTP 403 拒绝 webhook 请求。两项都已配置时，没有有效基本凭据的请求会收到 HTTP 401。

> :warning: **请确保 webhook 端点只能通过 HTTPS 访问**，以降低使用基本身份验证时凭据被截获的风险。
