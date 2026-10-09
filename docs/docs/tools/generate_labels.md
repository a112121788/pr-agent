---
title: "生成标签"
sidebar_position: 7
---

## 概述

`/generate_labels` 读取拉取请求 diff，并打上与变更匹配的标签。它不改写描述。需要摘要时用 [`/describe`](./describe.md)。

在拉取请求上评论：

```
/generate_labels
```

也可以把 `generate_labels` 传给 [Gitee CLI 镜像](./index.md#run)。URL 必须是 `https://gitee.com/owner/repo/pulls/N` 或 `https://e.gitee.com/<enterprise>/repos/owner/repo/pulls/N`。

## 发布内容

标签通过 Gitee API 写入。令牌需要有编辑拉取请求标签的权限。发布会替换整组标签，因此会先读出并保留人工添加的标签。如果这次读取失败，就什么都不发布，避免盲目写入把它们清掉。

命令运行时会发一条临时评论 `正在准备 PR 标签...`，结束后删除。

允许的名字是内置类型 `Bug fix`、`Tests`、`Enhancement`、`Documentation` 和 `Other`，再加上你配置的自定义名字。匹配忽略大小写。未知名字会被丢掉。如果模型只返回未知名字，当前标签保持不变。

## 自定义标签

```toml
[config]
enable_custom_labels = true

[custom_labels."Bug fix"]
description = "A fix for a bug in the codebase"

[custom_labels."sql_changes"]
description = "Use when a PR contains changes to SQL queries"
```

每条说明写成条件，模型才知道什么时候该打这个标签。不再匹配的自定义标签会在下一次 `/generate_labels` 或 `/describe` 时去掉。这组名字之外、由人加上的标签不会被这个过滤清掉。

`/describe` 使用同一组标签，但 `pr_description.publish_labels` 默认为 `false`。单独发布标签的命令是 `/generate_labels`。
