---
title: "简介"
sidebar_position: 2
---

完成[安装](../installation/index.md)后，调用 PR-Agent 有三种基本方式：

1. 在本地运行 CLI 命令
2. 在线用法——在拉取请求上<a href="https://github.com/the-pr-agent/pr-agent/pull/229#issuecomment-1695021901" target="_blank" rel="noopener noreferrer">发表评论</a>
3. 让 PR-Agent 工具在新的拉取请求打开时自动运行

具体而言，可以通过预构建的 [Docker 镜像](../installation/locally.md#using-docker-image)发出 CLI 命令，也可以通过[本地克隆的仓库](../installation/locally.md#run-from-source)发出。

对于在线用法，你需要设置 [GitHub App](../installation/github.md#run-as-a-github-app) 或 [GitHub Action](../installation/github.md#run-as-a-github-action)（GitHub）、[GitLab webhook](../installation/gitlab.md#run-a-gitlab-webhook-server)（GitLab），或 [BitBucket App](../installation/bitbucket.md)（BitBucket）。
这些平台也支持在新的拉取请求打开时，或在每次推送到分支时，自动运行 PR-Agent 的特定工具。
