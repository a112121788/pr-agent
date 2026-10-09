---
title: "配置文件"
sidebar_position: 3
---

PR-Agent 使用的各种工具和子工具，都可以通过仓库中的配置文件调整。
持久配置主要有三种设置方式：

1. [本地](./configuration_options.md#local-configuration-file)配置文件
2. [全局](./configuration_options.md#global-configuration-file)配置文件
3. [外部配置 URL](./configuration_options.md#external-configuration-url)（CLI 标志）

优先级上，本地配置会覆盖全局配置，全局配置会覆盖外部配置 URL。


全部可用配置见[配置选项](https://github.com/the-pr-agent/pr-agent/blob/main/pr_agent/settings/configuration.toml)页面，或已渲染的[配置参考](./configuration_reference.md)，其中按节列出每个选项。
除通用配置选项外，每个工具还有自己的配置。例如，`review` 工具会使用配置文件中 [pr_reviewer](https://github.com/the-pr-agent/pr-agent/blob/main/pr_agent/settings/configuration.toml) 节的参数。

:::tip[提示 1：只改你需要的部分]
配置文件应尽量精简，只修改相关的值。不要复制全部配置选项，否则在配置发生变化时容易留下过时问题。
:::

:::tip[提示 2：显示相关配置]
如果把 `config.output_relevant_configurations` 设为 True，每个工具还会在折叠区域中输出自己的相关配置。这有助于调试，或更好地了解这些配置。
:::



## 本地配置文件 {#local-configuration-file}

`支持的平台：GitHub、GitLab、Bitbucket、Azure DevOps`

把本地 `.pr_agent.toml` 文件上传到仓库默认分支的根目录，即可自定义支持仓库级覆盖的参数。请注意，需要在使用 PR Agent 工具之前（创建拉取请求时或手动触发时）上传或更新 `.pr_agent.toml`，配置才会生效。

提供商端点设置由主机控制：在仓库本地 `.pr_agent.toml` 中设置的 `openai.api_base`、`openai.api_type`、`openai.api_version`、`azure_ad.api_base`、`databricks.api_base`、`huggingface.api_base`、`moonshot.api_base`、`ollama.api_base` 和 `openrouter.api_base` 会被忽略，必须在主机上配置。同样的限制适用于提供商身份验证和 TLS 设置：`github.deployment_type`、`bitbucket.auth_type`、`gitlab.auth_type`、`gitlab.ssl_verify`、`gitea.skip_ssl_verification` 和 `gitea.ssl_ca_cert`。Jira 工单查询使用主机的 Atlassian 凭据，因此 `jira.jira_site`、`jira.jira_api_email` 和 `jira.project_keys` 同样由主机控制。这些设置在命令参数中也会被拒绝。

例如，如果在 `.pr_agent.toml` 中设置：

```
[pr_reviewer]
extra_instructions="""\
- instruction a
- instruction b
...
"""
```

就可以向 `review` 工具提供一组额外指令。

### 从非默认分支加载本地配置 {#loading-the-local-configuration-from-a-non-default-branch}

`支持的平台：GitHub、GitLab`

默认情况下，本地 `.pr_agent.toml` 从仓库的**默认分支**读取。从 CLI（或任何暴露其参数的封装）运行 PR-Agent 时，可以让它指向另一个分支——例如在合并之前，用功能分支测试配置变更：

```bash
python -m pr_agent.cli \
  --pr_url=<PR URL> \
  --config-branch=<branch name> \
  review
```

等价做法是设置环境变量 `PR_AGENT_CONFIG_BRANCH`。CLI 标志优先于环境变量，仅含空白的值会被忽略。

如果无法从所请求的分支加载 `.pr_agent.toml`（例如分支或文件不存在），PR-Agent 会记录警告并回退到默认分支。

:::danger[安全：将配置分支视为特权来源]
默认情况下，配置从**默认分支**读取，因此只有能合并到该分支的用户才能改变 PR-Agent 的行为。`--config-branch` / `PR_AGENT_CONFIG_BRANCH` 把这条信任边界移到你所指定的任意分支。

**切勿根据不可信或来自拉取请求的输入设置配置分支**（例如在 CI 中使用 `--config-branch=$GITHUB_HEAD_REF` / `${{ github.head_ref }}`）。这样做会让任何能向仓库推送分支的人提供自己的 `.pr_agent.toml` 并控制审查——例如把 `model` 或 API 基址指向攻击者的端点以窃取 diff、注入 `extra_instructions`，或启用对自己拉取请求的自动批准。始终把配置分支固定到由维护者控制的固定分支。
:::

:::note[提供商的分支行为]
分支选择目前为 GitHub 和 GitLab 实现。Gitea 会忽略这些选项，并从
拉取请求的目标 ref 读取本地 `.pr_agent.toml`，该 ref 可能不同于默认分支。
Gerrit 也会忽略这些选项，但从克隆下来的默认分支读取该文件。其他平台
仍使用各自提供商特定的设置来源。
:::

## 全局配置文件 {#global-configuration-file}

`支持的平台：GitHub、GitLab、Bitbucket（云）、Bitbucket Server、Azure DevOps、Gitea`

在部署自身的配置中用 `global_settings_repo` 指定一个组织级设置仓库；其 `.pr_agent.toml`（从该仓库的默认分支读取）会作为同一组织下每个仓库的全局配置。该设置默认为空，即关闭此功能，仓库的 `.pr_agent.toml` 或评论不能设置它。当 `global_settings_repo = "pr-agent-settings"` 时，读取的仓库为：

- **GitHub：** `<organization>/pr-agent-settings`
- **GitLab：** `<top-level-group>/pr-agent-settings`（GitLab.com 与自托管 GitLab 皆然）
- **Bitbucket（云）：** `<workspace>/pr-agent-settings`
- **Bitbucket Server：** `<project>/pr-agent-settings`
- **Azure DevOps：** `<org>/<project>/pr-agent-settings`（在与当前仓库相同的项目中查找）
- **Gitea：** `<owner>/pr-agent-settings`

特定仓库中本地 `.pr_agent.toml` 文件的参数会覆盖全局配置参数（全局文件合并在仓库本地文件*之下*）。
对于 GitHub Enterprise Server，在你的 GHES 主机上使用同样的组织级仓库。
PR-Agent 使用的应用安装或令牌必须对拉取请求仓库和设置仓库都有读权限；否则，PR-Agent 会跳过全局配置，继续使用仓库本地设置。

:::note[缓存]
在长期运行的部署（GitHub App / webhook 服务器）中，取回的全局设置会**在进程内**缓存最多 15 分钟，以避免每个 webhook 事件都重新获取，因此设置仓库的变更最多可能要这么久才会在那里生效。CLI 和 CI（GitHub Action）运行是短生命周期进程，因此每次调用获取一次全局设置，并且总能看到最新版本。
:::

是否加载全局设置文件由 `use_global_settings_file` 标志控制，它**默认启用**，但在设置 `global_settings_repo` 之前不会读取任何内容。若要退出并只依赖每个仓库的本地 `.pr_agent.toml`，请设置：

```toml
[config]
use_global_settings_file = false
```

例如，在名为 `my-org` 的 GitHub 组织中设置 `global_settings_repo = "pr-agent-settings"`：

- 文件 `my-org/pr-agent-settings/.pr_agent.toml`（从该仓库的默认分支读取）作为该组织中所有仓库的全局配置文件。

- `my-org/my-repo` 这样的仓库会继承该全局配置文件，并可以在自己的 `.pr_agent.toml` 中覆盖其可在仓库级配置的值。

## 项目/群组级配置文件 {#projectgroup-level-configuration-file}

`支持的平台：GitLab、Bitbucket Data Center`

一旦设置了 `global_settings_repo`，就会读取特定项目（Bitbucket）或群组/子群组（GitLab）中同名的仓库。
该仓库中的配置文件会应用于同一项目/群组/子群组直接下属的所有仓库。

:::note[注意]
对于 GitLab，如果仓库嵌套在多个子群组中，设置仓库只会在该仓库的上一级查找。
:::

## 外部配置 URL {#external-configuration-url}

`支持的平台：GitHub、GitLab、Bitbucket、Azure DevOps`

从 CLI（或任何暴露其参数的封装）运行 PR-Agent 时，可以在应用仓库本地配置和全局配置之前，从任意 URL 或本地路径再合并一份 `.pr_agent.toml`。这在以下情况有用：

- 你希望一份共享配置应用到深嵌在子群组中的仓库，而[项目/群组级查找](./configuration_options.md#projectgroup-level-configuration-file)只向上走一级。
- 共享配置发布在 Git 主机之外（静态站点、内部制品服务器、S3 存储桶等）。
- 你希望在 CI 时控制叠入哪些默认值，而不把文件提交到目标仓库。

### 用法 {#usage}

向 CLI 传入 `--extra_config_url`，或设置环境变量 `PR_AGENT_EXTRA_CONFIG_URL`：

```bash
python -m pr_agent.cli \
  --pr_url=<MR/PR URL> \
  --extra_config_url=https://config.example.com/pr-agent/shared.toml \
  review
```

可接受的值：

- `https://…` 或 `http://…`——运行时获取
- `file:///path/to/shared.toml`——从本地文件系统读取
- 裸文件系统路径——与 `file://` 相同

### 私有端点的身份验证 {#authentication-for-private-endpoints}

对于私有端点（例如指向私有 `pr-agent-settings` 文件的 GitLab API URL），通过环境变量 `PR_AGENT_EXTRA_CONFIG_AUTH_HEADER` 提供单个请求头，格式为 `<HeaderName>: <value>`：

```bash
# GitLab Personal Access Token
export PR_AGENT_EXTRA_CONFIG_AUTH_HEADER="PRIVATE-TOKEN: <your-personal-access-token>"

# GitLab CI job token
export PR_AGENT_EXTRA_CONFIG_AUTH_HEADER="JOB-TOKEN: $CI_JOB_TOKEN"

# Generic bearer token
export PR_AGENT_EXTRA_CONFIG_AUTH_HEADER="Authorization: Bearer <your-token>"
```

### 优先级 {#precedence}

外部 URL 的设置**最先**应用，因此其他每一层都会覆盖它们：

```
built-in defaults
  < --extra_config_url
    < global pr-agent-settings
      < local .pr_agent.toml (repo default branch)
        < environment variables (PR_AGENT__SECTION__KEY)
```

这意味着外部 URL 充当组织范围的*默认值*，任何团队仍可以用自己的 `pr-agent-settings` 或仓库本地 `.pr_agent.toml` 覆盖它。

### 安全与限制 {#security-and-limits}

外部文件通过与仓库本地 `.pr_agent.toml` 相同的安全加载器加载：include、preload、自定义加载器，以及其他可能执行代码或读取任意文件的指令都会被拒绝。获取器另外还会：

- 把响应大小限制为 **1 MB**
- 使用 **10 秒**请求超时
- 只接受 `http`、`https`、`file` 方案（或裸本地路径）

如果获取失败，会记录该请求，PR-Agent 继续使用其余配置层。
