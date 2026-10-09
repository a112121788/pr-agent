---
title: "Ask"
sidebar_position: 5
---

## Overview

`/ask` answers one question about the pull request, using the diff as context. Ask a specific question.

Comment on the pull request:

```
/ask "Which callers still pass the old argument?"
```

Or pass the same question to the [Gitee CLI image](./index.md#run):

```bash
ecloud-tcr.tencentcloudcr.com/ecloud_project/pr-agent:latest \
  --pr_url https://gitee.com/owner/repo/pulls/N \
  ask "Which callers still pass the old argument?"
```

The URL must be `https://gitee.com/owner/repo/pulls/N` or `https://e.gitee.com/<enterprise>/repos/owner/repo/pulls/N`. Set `CONFIG__GIT_PROVIDER=gitee`, `GITEE__PERSONAL_ACCESS_TOKEN`, `OPENAI__KEY`, and `OPENAI__API_BASE` as shown on the [tools page](./index.md#run).

The answer is a pull-request comment. Its heading comes from `pr_questions.ask_heading` (default `Ask`). The answer language follows `config.response_language` = `zh-CN`.

Each question is independent. Gitee does not keep a thread of earlier `/ask` answers for the next question.

## Ask about lines

If the comment is attached to lines in the diff, the question is answered from those lines plus the surrounding change. Inline comments use Gitee's diff `position`. A question that is not attached to a line uses the whole pull request.

## Configuration

| Key | Default | Effect |
|-----|---------|--------|
| `ask_heading` | `Ask` | Plain-text heading of a top-level answer. |
| `extra_instructions` | empty | Limits or format rules for every answer. |
| `enable_help_text` | `false` | Add help text under the answer. |

```toml
[pr_questions]
ask_heading = "Architecture"
extra_instructions = "Answer in one short paragraph."
```

The same override can sit on the comment:

```
/ask "What does this change do?" --pr_questions.extra_instructions="Answer in one short paragraph."
```
