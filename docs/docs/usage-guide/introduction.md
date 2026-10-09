---
title: "简介"
sidebar_position: 2
---

Gitee PR-Agent 审查 Gitee 上的拉取请求。本构建不连接 GitHub、GitLab、Bitbucket 或 Azure DevOps。

完成[安装](../installation/gitee.md)后，可以用以下两种方式调用：

1. 在本地用 CLI，并传入 Gitee 拉取请求 URL。
2. 在线使用 Gitee Webhook。服务器接受 `POST /api/v1/gitee_webhooks`。

打开拉取请求时会运行 `/describe`、`/review` 和 `/improve`。拉取请求上的评论只有在以 `/` 开头时才会执行。

发布镜像为 `ecloud-tcr.tencentcloudcr.com/ecloud_project/pr-agent:latest`。Webhook 服务目标是 `gitee_app`。命令、签名校验和环境变量见[用法与自动化](./automations_and_usage.md)。
