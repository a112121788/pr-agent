---
title: "提问"
sidebar_position: 5
---

## 概述

`/ask` 根据 diff 回答一个关于该拉取请求的问题。问题要具体。

在拉取请求上评论：

```
/ask "Which callers still pass the old argument?"
```

也可以把同一个问题传给 [Gitee CLI 镜像](./index.md#run)：

```bash
ecloud-tcr.tencentcloudcr.com/ecloud_project/pr-agent:latest \
  --pr_url https://gitee.com/owner/repo/pulls/N \
  ask "Which callers still pass the old argument?"
```

URL 必须是 `https://gitee.com/owner/repo/pulls/N` 或 `https://e.gitee.com/<enterprise>/repos/owner/repo/pulls/N`。按[工具页](./index.md#run)设置 `CONFIG__GIT_PROVIDER=gitee`、`GITEE__PERSONAL_ACCESS_TOKEN`、`OPENAI__KEY` 和 `OPENAI__API_BASE`。

回答是一条拉取请求评论。标题来自 `pr_questions.ask_heading`（默认 `Ask`）。回答语言遵循 `config.response_language` = `zh-CN`。

每个问题互相独立。Gitee 不会把之前的 `/ask` 回答保留成下一次提问的会话。

## 针对代码行提问

如果评论挂在 diff 的某些行上，问题会根据这些行以及周围的变更来回答。行内评论使用 Gitee diff 的 `position`。没有挂到行上的问题使用整个拉取请求。

## 配置

| 键 | 默认值 | 作用 |
|----|--------|------|
| `ask_heading` | `Ask` | 顶层回答的纯文本标题。 |
| `extra_instructions` | 空 | 对所有回答的限制或格式要求。 |
| `enable_help_text` | `false` | 在回答下加帮助文字。 |

```toml
[pr_questions]
ask_heading = "Architecture"
extra_instructions = "Answer in one short paragraph."
```

同样的覆盖可以写在评论上：

```
/ask "What does this change do?" --pr_questions.extra_instructions="Answer in one short paragraph."
```
