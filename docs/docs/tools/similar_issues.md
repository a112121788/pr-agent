---
title: "Similar Issues"
sidebar_position: 8
---

## Overview

`/similar_issue` is not available on Gitee.

Gitee PR-Agent only accepts Gitee pull-request URLs:

- `https://gitee.com/owner/repo/pulls/N`
- `https://e.gitee.com/<enterprise>/repos/owner/repo/pulls/N`

Issue indexing is not supported, so the command does not search issues and does not call the model. When it can publish, it posts:

```
The /similar_issue tool is not supported by the configured git provider.
```

Comment form, which still does not search:

```
/similar_issue
```

CLI form, which still does not search:

```bash
ecloud-tcr.tencentcloudcr.com/ecloud_project/pr-agent:latest \
  --issue_url https://gitee.com/owner/repo/issues/N \
  similar_issue
```

`CONFIG__GIT_PROVIDER` stays `gitee`. Do not point this command at another forge.

Keys under `[pr_similar_issue]`, `[pinecone]`, `[lancedb]`, and `[qdrant]` are unused on this build.
