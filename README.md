<p align="center">
  <img src="docs/static/img/favicon.svg" width="96" height="96" alt="Gitee PR-Agent 标志">
</p>

# Gitee PR-Agent

Gitee PR-Agent 是审核工厂的核心机。它阅读一张 Gitee 拉取请求，把证据写成中文评论。负责人写下「放行」「退回」或「等待」后，才由有权限的人在 Gitee 上合并。

本版本只支持 Gitee。

## 快速开始

准备模型密钥、模型地址和 Gitee 个人访问令牌。取证调用使用 openai-codex SDK，默认模型是 `glm-5.3`。把下面的占位内容换成真实值，并把地址换成浏览器里的拉取请求地址：

```bash
docker run --rm -it \
  -e OPENAI__KEY=<模型密钥> \
  -e OPENAI__API_BASE=<模型地址> \
  -e CONFIG__GIT_PROVIDER=gitee \
  -e GITEE__PERSONAL_ACCESS_TOKEN=<Gitee 令牌> \
  ecloud-tcr.tencentcloudcr.com/ecloud_project/pr-agent:latest \
  --pr_url https://gitee.com/owner/repo/pulls/7 review
```

企业版地址使用：

```text
https://e.gitee.com/<企业名>/repos/owner/repo/pulls/7
```

命令结束后，回到 Gitee 刷新页面，查看 **PR 审查指南**。把最后的 `review` 改成 `improve`，会再发布 **PR 代码建议**。

## 四段审核

| 阶段 | 谁来做 | 留下什么 |
|---|---|---|
| 受理 | 提出人 | 写明意图的拉取请求 |
| 取证 | Gitee PR-Agent | 中文评论和标签 |
| 判定 | 负责人 | 放行、退回或等待 |
| 汇入 | 有权限的人 | 在 Gitee 上合并 |

机器打印的「批准」「请求修改」「仅评论」只是证据，不等于负责人已经判定。

## 命令

| 命令 | 评论 |
|---|---|
| `/describe` | 标题、描述和文件导览 |
| `/review` | PR 审查指南、团队规则和审查工作量 |
| `/improve` | PR 代码建议 |
| `/ask` | 针对当前改动的一次回答 |

Gitee 不能接收机器推送的代码。建议、文档和变更日志都留在评论里。

拉取请求打开后，Webhook 依次运行 `/describe`、`/review` 和 `/improve`。之后只有以 `/` 开头的评论会触发命令。

## 配置

```bash
CONFIG__GIT_PROVIDER=gitee
GITEE__PERSONAL_ACCESS_TOKEN=<Gitee 令牌>
GITEE__WEBHOOK_SECRET=<Webhook 密钥>
OPENAI__KEY=<模型密钥>
OPENAI__API_BASE=<模型地址>
```

默认模型是 `glm-5.3`，备用模型是 `gpt-6.1-sol`，评论语言是 `zh-CN`。

Webhook 服务同时提供驾驶舱，路径是 `/dashboard`。先登记 `owner/repo`，再点「登记」后面的「批量审查」。打开页面不会自动审查。正在审查的拉取请求标成「审查中」，同一张不能同时再审一次。说明见 [驾驶舱](docs/docs/usage-guide/dashboard.md)。

本地安装后也可以运行：

```bash
uv sync
uv run gitee-pr-agent --pr_url https://gitee.com/owner/repo/pulls/7 review
```

## 继续阅读

- [第一次使用](https://docs.pr-agent.ai/)
- [接入 Gitee Webhook](https://docs.pr-agent.ai/installation/gitee/)
- [审核工厂的四段](https://docs.pr-agent.ai/overview/review_factory/)
