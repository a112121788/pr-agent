---
title: "相似议题"
sidebar_position: 8
---

## 概述

`/similar_issue` 在 Gitee 上不可用。

Gitee PR-Agent 只接受 Gitee 拉取请求 URL：

- `https://gitee.com/owner/repo/pulls/N`
- `https://e.gitee.com/<enterprise>/repos/owner/repo/pulls/N`

不支持议题索引，因此这条命令不会搜索议题，也不会调用模型。能够发布时，它会发出：

```
The /similar_issue tool is not supported by the configured git provider.
```

评论形式仍然不会搜索：

```
/similar_issue
```

CLI 形式仍然不会搜索：

```bash
ecloud-tcr.tencentcloudcr.com/ecloud_project/pr-agent:latest \
  --issue_url https://gitee.com/owner/repo/issues/N \
  similar_issue
```

`CONFIG__GIT_PROVIDER` 保持为 `gitee`。不要把这条命令指到别的代码托管平台。

`[pr_similar_issue]`、`[pinecone]`、`[lancedb]` 和 `[qdrant]` 下的键在这个构建里不会被使用。
