---
title: "Help Docs"
sidebar_position: 10
---

:::warning[`/help_docs` is disabled]
`/help_docs` is not registered, so a comment or CLI call does nothing on Gitee. The notes below describe the command as it was specified. Do not rely on it.
:::

## Overview

`/help_docs` was meant to answer a free-text question from a documentation directory in a Git repository.

```
/help_docs "How does authentication work?"
```

The intended defaults live under `[pr_help_docs]`:

| Key | Default | Effect |
|-----|---------|--------|
| `repo_url` | empty | Repository to read. Empty means the repository of the current pull request or issue. |
| `repo_default_branch` | `main` | Branch used when `repo_url` is set. |
| `docs_path` | `docs` | Documentation directory, relative to the repository root. |
| `exclude_root_readme` | `false` | Leave the root README out of the search. |
| `supported_doc_exts` | `.md`, `.mdx`, `.rst` | File types that would be searched. |

Gitee PR-Agent still only accepts `https://gitee.com/owner/repo/pulls/N` and `https://e.gitee.com/<enterprise>/repos/owner/repo/pulls/N` for pull-request commands. This disabled command is not one of them. For questions about these docs, use [`/help`](./help.md). For questions about the pull-request diff, use [`/ask`](./ask.md).
