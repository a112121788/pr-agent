---
title: "FAQ"
sidebar_position: 1
---

<details>
<summary>Q: Can Gitee PR-Agent replace a human reviewer?</summary>

#### Answer:<span style="display:none;">1</span>

No. It assists the author and the reviewer. It does not approve a Gitee pull request.

Long pull requests are where that help matters most: reviewers spend less time per line as the diff grows. Gitee PR-Agent still leaves the decision with the people on the pull request:

1. It keeps the original title.
2. It places the author's description above the generated description.
3. It does not approve. Approval stays with a reviewer.
4. Code suggestions are optional. They are there to surface bugs, oversights, and project conventions, not to commit themselves.

An opened pull request runs `/describe`, `/review`, and `/improve`. Comment on the pull request to run a tool again. See the [Gitee installation guide](../installation/gitee.md) and [online usage](../usage-guide/automations_and_usage.md#online-usage).

</details>

___

<details>
<summary>Q: I received an incorrect or irrelevant suggestion. Why?</summary>

#### Answer:<span style="display:none;">2</span>

- The default model is `gpt-6.1-sol`, with `glm-5.3` as the fallback. Both still make mistakes. Read the suggestion before applying it. Comments are written in `zh-CN`.
- The useful case is a suggestion that catches a mistake in the diff. Spending half a minute on the list is usually worth it, even when some items do not apply.
- `/improve` scores its own list and drops items it marks as wrong. See [Self-reflection](../core-abilities/self_reflection.md).
- The comment is hierarchical on purpose. Read the category, then the one-line summary, and open the suggestion only if that summary is relevant.
- Use [`extra_instructions`](../tools/improve.mdx#extra-instructions-and-repo-files) to tell the model what this repository cares about.

</details>

___

<details>
<summary>Q: How can I get more tailored suggestions?</summary>

#### Answer:<span style="display:none;">3</span>

Set `extra_instructions` and best-practice text for the repository. See [Extra instructions and best practices](../tools/improve.mdx#extra-instructions-and-repo-files).

Host-level [agent skills](../core-abilities/agent_skills.md) apply the same kind of guidance across Gitee repositories. A repository cannot point `skills.paths` at the host filesystem.

</details>

___

<details>
<summary>Q: Will you store my code or train on it?</summary>

#### Answer:<span style="display:none;">4</span>

This build does not keep pull-request content for training. Prompts are sent to the model endpoint you configure (`gpt-6.1-sol`, then `glm-5.3` on fallback).

See [Data privacy](../overview/data_privacy.md).

</details>

___

<details>
<summary>Q: How are large pull requests reviewed?</summary>

#### Answer:<span style="display:none;">5</span>

They are segmented by default.

- `/review` sets `enable_large_pr_chunking = true` and uses at most `max_number_of_calls` (default 3) chunk calls, then merges one comment.
- `/describe` sets `enable_large_pr_handling = true` and combines further calls so more files are covered.

Files that still do not fit are named in the review coverage footer. The primary model is `gpt-6.1-sol`; a failed chunk can fall over to `glm-5.3`. Details are in [Compression strategy](../core-abilities/compression_strategy.md) and [Other options](../tools/review.md#other-options).

</details>

___

<details>
<summary>Q: Where do inline comments attach?</summary>

#### Answer:<span style="display:none;">6</span>

Gitee anchors an inline comment with a diff `position`: the line index counted from the line below the first `@@` hunk header in that file's patch. Gitee PR-Agent computes that index from the pull-request diff. If the file or line cannot be mapped, the comment is not posted.

See [Verified behavior](../installation/gitee.md#verified-behavior) in the Gitee installation guide.

</details>

___

<details>
<summary>Q: A referenced Gitee issue was ignored. Why?</summary>

#### Answer:<span style="display:none;">7</span>

Issue reading is implemented. The pull request can point at an issue with a Gitee issue URL, `owner/repo#number`, `#number`, or a branch name such as `123-fix-bug`. The command then calls `GET /repos/{owner}/{repo}/issues/{number}`.

Some enterprise repositories return HTTP 404 from that API even when the issue page loads in the browser. The issue is skipped, and `/describe` and `/review` continue without its title and body. Paste the requirements into the pull-request description if you still want them in the prompt.

See [Fetching ticket context](../core-abilities/fetching_ticket_context.md).

</details>

___

<details>
<summary>Q: Can the review-effort score be calibrated?</summary>

#### Answer:<span style="display:none;">8</span>

Yes. `pr_reviewer.extra_instructions` can describe what each level means for your team. See [Other options](../tools/review.md#other-options).

Example:

- Effort 1: under 30 minutes
- Effort 2: 30–60 minutes
- Effort 3: 60–90 minutes

The 1–5 score is comparative. It is there so smaller pull requests can be reviewed first. It is not a timer.

</details>

___

<details>
<summary>Q: How do I reduce noise?</summary>

#### Answer:<span style="display:none;">9</span>

The defaults are already trimmed:

- An opened pull request runs three structured tools, `/describe`, `/review`, and `/improve`, not a stream of status comments.
- `/improve` suggestions are a table. A suggestion is not posted inline unless a Gitee diff `position` is found.
- The file walkthrough is folded.
- Large diffs become one merged review, not one comment per file. See [Compression strategy](../core-abilities/compression_strategy.md).

If that is still too much for one repository:

- Raise the [suggestion score threshold](../tools/improve.mdx#configuration).
- Narrow the model with [`extra_instructions`](../tools/improve.mdx#extra-instructions-and-repo-files).
- Set `gitee.pr_commands` to `[]` to stop the automatic tools. Comment commands that start with `/` still run. See [Automatic feedback](../usage-guide/automations_and_usage.md#pr-agent-automatic-feedback).

To keep automatic review but make suggestions easier to apply, see [what is published](../tools/improve.mdx#what-is-published) and [how many suggestions](../tools/improve.mdx#how-many-suggestions).

</details>

___
