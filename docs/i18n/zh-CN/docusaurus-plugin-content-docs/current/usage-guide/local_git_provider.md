---
title: "本地 Git 提供商"
sidebar_position: 13
---

当没有托管的 GitHub、GitLab 或 Bitbucket 拉取/合并请求时，使用 `local` Git 提供商从本地 Git 检出运行 PR-Agent。它把本地分支比较视为类似拉取请求的变更，并把结果写入检出目录中的文件。

本页介绍分支对分支的本地审查。若要在本地针对已有的托管 PR/MR 运行 PR-Agent，请按照[从源码运行](../installation/locally.md#run-from-source)，并改为配置该托管提供商。

## 适用场景 {#when-to-use-it}

本地 Git 提供商适用于：

- 本地试验
- 没有托管 PR/MR 的工作流
- 直接在本地 Git 检出上运行的 CI 作业

## 工作原理 {#how-it-works}

- 当前 `HEAD` 是提议的变更。
- PR-Agent 计算当前 `HEAD` 与「`HEAD` 和所给本地目标分支的合并基线」之间的 diff。

共享 CLI 为了与其他提供商兼容，仍保留 `--pr_url` 这个选项名。当 `git_provider=local` 时，传入本地目标分支名，例如 `main`，而不是托管 PR/MR 的 URL。

## 前提条件 {#prerequisites}

运行命令之前：

- 在包含提议变更的 Git 仓库内运行。
- 保持工作树干净。用 `git status --short` 检查；该命令比较的是已提交的 `HEAD` 内容。
- 确保目标分支在本地存在，例如用 `git branch --list main`。
- 配置你的环境所需要的 LLM 提供商。此模式不需要托管 Git 提供商的令牌。

## 基本用法 {#basic-usage}

CLI 命令名为 `review`、`describe` 和 `improve`；它们分别对应 `/review`、`/describe` 和 `/improve` 工具。

针对本地 `main` 分支运行 `/review`：

```bash
cd /path/to/repository
CONFIG__GIT_PROVIDER=local \
python -m pr_agent.cli --pr_url main review
```

运行 `/describe`：

```bash
CONFIG__GIT_PROVIDER=local \
python -m pr_agent.cli --pr_url main describe
```

运行 `/improve`：

```bash
CONFIG__GIT_PROVIDER=local \
python -m pr_agent.cli --pr_url main improve
```

把 `main` 换成要作为目标的本地分支。

## 输出文件 {#output-files}

默认情况下，这些命令把文件写到仓库根目录：

- `/review` 命令写入 `review.md`。
- `/describe` 命令写入 `description.md`。
- `/improve` 命令写入 `improve.md`。

本地提供商写入这些文件，而不是把结果发布到托管的拉取/合并请求。

## 自定义输出路径 {#custom-output-paths}

在本次运行所使用的配置中设置路径，例如仓库根目录的 `.pr_agent.toml`：

```toml
[local]
review_path = "artifacts/review.md"
description_path = "artifacts/description.md"
improve_path = "artifacts/improve.md"
```

使用相对的自定义路径时，请像上面那样从仓库根目录运行 PR-Agent。

运行命令之前，请先为自定义路径创建所有父目录。

## 限制 {#limitations}

本地 Git 提供商不能发布到托管平台：它不会发布托管 PR 评论、应用标签、添加反应，也不会发布行内评论。

PR-Agent 仍然需要已配置的 LLM 提供商，这可能需要网络访问。
