---
title: "管理邮件通知"
sidebar_position: 6
---

PR-Agent 在 Gitee 上发表评论时，Gitee 会通知关注该仓库的人。Gitee 不能在保留其他拉取请求评论邮件的同时，单独关掉某一个机器人用户的邮件。

可以用下面两种方式减少邮件：

- 在 Gitee 里，对安装了 PR-Agent 的仓库关闭拉取请求评论的邮件，如果仍想看到评论，可以保留站内通知。
- 在邮件服务里过滤正文来自 PR-Agent 的邮件（例如按 `PR Reviewer Guide` 或发表评论的机器人账号过滤）。

也可以缩短评论本身。每个工具都有 `enable_help_text`。设为 `false` 会去掉可折叠的帮助段落：

```toml
[pr_reviewer]
enable_help_text = false
```

其他工具如果也不需要帮助文字，在对应的配置节里设置同一个键。仓库级设置写在 [`.pr_agent.toml`](./configuration_options.md#local-configuration-file)。
