---
title: "管理邮件通知"
sidebar_position: 6
---


很遗憾，GitHub 无法关闭来自特定用户的邮件通知。
如果你订阅了启用 PR-Agent 的仓库通知，建议关闭拉取请求评论的通知，以避免收到冗长邮件：

<img src="/img/notifications.png" alt="通知" width="512" />

也可以在邮件服务商中专门过滤来自 PR-Agent 机器人的通知，[查看方法](https://www.quora.com/How-can-you-filter-emails-for-specific-people-in-Gmail#:~:text=On%20the%20Filters%20and%20Blocked,the%20body%20of%20the%20email)。

<img src="/img/filter_mail_notifications.png" alt="过滤邮件通知" width="512" />

另一种减轻邮件负担、同时仍接收 PR-Agent 工具通知的做法，是关闭 PR-Agent 机器人评论中的帮助折叠区域。
可以在配置文件中为相应工具设置 `enable_help_text=false`。
例如，要关闭 `pr_reviewer` 工具的帮助文本，设置：

```
[pr_reviewer]
enable_help_text = false
```
