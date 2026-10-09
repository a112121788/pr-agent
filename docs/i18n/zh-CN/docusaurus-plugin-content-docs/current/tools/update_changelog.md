---
title: "更新变更日志"
sidebar_position: 11
---

## 概述

`update_changelog` 工具会根据拉取请求变更自动更新 CHANGELOG.md。
可以在任意拉取请求上评论来手动调用：

```
/update_changelog
```

## 使用示例

<img src="/img/update_changelog_comment.png" alt="update_changelog_comment" width="768" />

<img src="/img/update_changelog.png" alt="update_changelog" width="768" />

## 配置选项

在 `pr_update_changelog` 节下，[配置文件](https://github.com/the-pr-agent/pr-agent/blob/main/pr_agent/settings/configuration.toml)包含用于自定义 “update changelog” 工具的选项：

- `push_changelog_changes`：是把变更推送到 CHANGELOG.md，还是只作为评论发布。默认值为 false（作为评论发布）。推送之前，工具需要已确认读到现有的 CHANGELOG.md；确认文件缺失时视为空文件，其他读取失败则会跳过仓库写入，尝试发布一条未推送的回退评论，并抛出原始错误。如果仓库写入本身失败，工具会尽最大努力尝试发布
- `extra_instructions`：给工具的可选附加指令。例如："Use the following structure: ..."
- `add_pr_link`：模型是否应尝试在变更日志中加入指向该拉取请求的链接。默认值为 true。
- `skip_ci_on_push`：当 `push_changelog_changes` 为 true 时，提交消息是否包含 “[skip ci]”，从而避免变更日志提交触发 CI 测试。默认值为 true。
