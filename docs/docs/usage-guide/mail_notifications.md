---
title: "Managing Mail Notifications"
sidebar_position: 6
---

Gitee notifies watchers when PR-Agent publishes a comment. Gitee does not provide a switch that silences one bot user while leaving every other pull-request comment in your inbox.

Reduce the mail in either of these ways:

- In Gitee, turn off email for pull-request comments on repositories where PR-Agent is installed, and keep the in-site notification if you still want to see the comment.
- In your mail provider, filter messages whose body is a PR-Agent comment (for example a filter on `PR Reviewer Guide` or the bot account that posts the comment).

You can also shorten the comment itself. Each tool has `enable_help_text`. Set it to `false` to drop the collapsible help block:

```toml
[pr_reviewer]
enable_help_text = false
```

Apply the same key under the section of any other tool whose help text you do not want mailed. Repository settings go in [`.pr_agent.toml`](./configuration_options.md#local-configuration-file).
