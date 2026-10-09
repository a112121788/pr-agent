---
title: "Data Privacy"
sidebar_position: 2
---

Gitee PR-Agent is self-hosted. It reads a Gitee pull request with your token and sends the prompt to the model endpoint you configure. This build does not store pull-request content to train models.

## What is sent

- Gitee API calls use the host token (`GITEE__PERSONAL_ACCESS_TOKEN` or `[gitee].personal_access_token` in the host secrets). A repository `.pr_agent.toml` cannot set that token, the API base, or the webhook secret.
- The prompt can include the title, description, commits, diff, file context, repository instructions, and the title and body of a Gitee issue when the issues API returns them.
- The default model is `gpt-6.1-sol`. A failed call falls over to `glm-5.3`. Responses are requested in `zh-CN` (`config.response_language`).
- Which of those calls happens is between you and the endpoint behind the API key. See [Changing a model](../usage-guide/changing_a_model.md).

## What is not sent

- An issue whose Gitee API returns HTTP 404 is skipped. Some enterprise repositories do this even though the issue is visible on the web. That body never reaches the model. See [Fetching ticket context](../core-abilities/fetching_ticket_context.md).
- Inline comments are published back to Gitee. They are not a separate data export. The anchor is Gitee's diff `position`.

## What stays on the host

- Keep tokens and model keys in the environment or the host secrets file.
