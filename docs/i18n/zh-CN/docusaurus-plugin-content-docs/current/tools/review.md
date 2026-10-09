---
title: "审查"
sidebar_position: 3
---

## 概述

生成拉取请求审查，反馈可能的问题、安全顾虑、测试和审查工作量。
<br>
该工具可以在每次新拉取请求[打开](../usage-guide/automations_and_usage.md#github-app-automatic-tools-when-a-new-pr-is-opened)时自动触发，也可以在任意拉取请求上评论来手动调用：

```
/review
```

请注意，`review` 工具的主要目的是向**拉取请求审查者**提供有用的反馈和洞察。相比之下，拉取请求作者可能更希望节省时间，专注于 [improve](./improve.mdx) 工具的输出，后者提供可执行的代码建议。

（关于拉取请求流程中的不同角色，以及 PR-Agent 如何协助他们，详见我们的[博客](https://www.qodo.ai/blog/understanding-the-challenges-and-pain-points-of-the-pull-request-cycle/)）

## 使用示例

### 手动触发

在任意拉取请求上评论 `/review` 来手动调用该工具：

<img src="/img/review_comment.png" alt="审查评论" width="512" />

大约 30 秒后，工具会为该拉取请求生成审查：

<img src="/img/review3.png" alt="审查" width="512" />

如果要编辑[配置](#configuration-options)，把相关项加到命令中：

```
/review --pr_reviewer.some_config1=... --pr_reviewer.some_config2=...
```

### 自动触发

要在拉取请求打开时自动运行 `review`，在[配置文件](../usage-guide/configuration_options.md#local-configuration-file)中定义：

```
[github_app]
pr_commands = [
    "/review",
    ...
]

[pr_reviewer]
extra_instructions = "..."
...
```

- `pr_commands` 列出拉取请求打开时会自动执行的命令。
- `[pr_reviewer]` 节包含你想修改的 `review` 工具配置（如果有）。

## 配置选项 {#configuration-options}

下面的说明解释每个选项的行为。权威默认值见
[`configuration.toml`](https://github.com/the-pr-agent/pr-agent/blob/main/pr_agent/settings/configuration.toml)
中的相关节。

<details open>
<summary>通用选项</summary>

<table>
  <tr>
    <td><b>persistent_comment</b></td>
    <td>设为 true 时，审查评论会持久存在，即每次新的审查请求都会编辑上一条。</td>
  </tr>
  <tr>
    <td><b>publish_review_failure_comment</b></td>
    <td>
      设为 false 可抑制 “Failed to review PR” 评论，包括无法更新持久审查评论的情况。
      成功的审查输出和命令的失败状态不变。默认值为 true。
    </td>
  </tr>
  <tr>
    <td><b>publish_error_details</b></td>
    <td>
      设为 true 时，失败的手动审查评论会为已知的提供方和运行时错误包含一条确定的、已净化的失败原因。
      失败格式化器不会调用 AI 模型，绝不发布原始异常文本，并会回退到通用的内部错误消息。默认值为 false。
    </td>
  </tr>
  <tr>
    <td><b>review_heading</b></td>
    <td>
      审查评论的可见基础标题，不含 Markdown 前缀或增量标签。
      例如，<code>review_heading = "Guideline Compliance Check"</code> 在完整审查中渲染为
      <code>## Guideline Compliance Check 🔍</code>，在增量审查中渲染为
      <code>## Incremental Guideline Compliance Check 🔍</code>。
      在 GitHub、GitLab、Azure DevOps 和 Bitbucket Cloud 上，更改此值会更新同一条持久审查评论；它不会创建单独的审查通道。
    </td>
  </tr>
  <tr>
    <td><b>persistent_finding_state</b></td>
    <td>设为 true 时，PR-Agent 会在完整审查运行之间持久保存结构化的审查发现状态，因此发现可以被解决并重新打开。已解决的发现会保留其描述的原始 Markdown 格式。增量审查和部分审查不会把缺失的发现标为已解决。默认值为 true。</td>

  </tr>
  <tr>
    <td><b>max_previous_findings_chars</b></td>
    <td>先前审查所存储发现的字符预算（需要 <code>persistent_finding_state</code>）。它们会提供给模型，以便模型用先前的措辞重复仍然有效的发现，而不是换一种说法重新提出，并且除非代码重新引入，否则不会重新提出已解决的发现。在 GitLab 上，由 PR-Agent 以外的人解决的行内关键问题讨论会被标为已驳回，并附上最后一条回复，因此除非代码使问题更严重，模型不会重新提出它
  </tr>
  <tr>
  <td><b>final_update_message</b></td>
  <td>设为 true 时，在线评论期间更新持久审查评论会自动在拉取请求中添加一条短评论，并附上指向已更新审查的链接。</td>
  </tr>
  <tr>
    <td><b>extra_instructions</b></td>
    <td>给工具的可选附加指令。例如："focus on the changes in the file X. Ignore change in ..."。</td>
  </tr>
  <tr>
    <td><b>enable_help_text</b></td>
    <td>设为 true 时，工具会在评论中显示帮助文本。</td>
  </tr>
  <tr>
    <td><b>enable_review_coverage_footer</b></td>
    <td>设为 true 时，当令牌预算把文件排除在审查之外时，工具会显示审查覆盖范围页脚。</td>
  </tr>
  <tr>
    <td><b>enable_large_pr_chunking</b></td>
    <td>设为 true 时，如果令牌预算把文件排除在审查之外，diff 会被拆成多个分块，每个分块单独审查，再把各分块结果合并为一次审查。见<a href="#reviewing-a-pr-that-does-not-fit-in-one-call">审查一次调用放不下的拉取请求</a>。默认值为 false。</td>
  </tr>
  <tr>
    <td><b>max_number_of_calls</b></td>
    <td>分块审查调用的最大次数，仅在 <code>enable_large_pr_chunking</code> 为 true 时使用。默认值为 3。</td>
  </tr>
  <tr>
    <td><b>num_max_findings</b></td>
    <td>返回发现的最大数量。</td>
  </tr>
  <tr>
    <td><b>inline_key_issues</b></td>
    <td>设为 true 时，在提供方支持经过验证的行内评论发布（GitHub、Bitbucket Cloud、Azure DevOps、GitLab）的情况下，每个关键问题都会作为行内评论发布。当存在匹配评论或提供方接受新评论时，该发现会离开审查摘要。无法锚定或发布的发现仍留在摘要中。</td>
  </tr>
</table>

</details>

<details open>
<summary>启用或禁用特定子节</summary>

<table>
  <tr>
    <td><b>require_score_review</b></td>
    <td>设为 true 时，工具会添加一个为拉取请求打分的节。</td>
  </tr>
  <tr>
    <td><b>require_tests_review</b></td>
    <td>设为 true 时，工具会添加一个检查拉取请求是否包含测试的节。</td>
  </tr>
  <tr>
    <td><b>require_estimate_effort_to_review</b></td>
    <td>设为 true 时，工具会添加一个估计审查该拉取请求所需工作量的节。</td>
  </tr>
  <tr>
    <td><b>require_estimate_contribution_time_cost</b></td>
    <td>设为 true 时，工具会添加一个节，估计资深开发者创建并提交此类变更所需的时间。</td>
  </tr>
  <tr>
    <td><b>require_can_be_split_review</b></td>
    <td>设为 true 时，工具会添加一个节，检查拉取请求是否包含多个主题，以及是否可以拆成更小的拉取请求。</td>
  </tr>
  <tr>
    <td><b>require_security_review</b></td>
    <td>设为 true 时，工具会添加一个节，检查拉取请求是否包含可能的安全或漏洞问题。</td>
  </tr>
    <tr>
    <td><b>require_todo_scan</b></td>
    <td>设为 true 时，工具会添加一个节，列出在拉取请求代码变更中找到的 TODO 注释。
    </td>
  </tr>
  <tr>
    <td><b>require_ticket_analysis_review</b></td>
    <td>
      设为 true 且工单上下文可用时，工具会在审查评论中添加工单符合性节，
      检查拉取请求是否满足工单要求。支持的来源包括 GitHub 和 GitLab 议题、
      已链接的 Azure DevOps 工作项、Jira Cloud 工单和 Asana 任务。
    </td>
  </tr>
  <tr>
    <td><b>require_risk_assessment</b></td>
    <td>设为 true 时，工具会添加一个节，把拉取请求的总体风险评为低、中或高。</td>
  </tr>
  <tr>
    <td><b>require_merge_recommendation</b></td>
    <td>设为 true 时，工具会添加一个节，给出 safe_to_merge、merge_with_caution 或 changes_required 的合并建议。</td>
  </tr>
  <tr>
    <td><b>require_priority_files</b></td>
    <td>设为 true 时，工具会添加一个节，列出人工审查者应优先检查的文件。</td>
  </tr>
</table>

</details>

<details open>
<summary>添加拉取请求标签</summary>

可以启用或禁用 `review` 工具向拉取请求添加特定标签：

<table>
  <tr>
    <td><b>enable_review_labels_security</b></td>
    <td>设为 true 时，如果检测到安全问题，工具会发布 “possible security issue” 标签。</td>
  </tr>
  <tr>
    <td><b>enable_review_labels_effort</b></td>
    <td>设为 true 时，工具会发布 “Review effort x/5” 标签（1–5 分制）。</td>
  </tr>
</table>

</details>

## 使用提示

### 一般准则

:::tip

`review` 工具提供一组可配置的拉取请求反馈。
建议查看[配置选项](#configuration-options)一节，并为你的用例选择相关选项。

一些默认禁用的功能相当有用，应当考虑启用。例如：
`require_score_review` 等。

另一方面，如果发现某个已启用的功能与你的用例无关，就禁用它。没有任何默认配置能适合所有用例。
:::

### 自动化

:::tip
首次安装 PR-Agent 应用时，`review` 工具的[默认模式](../usage-guide/automations_and_usage.md#github-app-automatic-tools-when-a-new-pr-is-opened)是：
```
pr_commands = ["/review", ...]
```
意味着 `review` 工具会在每个拉取请求上自动运行，无需任何额外配置。
编辑此字段以启用/禁用该工具，或更改所使用的配置。
:::

### 审查工具自动生成的拉取请求标签

:::tip

`review` 工具可以自动为拉取请求添加标签：

- **`possible security issue`**：如果工具在拉取请求代码中检测到潜在的[安全漏洞](https://github.com/the-pr-agent/pr-agent/blob/main/pr_agent/settings/pr_reviewer_prompts.toml#L134)，就会应用此标签。此反馈由 “enable_review_labels_security” 标志控制（默认值为 true）。
- **`review effort [x/5]`**：此标签在 1 到 5 的相对尺度上估计审查该拉取请求所需的[工作量](https://github.com/the-pr-agent/pr-agent/blob/main/pr_agent/settings/pr_reviewer_prompts.toml#L118)，其中 “x” 表示评估出的工作量。此反馈由 “enable_review_labels_effort” 标志控制（默认值为 true）。

工单符合性写在审查评论中，而不是作为拉取请求标签。它由
`pr_reviewer.require_ticket_analysis_review` 控制，并且需要可用的工单上下文。该工具不会添加
工单符合性标签或 “No ticket found” 标签。链接和认证细节见
[获取工单上下文](../core-abilities/fetching_ticket_context.md)。


### 根据生成的标签自动阻止拉取请求合并

:::tip

可以配置 CI/CD Action 来阻止合并带有特定标签的拉取请求。例如，实现一个专用的 [GitHub Action](https://medium.com/sequra-tech/quick-tip-block-pull-request-merge-using-labels-6cc326936221)。

这种方法有助于确保存在潜在安全问题的拉取请求不会在未经进一步审查的情况下被合并。

由于 AI 可能出错或缺少完整上下文，请审慎使用此功能。为了灵活起见，具有相应权限的用户可以在必要时移除生成的标签。标签被移除时，此操作会自动记录在拉取请求讨论中，明确表示这是授权用户为允许合并而做出的有意覆盖。
:::

### 附加指令

:::tip

附加指令很重要。
可以为 `review` 工具配置附加指令，用来引导模型给出符合项目需求的反馈。

指令要具体、清楚、简洁。使用附加指令时，你就是提示词的作者。指明相关子工具，以及你想强调的拉取请求相关方面。

附加指令示例：
```
[pr_reviewer]
extra_instructions="""\
In the code feedback section, emphasize the following:
- Does the code logic cover relevant edge cases?
- Is the code logic clear and easy to understand?
- Is the code logic efficient?
...
"""
```
使用三引号编写多行指令。使用项目符号让指令更易读。
:::

### 审查一次调用放不下的拉取请求 {#reviewing-a-pr-that-does-not-fit-in-one-call}

:::tip

当拉取请求 diff 大于模型的令牌预算时，`review` 工具会丢弃整个文件，
直到 diff 能够放下，并在审查覆盖范围页脚中列出被丢弃的文件。

设置 `enable_large_pr_chunking = true` 会改变后续行为：diff 会被拆成最多
`max_number_of_calls` 个分块，每个分块单独审查，再把回答合并为一次审查，并说明它由多少个分块构成。即使分块之后仍然放不下的文件，仍会列在覆盖范围页脚中。每个分块都是一次独立的模型调用，
因此分块审查的成本大约是普通审查的 `max_number_of_calls` 倍。

分块运行期间，临时评论 `Preparing review...` 会就地改写，带上
已经分析的分块数，例如 `Preparing review... analyzed 2 of 3 chunks`，当分块放弃时还会加上
`... 1 chunk failed`。更新需要
`config.publish_output_progress`，以及同时支持编辑和删除评论的提供方，因此纯 diff 运行会保留冻结的占位符。自动命令不发布进度评论，但在启用 `github.publish_as_check_run` 时，其进行中的 check run 会显示相同的分块计数。该评论保持
临时状态，并仍会在合并后的审查发布之前被移除。回退模型会在开始之前恢复
占位符，因此可见计数绝不会倒退。

如果某个分块失败或返回格式错误的输出，成功的分块会被保留，回退模型只重试尚未完成的工作。待处理分块可以在调用次数限制内为更小的模型再拆分；更大的模型也可以包含先前省略的文件。仍然超出模型预算的分块不会发送给它。

如果所有回退都已耗尽，成功的分块会作为部分审查发布，并带有分块失败的覆盖范围警告，即使 `publish_output_no_suggestions = false` 也是如此。不完整的审查不能把缺失的持久发现标为已解决。如果没有任何分块成功，审查失败。
当 `config.propagate_tool_errors = true` 时，耗尽的回退链在发布部分审查并移除进度评论之后，仍会向调用方发出失败信号。
可选的运行细节会列出所有对合并审查有贡献的模型。

每个分块针对拉取请求的不同部分回答相同的问题，因此回答会按字段合并：

| 字段 | 合并规则 |
| --- | --- |
| `key_issues_to_review` | 对各分块取并集，丢弃文件、标题和文本都相同的重复发现 |
| `security_concerns` | 保留每个报告了顾虑的分块；只有每个分块都说没有时才为 “No” |
| `todo_sections`、`review_priority_files`、`can_be_split` | 取并集、去重，按分块顺序（`can_be_split` 最多保留 3 个子拉取请求） |
| `relevant_tests` | 任一分块发现测试则为 Yes |
| `score` | 任一分块给出的最低分 |
| `risk_level`、`merge_recommendation` | 任一分块给出的最保守值 |
| `estimated_effort_to_review_[1-5]` | 任一分块给出的最高值 |
| `contribution_time_cost_estimate` | 按情况对各分块求和 |
| `ticket_compliance_check` | 每个工单一条，其项目符号列表在各分块间取并集 |

合并后的结论刻意不会比最差的分块更不令人警惕：一个干净的分块
不能抬高分数、消除安全顾虑，或缓和另一个分块设定的风险等级。
:::
