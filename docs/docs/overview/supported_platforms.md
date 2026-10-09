---
title: "Supported platforms"
sidebar_position: 3
---

Gitee PR-Agent supports Gitee only. Configure the token, webhook, and Docker service with the [Gitee installation guide](../installation/gitee.md).

The CLI accepts a Gitee pull-request URL, for example `https://gitee.com/<owner>/<repo>/pulls/<number>`.

Defaults for that review:

- Model `gpt-6.1-sol`, fallback `glm-5.3`. See [Changing a model](../usage-guide/changing_a_model.md).
- Response language `zh-CN`.
- Large pull requests are segmented. See [Compression strategy](../core-abilities/compression_strategy.md).
- Inline comments use Gitee's diff `position`.

GitHub, GitLab, Bitbucket, Azure DevOps, Gitea, Gerrit, and CodeCommit are not available. Do not point the CLI or the webhook at those hosts.

The [MOSAICO A2A server](../installation/mosaico_server.md) accepts a Gitee pull-request URL or a unified diff pasted into the request. It is not a second git host.
