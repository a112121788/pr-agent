---
title: "驾驶舱"
sidebar_position: 6
---

Webhook 镜像在 `/dashboard` 提供驾驶舱。容器内端口是 `3000`。打开页面只显示已登记的仓库，不会开始审查。

## 登记仓库

在首页输入 `owner/repo`，点「登记」。驾驶舱列出这个仓库里打开的拉取请求。点「移除」只从驾驶舱拿掉这个仓库，不删除 Gitee 上的仓库、拉取请求或评论。

记录默认写在 `sqlite:////data/factory.db`。用 `docker/dashboard.sh` 启动时，这个目录挂在命名卷 `pr-agent-data` 上，换容器不会丢掉已登记仓库。要换数据库，设置 `DASHBOARD__DATABASE_URL`，例如 `postgresql://user:pass@host:5432/dbname`。页面不显示这个地址。页头的「构建」是启动时传入的 `PR_AGENT_BUILD`。进程退出后，上次没跑完的审查会标成失败，可以再点。

## 批量审查

「登记」后面是「批量审查」。点它之后，已登记仓库里打开的拉取请求各走下一步：还没有当前提交的审查证据时，发起一次审查。

正在审查或还在排队的同一张拉取请求会标成「审查中」，审查按钮停用，也不会再排一次。这次审查结束后，才可以再审。

每张拉取请求上仍可以单独点「审查」「建议」或「状态」。

## 审核流水线

点开一张拉取请求进入审核流水线。页头有编号、标题、作者、分支和开放状态。「在 Gitee 打开」会在新的浏览器标签页打开，当前页留着。

从 Gitee 拉下的评论按 Markdown 显示，包括标题、列表、表格和代码块。评论里自带的 HTML 只当文本，不会执行。

## 内测

1. 构建镜像：`docker build -f docker/Dockerfile --target gitee_app -t pr-agent:gitee_app .`
2. 用 `docker/dashboard.sh` 启动，并传入 `GITEE__PERSONAL_ACCESS_TOKEN` 和 `OPENAI__KEY`。可选 `OPENAI__API_BASE`。数据卷是 `pr-agent-data`。
3. 打开 `/dashboard`。页头应有「构建」。
4. 输入 `owner/repo`，点「登记」。
5. 点「批量审查」，或在一张拉取请求上点「审查」。
6. 到 Gitee 刷新，查看 **PR 审查指南**。流水线里同一条评论按 Markdown 显示。

默认 `config.allow_auto_merge` 是 `false`。批量审查不会调用 Gitee 合并。要恢复自动汇入，在主机配置里把它设为 `true`。

抽查发现的问题不要在页面上改判定。规则改 `pr_agent/algo/review_policy.py`。模型、语言和是否自动合并改 `pr_agent/settings/configuration.toml` 或对应的环境变量。

## 汇入

驾驶舱不规划意图。意图仍由提出人用 `/intake` 写在拉取请求上。已经写下「双线」的拉取请求不能放行，也不能汇入。

流水线底部可以写「放行」「退回」或「等待」。这三个按钮只发布判定记录，不合并。审查正文里的「批准」不是放行。

只有主机打开 `config.allow_auto_merge`，并且当前提交已经有「放行」、且不是双线时，批量审查才会调用 Gitee 合并。退回、等待，或判定对应的提交已经变了，都留给人处理。
