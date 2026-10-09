---
title: "配置文件"
sidebar_position: 3
---

Gitee PR-Agent 使用的工具从 TOML 配置读取选项。持久配置有三层：

1. [本地](./configuration_options.md#local-configuration-file)配置文件
2. [全局](./configuration_options.md#global-configuration-file)配置文件
3. [外部配置 URL](./configuration_options.md#external-configuration-url)（CLI）

本地配置覆盖全局配置，全局配置覆盖外部 URL。形如 `SECTION__KEY` 的环境变量覆盖这些文件。

全部键见[配置参考](./configuration_reference.md)，它由 [`configuration.toml`](https://github.com/the-pr-agent/pr-agent/blob/main/pr_agent/settings/configuration.toml) 渲染而来。每个工具还有自己的配置节。`/review` 读取 `[pr_reviewer]`。

:::tip[只改需要的项]
配置文件应尽量短。把整份默认文件复制进去后，以后的默认值变化会看起来像本地覆盖。
:::

:::tip[显示某次运行实际使用的设置]
当 `config.output_relevant_configurations` 为 true 时，每个工具会附加一个可折叠段落，列出本次生效的设置。评论参数不能打开它，因为该段落可能包含主机控制的值。请在 `.pr_agent.toml` 或主机配置里设置。
:::

## 本地配置文件 {#local-configuration-file}

把 `.pr_agent.toml` 上传到仓库。Gitee 从拉取请求的**目标**分支读取它，而不是从源分支读取，因此拉取请求不能把审查指向自己刚添加的文件。命令运行前，该文件必须已经在目标分支上。

路径默认为 `.pr_agent.toml`（`gitee.repo_setting`）。

下列 Gitee 键只属于主机。仓库文件不能设置它们：

- `gitee.api_base`
- `gitee.webhook_secret`
- `gitee.skip_ssl_verification`
- `gitee.ssl_ca_cert`

模型端点和凭据也只属于主机，包括 `openai.api_base` 和 `openai.key`。请在主机上用 `OPENAI__API_BASE` 和 `OPENAI__KEY` 设置，见[更换模型](./changing_a_model.md)。

`.pr_agent.toml` 示例：

```toml
[pr_reviewer]
extra_instructions = """\
- instruction a
- instruction b
"""
```

Gitee 提供商不使用 `--config-branch` 或 `PR_AGENT_CONFIG_BRANCH`。这两个选项不会把配置文件从目标分支移走。

## 全局配置文件 {#global-configuration-file}

在**主机**上把 `config.global_settings_repo` 设为同一 Gitee 所有者（命名空间）下的一个仓库名。PR-Agent 从该仓库的默认分支读取 `.pr_agent.toml`，并应用到该所有者下的每个仓库。此设置默认为空，即关闭该功能。仓库文件或评论不能设置 `global_settings_repo`。

当 `global_settings_repo = "pr-agent-settings"`，且拉取请求位于 `my-org/my-repo` 时，读取的是 `my-org/pr-agent-settings` 默认分支上的文件。`my-org/my-repo` 自己的 `.pr_agent.toml` 会覆盖它。

`GITEE__PERSONAL_ACCESS_TOKEN` 中的令牌必须能读取这两个仓库。如果设置仓库或文件不存在，PR-Agent 会跳过全局文件，并继续使用仓库本地文件。

:::note[缓存]
Gitee Webhook 进程会把全局文件缓存在内存中，最长 15 分钟。设置仓库里的修改可能要等这么久才生效。CLI 进程是短生命周期的，每次调用读取一次。
:::

`use_global_settings_file` 默认为 true，但在设置 `global_settings_repo` 之前不会读取任何文件。若要忽略全局文件：

```toml
[config]
use_global_settings_file = false
```

## 外部配置 URL {#external-configuration-url}

在 CLI 上，可以在全局文件和仓库本地文件之前再合并一份 `.pr_agent.toml`。当共享文件不在 Gitee 所有者的命名空间里，或者 CI 希望选择默认值而又不把文件提交到目标仓库时，可以使用它。

### 用法 {#usage}

传入 `--extra_config_url`，或设置 `PR_AGENT_EXTRA_CONFIG_URL`：

```bash
uv run python -m pr_agent.cli \
  --pr_url=<Gitee 拉取请求 URL> \
  --extra_config_url=https://config.example.com/pr-agent/shared.toml \
  review
```

可接受的值：

- `https://…` 或 `http://…`，运行时获取
- `file:///path/to/shared.toml`
- 裸文件系统路径，与 `file://` 相同

### 私有端点的身份验证 {#authentication-for-private-endpoints}

对于私有 URL，用 `PR_AGENT_EXTRA_CONFIG_AUTH_HEADER` 设置一个请求头，格式为 `<HeaderName>: <value>`：

```bash
export PR_AGENT_EXTRA_CONFIG_AUTH_HEADER="Authorization: Bearer <your-token>"
```

### 优先级 {#precedence}

外部文件最先应用。后面的层会覆盖它：

```text
内置默认值
  < --extra_config_url
    < 全局 pr-agent-settings
      < 本地 .pr_agent.toml（拉取请求目标分支）
        < 环境变量（SECTION__KEY）
```

### 安全与限制 {#security-and-limits}

该文件与仓库 `.pr_agent.toml` 使用同一个加载器。include、preload、自定义加载器，以及其他可能执行代码或读取任意文件的指令都会被拒绝。获取时还会：

- 在 **1 MB** 处停止
- **10 秒**后超时
- 只接受 `http`、`https`、`file` 或裸本地路径

获取失败会被记录。PR-Agent 继续使用其余配置层。外部文件里的主机专用键仍然会被丢弃。
