---
title: "Update Changelog"
sidebar_position: 11
---

## Overview

`/update_changelog` drafts a changelog entry from the pull request. On Gitee the draft is published as a comment. The command cannot push `CHANGELOG.md` or any other file.

Comment on the pull request:

```
/update_changelog
```

Or pass `update_changelog` to the [Gitee CLI image](./index.md#run). The URL must be `https://gitee.com/owner/repo/pulls/N` or `https://e.gitee.com/<enterprise>/repos/owner/repo/pulls/N`.

## Why it does not push

Gitee's API used by this build cannot write repository files, so the `push_code` capability is off. `pr_update_changelog.push_changelog_changes` defaults to `false`. Setting it to `true` still does not create a commit. The entry stays in the comment.

The comment can include a stock note that tells you to enable `pr_update_changelog.push_changelog_changes`. That note does not apply on Gitee. Copy the entry into `CHANGELOG.md` yourself if you want it in the branch.

When Gitee returns the current `CHANGELOG.md`, that text is used as context for the draft. `pr_update_changelog.add_pr_link` defaults to `true`, so the draft tries to link the pull request. `pr_update_changelog.skip_ci_on_push` has no effect, because nothing is pushed.

## Configuration

```toml
[pr_update_changelog]
extra_instructions = "Use Added, Fixed, and Changed."
add_pr_link = true
push_changelog_changes = false
```

| Key | Default | Effect on Gitee |
|-----|---------|-----------------|
| `push_changelog_changes` | `false` | Cannot push. The result is still a comment. |
| `add_pr_link` | `true` | Ask the model to link the pull request. |
| `extra_instructions` | empty | Structure or wording for the entry. |
| `skip_ci_on_push` | `true` | Unused, because no commit is created. |

```
/update_changelog --pr_update_changelog.extra_instructions="Write one bullet."
```
