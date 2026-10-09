---
title: "Local and global metadata injection with multi-stage analysis"
sidebar_position: 6
---

`Supported Git platform: Gitee`

Gitee PR-Agent builds the prompt in layers: the pull request itself, the `/describe` summary, the surrounding file context, and any host or repository instructions. Later commands reuse those layers instead of calling the model again just to recover them. Comments are written in `zh-CN`.

1. For each Gitee pull request it loads:

- Title and branch name
- The existing description
- Commit messages
- The diff, in [hunk](https://loicpefferkorn.net/2014/02/diff-files-what-are-hunks-and-how-to-extract-them/) form
- The full contents of the files the pull request changes
- The title and body of referenced Gitee issues, when the issues API returns them. See [Fetching ticket context](./fetching_ticket_context.md).

:::tip[Repository instructions]
Repository preferences such as [`extra_instructions`](../tools/improve.mdx#extra-instructions-and-repo-files) are added on top of those inputs. They steer suggestions. They do not change the Gitee token, the model endpoint, or `skills.paths`.
:::

2. The first automatic command on an opened pull request is [`/describe`](../tools/describe.md). It produces:

- A pull-request type (bug fix, feature, refactor, and so on)
- A short bullet summary
- A changes walkthrough: one line per modified file, then a short bullet list of what changed

That output becomes pull-request metadata for later `/review` and `/improve` calls. The model can use the walkthrough without another round trip.

When `/improve` suggests a change in a file, the prompt can include that file's walkthrough next to the hunk:

```diff
## File: 'src/file1.py'
### AI-generated file summary:
- edited function `func1` that does X
- Removed function `func2` that was not used
- ....

@@ ... @@ def func1():
__new hunk__
11  unchanged code line0
12  unchanged code line1
13 +new code line2 added
14  unchanged code line3
__old hunk__
 unchanged code line0
 unchanged code line1
-old code line2 removed
 unchanged code line3

@@ ... @@ def func2():
__new hunk__
...
__old hunk__
...
```

3. The full file contents expand the hunk context. See [Dynamic context](./dynamic_context.md).

4. Together these layers run from the hunk, to the file, to the pull request, to repository instructions. `/review` on a diff that does not fit one call segments that metadata across chunks and merges one comment. See [Compression strategy](./compression_strategy.md).
