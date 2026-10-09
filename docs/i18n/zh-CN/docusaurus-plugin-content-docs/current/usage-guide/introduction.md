---
title: "简介"
sidebar_position: 2
---

完成[安装](../installation/index.md)后，调用 PR-Agent 有三种基本方式：

1. 在本地运行 CLI 命令
2. 在线用法——在拉取请求上<a href="https://github.com/the-pr-agent/pr-agent/pull/229#issuecomment-1695021901" target="_blank" rel="noopener noreferrer">发表评论</a>
3. 让 PR-Agent 工具在新的拉取请求打开时自动运行

具体而言，可以通过预构建的 [Docker 镜像](../installation/locally.md#using-docker-image)发出 CLI 命令，也可以通过[本地克隆的仓库](../installation/locally.md#run-from-source)发出。

在线使用时，配置 [Gitee Webhook](../installation/gitee.md)。拉取请求打开时会自动运行工具，也可以在评论中使用以 `/` 开头的命令。
