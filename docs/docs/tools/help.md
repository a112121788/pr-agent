---
title: "Help"
sidebar_position: 9
---

## Overview

`/help` has two forms.

With no question, it posts a comment that lists the commands you can run on the pull request: `/describe`, `/review`, `/improve`, `/ask`, `/add_docs`, `/generate_labels`, and `/update_changelog`.

With a question, it answers from the packaged documentation and posts the answer as a comment, including the doc sections it used.

```
/help
```

```
/help "How do I run /review on a Gitee pull request?"
```

CLI, using the [Gitee image](./index.md#run) and a Gitee pull-request URL:

```bash
ecloud-tcr.tencentcloudcr.com/ecloud_project/pr-agent:latest \
  --pr_url https://gitee.com/owner/repo/pulls/N \
  help "How do I run /review on a Gitee pull request?"
```

Accepted URLs are `https://gitee.com/owner/repo/pulls/N` and `https://e.gitee.com/<enterprise>/repos/owner/repo/pulls/N`.

`/help_docs` is a different command and is [disabled](./help_docs.md). `/similar_issue` does not search Gitee issues; see [Similar issues](./similar_issues.md).
