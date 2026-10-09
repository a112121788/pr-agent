---
title: "文档帮助"
sidebar_position: 10
---

:::warning[`/help_docs` 已禁用]
`/help_docs` 没有注册，因此在 Gitee 上评论或调用 CLI 都没有效果。下面记录的是这条命令原先的设定。不要依赖它。
:::

## 概述

`/help_docs` 原意是根据某个 Git 仓库里的文档目录，回答一段自由文本问题。

```
/help_docs "How does authentication work?"
```

原先的默认值在 `[pr_help_docs]` 下：

| 键 | 默认值 | 作用 |
|----|--------|------|
| `repo_url` | 空 | 要读取的仓库。空表示当前拉取请求或议题所在的仓库。 |
| `repo_default_branch` | `main` | 设置了 `repo_url` 时使用的分支。 |
| `docs_path` | `docs` | 文档目录，相对于仓库根目录。 |
| `exclude_root_readme` | `false` | 搜索时排除根目录 README。 |
| `supported_doc_exts` | `.md`、`.mdx`、`.rst` | 会搜索的文件类型。 |

Gitee PR-Agent 的拉取请求命令仍然只接受 `https://gitee.com/owner/repo/pulls/N` 和 `https://e.gitee.com/<enterprise>/repos/owner/repo/pulls/N`。这条已禁用的命令不在其中。问这些文档，用 [`/help`](./help.md)。问拉取请求 diff，用 [`/ask`](./ask.md)。
