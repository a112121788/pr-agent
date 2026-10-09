---
title: "帮助"
sidebar_position: 9
---

## 概述

`/help` 有两种用法。

不带问题时，它会发一条评论，列出可以在该拉取请求上运行的命令：`/describe`、`/review`、`/improve`、`/ask`、`/add_docs`、`/generate_labels` 和 `/update_changelog`。

带上问题时，它根据随包文档作答，并把答案发成评论，同时附上用到的文档段落。

```
/help
```

```
/help "How do I run /review on a Gitee pull request?"
```

CLI 使用 [Gitee 镜像](./index.md#run) 和一条 Gitee 拉取请求 URL：

```bash
ecloud-tcr.tencentcloudcr.com/ecloud_project/pr-agent:latest \
  --pr_url https://gitee.com/owner/repo/pulls/N \
  help "How do I run /review on a Gitee pull request?"
```

接受的 URL 是 `https://gitee.com/owner/repo/pulls/N` 和 `https://e.gitee.com/<enterprise>/repos/owner/repo/pulls/N`。

`/help_docs` 是另一条命令，而且已经[禁用](./help_docs.md)。`/similar_issue` 不会搜索 Gitee 议题，见[相似议题](./similar_issues.md)。
