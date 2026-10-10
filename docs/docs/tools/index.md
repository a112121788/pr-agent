---
title: "工具"
sidebar_position: 1
---

Gitee PR-Agent 只审查 Gitee 上的拉取请求。它只接受这两种拉取请求 URL：

- `https://gitee.com/owner/repo/pulls/N`
- `https://e.gitee.com/<enterprise>/repos/owner/repo/pulls/N`

发布文本使用 `config.response_language` = `zh-CN`。默认模型是 `config.model` = `glm-5.3`。这次调用失败时，`config.fallback_models` 使用 `gpt-6.1-sol`。

## 运行工具 {#run}

在拉取请求上评论。只有以 `/` 开头的评论会执行命令：

```
/review
```

也可以运行 CLI 镜像 `ecloud-tcr.tencentcloudcr.com/ecloud_project/pr-agent:latest`：

```bash
docker run --rm -it \
  -e OPENAI__KEY=<your_openai_key> \
  -e OPENAI__API_BASE=https://your-gateway.example/v1 \
  -e CONFIG__GIT_PROVIDER=gitee \
  -e GITEE__PERSONAL_ACCESS_TOKEN=<your_gitee_token> \
  ecloud-tcr.tencentcloudcr.com/ecloud_project/pr-agent:latest \
  --pr_url https://gitee.com/owner/repo/pulls/N review
```

`CONFIG__GIT_PROVIDER` 必须是 `gitee`。`OPENAI__KEY` 和 `OPENAI__API_BASE` 是模型凭据。`GITEE__PERSONAL_ACCESS_TOKEN` 用来读取拉取请求，并发布评论、行内评论、描述和标签。

评论里可以用同样的覆盖参数：

```
/review --pr_reviewer.extra_instructions="focus on the migration"
```

拉取请求打开时，[Gitee webhook](../installation/gitee.md) 会运行 `/describe`、`/review` 和 `/improve`，除非 `gitee.pr_commands` 换掉这份列表。推送事件不会启动命令。

如果 Gitee 无法返回完整的变更文件列表，命令会停止。启用 `config.publish_output` 时，Gitee PR-Agent 会尝试发布 **PR-Agent command was not run**。

## 工具

| 工具 | 在 Gitee 上发布什么 |
|------|---------------------|
| **[`/describe`](./describe.md)** | 拉取请求类型、摘要、文件导览，以及可选的图。 |
| **[`/intake`](./factory.md)** | 受理记录。只保存四个意图之一和提出人的原话。 |
| **[`/review`](./review.md)** | 标题为 `PR 审查指南` 的中文审查，评论绑定当前提交号。 |
| **[`/improve`](./improve.mdx)** | `PR 代码建议`，以评论和行内评论发布。Gitee 不能提交建议代码。 |
| **[`/verdict`](./factory.md)** | 判定记录。只接受放行、退回、等待。 |
| **[`/merge-check`](./factory.md)** | 汇入检查。只报告能否由人合并，不会点击合并。 |
| **[`/ask`](./ask.md)** | 针对该拉取请求的一个回答。 |
| **[`/add_docs`](./add_docs.md)** | 以行内评论发布的文档建议。 |
| **[`/generate_labels`](./generate_labels.md)** | 与本次变更匹配的标签。 |
| **[`/update_changelog`](./update_changelog.md)** | 以评论发布的变更日志草稿。不会推送文件。 |
| **[`/similar_issue`](./similar_issues.md)** | 没有检索结果：不支持议题索引，命令会说明这一点后停止。 |
| **[`/help`](./help.md)** | 命令列表，或根据这些文档作出的回答。 |


## 已验证的拉取请求

`/review` 和 `/improve` 已在 [eclouddev/hlzs_web#2896](https://gitee.com/eclouddev/hlzs_web/pulls/2896) 上运行过。

默认值在 `pr_agent/settings/configuration.toml`。仓库级覆盖写在拉取请求目标分支的 `.pr_agent.toml` 里。参见[配置文件](../usage-guide/configuration_options.md)。仓库文件不能覆盖 `api_base`、`webhook_secret`、`skip_ssl_verification` 或 `ssl_ca_cert`。
