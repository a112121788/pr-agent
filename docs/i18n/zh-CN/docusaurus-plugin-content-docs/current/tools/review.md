---
title: "审查"
sidebar_position: 3
---

## 概述

`/review` 给审查者一份中文评估：发现的问题、测试、安全和审查工作量。想直接改代码的作者应使用 [`/improve`](./improve.mdx)。

在拉取请求上评论：

```
/review
```

也可以把 `review` 传给 [Gitee CLI 镜像](./index.md#run)。URL 必须是 `https://gitee.com/owner/repo/pulls/N` 或 `https://e.gitee.com/<enterprise>/repos/owner/repo/pulls/N`。

拉取请求打开时会和 `/describe`、`/improve` 一起运行 `/review`，除非 `gitee.pr_commands` 换掉这份列表。

```
/review --pr_reviewer.extra_instructions="check the transaction boundaries"
```

## 发布内容

评论标题来自 `pr_reviewer.review_heading`，默认是 `PR 审查指南`。正文是中文，因为 `config.response_language` 为 `zh-CN`。

`pr_reviewer.persistent_comment` 为 `true`，因此下一次完整审查会编辑这条评论，而不是再发一条。

`pr_reviewer.inline_key_issues` 保持 `true` 时，每个能定位的发现还会发成行内评论。Gitee 用 diff 的 `position` 锚定评论，从第一个 `@@` hunk 头的下一行开始计数。无法定位的发现留在摘要里。

两个开关打开时会发布这些标签：

- `pr_reviewer.enable_review_labels_effort` 为 `true` 时发布 `审查工作量N/5`。`N` 是 1 到 5 的整数。这还需要 `pr_reviewer.require_estimate_effort_to_review`（默认 `true`）。
- `pr_reviewer.enable_review_labels_security` 为 `true` 且审查发现安全问题时发布 `可能存在安全问题`。这需要 `pr_reviewer.require_security_review`（默认 `true`）。

之后的审查会换掉旧的 `审查工作量` 标签。之后的审查若给出了明确的安全结论，且结论是没有问题，会去掉 `可能存在安全问题`。拉取请求上的其他标签保持不动。如果读不到当前标签，就不会发布标签更新，避免一次失败的读取清掉人工添加的标签。

`/review` 和 `/improve` 已在 [eclouddev/hlzs_web#2896](https://gitee.com/eclouddev/hlzs_web/pulls/2896) 上运行过。

## 段落

这些开关用来增减段落。默认值就是 `pr_agent/settings/configuration.toml` 里的值。

| 键 | 默认值 | 段落 |
|----|--------|------|
| `require_tests_review` | `true` | 变更是否包含测试。 |
| `require_estimate_effort_to_review` | `true` | 用于 `审查工作量N/5` 的工作量分。 |
| `require_security_review` | `true` | 用于 `可能存在安全问题` 的安全说明。 |
| `require_ticket_analysis_review` | `true` | 工单符合度。仅在有工单上下文时出现。 |
| `require_merge_recommendation` | `true` | `safe_to_merge`、`merge_with_caution` 或 `changes_required`。 |
| `require_score_review` | `false` | 数字评分。 |
| `require_can_be_split_review` | `false` | 拉取请求是否混了多个主题。 |
| `require_estimate_contribution_time_cost` | `false` | 粗略的作者耗时。 |
| `require_todo_scan` | `false` | diff 里的 `TODO` 注释。 |
| `require_risk_assessment` | `false` | 总体风险：low、medium 或 high。 |
| `require_priority_files` | `false` | 建议先读的文件。 |

工单符合度是评论里的一段，不是标签。

## 其他选项

| 键 | 默认值 | 作用 |
|----|--------|------|
| `extra_instructions` | 空 | 针对本仓库的审查说明。 |
| `num_max_findings` | `3` | 返回发现的上限。 |
| `persistent_finding_state` | `true` | 在完整审查之间保留发现状态，已解决的发现可以继续保持解决。 |
| `max_previous_findings_chars` | `8000` | 展示给模型的历史发现文本量。`0` 表示关闭。 |
| `enable_large_pr_chunking` | `true` | 一次调用放不下的 diff 最多拆成 `max_number_of_calls` 块（默认 `3`）再合并。 |
| `enable_review_coverage_footer` | `true` | 列出令牌预算没覆盖的文件。 |
| `publish_review_failure_comment` | `true` | 审查没有完成时发布失败评论。 |
| `publish_error_details` | `false` | 在失败的手动审查里附加一段经过清理的原因。这段原因不会再调用模型。 |
| `final_update_message` | `true` | 持久审查评论被更新时加一条短通知。 |
| `enable_help_text` | `false` | 在评论里加帮助文字。 |

合并后的分块审查不会比最差的一块更温和：最低分、最高工作量和任何安全问题都会保留。

想让每次运行都带上的值，写进 `.pr_agent.toml` 的 `[pr_reviewer]`。参见[配置文件](../usage-guide/configuration_options.md)。
