---
title: "安装"
sidebar_position: 1
---

当前版本只支持 Gitee 拉取请求。

<div class="pra-provider-grid">

- <span class="pra-logo pra-logo--terminal" aria-hidden="true"></span> [本地](./locally.md)
- [Gitee](./gitee.md)

</div>

## GitHub 轮询 HTTP 请求

当 GitHub 轮询需要回溯拉取请求评论时，它会复用轮询 HTTP 会话，而不是用同步请求阻塞事件循环。
`github.polling_request_timeout` 为整次回退评论历史扫描设置总超时，包括任何后续分页请求
（默认：10 秒；正数上限为 60）。无效值会使用默认值并给出警告。请在主机配置中设置，或通过
`GITHUB__POLLING_REQUEST_TIMEOUT` 设置；仓库设置不能控制此上限。
这不会改变其他轮询请求，也不会改变顺序通知扫描。该回退现在遵循现有 aiohttp 会话的代理和 TLS
行为，而不是 Requests 专用的环境设置。

## 为自托管 webhook 服务器估算规格 {#sizing-a-self-hosted-webhook-server}

GitHub、GitLab、Gitea、Gitee 和 Bitbucket Server 的 webhook 服务器（Docker 目标 `github_app`、`gitlab_webhook`、`gitea_app`、`gitee_app` 和 `bitbucket_server_webhook`）在 gunicorn 下以多个工作进程运行，这样某个工作进程忙于处理请求时，不会挡住另一个工作进程提供的健康检查。其余部署方式——Bitbucket Cloud、Azure DevOps、GitHub 轮询以及 Lambda 变体——不使用这套 gunicorn 工作进程配置。

| 变量                   | 默认值      | 说明                                                                                      |
|------------------------|-------------|-------------------------------------------------------------------------------------------|
| `GUNICORN_WORKERS`     | *（未设置）* | 精确固定工作进程数。会覆盖推导出的数量以及 `GUNICORN_MAX_WORKERS`。                        |
| `GUNICORN_MAX_WORKERS` | `4`         | 自动推导的工作进程数上限。                                                                 |
| `PORT`                 | `3000`      | 服务器绑定的端口。                                                                         |

当 `GUNICORN_WORKERS` 未设置时，工作进程数由容器实际可用的 CPU 推导（cgroup CPU 限制，回退到 CPU 亲和性），并限制在 2 与 `GUNICORN_MAX_WORKERS` 之间。注意：只有 CPU *request* 而没有 *limit* 时，没有可供读取的 cgroup 配额，因此此时由该上限约束工作进程数。

**估算内存：** 导入应用大约占用 250MB。应用在 gunicorn master 中导入一次，工作进程从它 fork 而来，因此它们以写时复制方式共享大部分基线内存，而不是各自完整占用——总内存随工作进程数增长，但明显低于每个工作进程 250MB。默认 4 个工作进程可从大约 1Gi 起步，再按你自己的指标调整。

如果容器在启动期间被 OOMKilled，请降低工作进程数：

```bash
GUNICORN_WORKERS=2
```

## GitHub 轮询工作进程

GitHub 轮询使用一个轮询进程，并为每条已接受的评论使用单独的子进程。在所有轮询迭代中，最多可以有 10 个这样的子工作进程处于活动状态。如果较早的一批仍然占满上限，已接受的工作会等待空闲槽位，且不会阻塞事件循环。在持续负载下，这可能推迟下一次通知轮询。

现有的每批上限不变：一批中只有前 10 条排队评论会被接受；超出的工作会被记录并丢弃。等待中的工作仅保存在内存中。通知确认行为不变，因此关闭或启动失败并不保证重新投递。分发中断会记录剩余数量。工作进程启动失败会停止轮询，而不是冒着未跟踪子进程继续分发的风险；重启前请先检查失败原因。
已完成的子进程在每次迭代中会被 join（不等待）并关闭；
取消时不会终止仍在运行的子进程。这不是持久队列、
模型调用截止时间，也不是主机范围的内存上限。

:::note[Docker Hub 命名空间迁移]
**`0.34.2` 及之后**的版本发布在 [`pragent/pr-agent`](https://hub.docker.com/r/pragent/pr-agent) 下。更早的版本（直至并包括 `v0.31`）仍留在旧的 [`codiumai/pr-agent`](https://hub.docker.com/r/codiumai/pr-agent) 命名空间，作为冻结归档——那里不再推送新镜像。本站示例引用新命名空间；如果你固定到 `0.34.2` 之前的版本，请在 `image:` / `docker pull` / `uses: docker://` 引用中把 `pragent/pr-agent` 换成 `codiumai/pr-agent`。
:::

:::note[不可变版本与版本标签]
**你固定的就是你得到的。** 带版本号的产物在发布后绝不会改变：

- **GitHub 发布**——Git 标签不能移动或删除，附加的资源也不能新增、替换或移除。该保护在仓库删除后仍然有效，因此不可变发布中的标签永远不能被同名重建的仓库复用。（发布标题和说明仍可编辑；不可变性覆盖标签和资源。）
- **Docker 镜像**——`0.40.0` 和 `0.40.0-github_app` 这类版本标签始终解析到同一镜像。一旦推送，就不能被覆盖或重新指向。

**滚动标签按设计保持可变。** `latest`、`github_action`、`github_lambda`、`gitlab_lambda`、`gitlab_webhook`、`gitea_app`、`gitee_app`、`mosaico_agent` 和 `bitbucket_server_webhook` 会在每次发布时指向最新构建。它们便于试用，但在不同日期对同一滚动标签执行 `docker pull` 可能得到两个不同的镜像。

对于你所依赖的任何东西——CI、生产 webhook、固定的 Action 步骤——请引用版本标签（或摘要），而不是滚动标签。这样升级就是你主动做出的变更，而不是在你不知不觉中发生的事。
:::
