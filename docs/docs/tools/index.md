---
title: "Tools"
sidebar_position: 1
---

Gitee PR-Agent reviews pull requests on Gitee. It accepts only these pull-request URLs:

- `https://gitee.com/owner/repo/pulls/N`
- `https://e.gitee.com/<enterprise>/repos/owner/repo/pulls/N`

Published text uses `config.response_language` = `zh-CN`. The default model is `config.model` = `gpt-6.1-sol`. If that call fails, `config.fallback_models` uses `glm-5.3`.

## Run a tool {#run}

Comment on the pull request. Only a comment that starts with `/` runs a command:

```
/review
```

Or run the CLI image `ecloud-tcr.tencentcloudcr.com/ecloud_project/pr-agent:latest`:

```bash
docker run --rm -it \
  -e OPENAI__KEY=<your_openai_key> \
  -e OPENAI__API_BASE=https://your-gateway.example/v1 \
  -e CONFIG__GIT_PROVIDER=gitee \
  -e GITEE__PERSONAL_ACCESS_TOKEN=<your_gitee_token> \
  ecloud-tcr.tencentcloudcr.com/ecloud_project/pr-agent:latest \
  --pr_url https://gitee.com/owner/repo/pulls/N review
```

`CONFIG__GIT_PROVIDER` must be `gitee`. `OPENAI__KEY` and `OPENAI__API_BASE` are the model credentials. `GITEE__PERSONAL_ACCESS_TOKEN` reads the pull request and publishes comments, inline comments, descriptions, and labels.

The same overrides work on a comment:

```
/review --pr_reviewer.extra_instructions="focus on the migration"
```

When a pull request is opened, the [Gitee webhook](../installation/gitee.md) runs `/describe`, `/review`, and `/improve` unless `gitee.pr_commands` replaces that list. Push events do not start a command.

If Gitee cannot return a complete changed-file list, the command stops. With `config.publish_output` enabled, Gitee PR-Agent tries to post **PR-Agent command was not run**.

## Tools

| Tool | What it publishes on Gitee |
|------|----------------------------|
| **[`/describe`](./describe.md)** | Pull-request type, summary, walkthrough, and an optional diagram. |
| **[`/review`](./review.md)** | A Chinese review titled `PR 审查指南`, plus `审查工作量N/5` and `可能存在安全问题` when those labels apply. |
| **[`/improve`](./improve.mdx)** | `PR 代码建议`, as a comment and inline comments. Gitee cannot commit the suggested code. |
| **[`/ask`](./ask.md)** | An answer to one question about the pull request. |
| **[`/add_docs`](./add_docs.md)** | Documentation suggestions as inline comments. |
| **[`/generate_labels`](./generate_labels.md)** | Labels chosen from the change. |
| **[`/update_changelog`](./update_changelog.md)** | A changelog draft as a comment. The file is not pushed. |
| **[`/similar_issue`](./similar_issues.md)** | Nothing useful: issue indexing is not supported, so the command reports that and stops. |
| **[`/help`](./help.md)** | A command list, or an answer taken from these docs. |
| **[`/help_docs`](./help_docs.md)** | Nothing. The command is disabled and not registered. |

## Checked pull request

`/review` and `/improve` were run on [eclouddev/hlzs_web#2896](https://gitee.com/eclouddev/hlzs_web/pulls/2896).

Defaults live in `pr_agent/settings/configuration.toml`. Put repository overrides in `.pr_agent.toml` on the pull request's target branch. See [Configuration file](../usage-guide/configuration_options.md). A repository file cannot override `api_base`, `webhook_secret`, `skip_ssl_verification`, or `ssl_ca_cert`.
