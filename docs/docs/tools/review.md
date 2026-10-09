---
title: "Review"
sidebar_position: 3
---

## Overview

`/review` gives the reviewer a Chinese assessment of the pull request: findings, tests, security, and review effort. The author who wants code edits should use [`/improve`](./improve.mdx).

Comment on the pull request:

```
/review
```

Or pass `review` to the [Gitee CLI image](./index.md#run). The URL must be `https://gitee.com/owner/repo/pulls/N` or `https://e.gitee.com/<enterprise>/repos/owner/repo/pulls/N`.

An opened pull request runs `/review` with `/describe` and `/improve`, unless `gitee.pr_commands` replaces that list.

```
/review --pr_reviewer.extra_instructions="check the transaction boundaries"
```

## What is published

The comment heading is `pr_reviewer.review_heading`, which defaults to `PR 审查指南`. The body is Chinese because `config.response_language` is `zh-CN`.

`pr_reviewer.persistent_comment` is `true`, so a later full review edits that comment instead of adding another one.

With `pr_reviewer.inline_key_issues` left at `true`, each finding that can be anchored is also posted as an inline comment. Gitee anchors that comment with the diff `position`, counted from the line below the first `@@` hunk header. A finding that cannot be placed stays in the summary.

Two labels are published when the matching switch is on:

- `审查工作量N/5` when `pr_reviewer.enable_review_labels_effort` is `true`. `N` is an integer from 1 to 5. This also needs `pr_reviewer.require_estimate_effort_to_review` (default `true`).
- `可能存在安全问题` when `pr_reviewer.enable_review_labels_security` is `true` and the review reports a security concern. This needs `pr_reviewer.require_security_review` (default `true`).

A later review replaces an older `审查工作量` label. A later review that has a real security verdict removes `可能存在安全问题` when the new verdict is no. Other labels on the pull request are left in place. If the current labels cannot be read, no label update is published, so a failed read cannot wipe labels a person added.

`/review` and `/improve` were run on [eclouddev/hlzs_web#2896](https://gitee.com/eclouddev/hlzs_web/pulls/2896).

## Sections

These switches add or remove sections. Defaults are the values in `pr_agent/settings/configuration.toml`.

| Key | Default | Section |
|-----|---------|---------|
| `require_tests_review` | `true` | Whether the change includes tests. |
| `require_estimate_effort_to_review` | `true` | Effort score used for `审查工作量N/5`. |
| `require_security_review` | `true` | Security note used for `可能存在安全问题`. |
| `require_ticket_analysis_review` | `true` | Ticket compliance, only when ticket context is available. |
| `require_merge_recommendation` | `true` | `safe_to_merge`, `merge_with_caution`, or `changes_required`. |
| `require_score_review` | `false` | Numeric score. |
| `require_can_be_split_review` | `false` | Whether the pull request mixes several themes. |
| `require_estimate_contribution_time_cost` | `false` | Rough author time. |
| `require_todo_scan` | `false` | `TODO` comments in the diff. |
| `require_risk_assessment` | `false` | Overall risk: low, medium, or high. |
| `require_priority_files` | `false` | Files to read first. |

Ticket compliance is a section in the comment, not a label.

## Other options

| Key | Default | Effect |
|-----|---------|--------|
| `extra_instructions` | empty | Project-specific review directions. |
| `num_max_findings` | `3` | Cap on returned findings. |
| `persistent_finding_state` | `true` | Keep finding state across complete reviews so a resolved finding can stay resolved. |
| `max_previous_findings_chars` | `8000` | How much earlier finding text is shown to the model. `0` disables it. |
| `enable_large_pr_chunking` | `true` | Review a diff that does not fit in one call as up to `max_number_of_calls` chunks (default `3`) and merge them. |
| `enable_review_coverage_footer` | `true` | List files the token budget left out. |
| `publish_review_failure_comment` | `true` | Post a failure comment when the review does not complete. |
| `publish_error_details` | `false` | Add a short sanitized reason to a failed manual review. No model call is used for that reason. |
| `final_update_message` | `true` | Add a short note when a persistent review comment is updated. |
| `enable_help_text` | `false` | Add help text to the comment. |

The merged chunk review does not soften a worse chunk: the lowest score, the highest effort, and any security concern are kept.

Use `[pr_reviewer]` in `.pr_agent.toml` for values you want on every run. See [Configuration file](../usage-guide/configuration_options.md).
