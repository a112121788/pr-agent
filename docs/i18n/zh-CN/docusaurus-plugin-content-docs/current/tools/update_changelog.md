---
title: "更新变更日志"
sidebar_position: 11
---

## 概述

`/update_changelog` 根据拉取请求起草一条变更日志。在 Gitee 上，草稿以评论发布。这条命令不能推送 `CHANGELOG.md` 或任何其他文件。

在拉取请求上评论：

```
/update_changelog
```

也可以把 `update_changelog` 传给 [Gitee CLI 镜像](./index.md#run)。URL 必须是 `https://gitee.com/owner/repo/pulls/N` 或 `https://e.gitee.com/<enterprise>/repos/owner/repo/pulls/N`。

## 为什么不能推送

这个构建使用的 Gitee API 不能写仓库文件，因此 `push_code` 能力是关闭的。`pr_update_changelog.push_changelog_changes` 默认为 `false`。把它设为 `true` 仍然不会产生提交。条目留在评论里。

评论里可能带一段固定说明，让你打开 `pr_update_changelog.push_changelog_changes`。这段说明在 Gitee 上不起作用。如果要把条目放进分支，请自己复制到 `CHANGELOG.md`。

当 Gitee 返回当前的 `CHANGELOG.md` 时，这段文字会作为草稿的上下文。`pr_update_changelog.add_pr_link` 默认为 `true`，草稿会尝试链接该拉取请求。`pr_update_changelog.skip_ci_on_push` 没有效果，因为不会产生提交。

## 配置

```toml
[pr_update_changelog]
extra_instructions = "Use Added, Fixed, and Changed."
add_pr_link = true
push_changelog_changes = false
```

| 键 | 默认值 | 在 Gitee 上的效果 |
|----|--------|-------------------|
| `push_changelog_changes` | `false` | 不能推送。结果仍然是评论。 |
| `add_pr_link` | `true` | 让模型链接该拉取请求。 |
| `extra_instructions` | 空 | 条目的结构或措辞。 |
| `skip_ci_on_push` | `true` | 未使用，因为不会创建提交。 |

```
/update_changelog --pr_update_changelog.extra_instructions="Write one bullet."
```
