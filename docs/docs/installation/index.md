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

Gitee Webhook 服务（Docker 目标 `gitee_app`）在 gunicorn 下以多个工作进程运行。某个工作进程忙于处理请求时，不会挡住另一个工作进程提供的健康检查。

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

:::note[镜像位置]
当前镜像发布在 `ecloud-tcr.tencentcloudcr.com/ecloud_project/pr-agent`。`latest` 指向最新构建，提交短哈希标签固定到一次构建。旧的 Docker Hub 命名空间不再接收本仓库的新镜像。
:::

:::note[不可变版本与版本标签]
**你固定的就是你得到的。** 带版本号的产物在发布后绝不会改变：

- **GitHub 发布**——Git 标签不能移动或删除，附加的资源也不能新增、替换或移除。该保护在仓库删除后仍然有效，因此不可变发布中的标签永远不能被同名重建的仓库复用。（发布标题和说明仍可编辑；不可变性覆盖标签和资源。）
- **Docker 镜像**——提交短哈希标签对应一次构建。生产环境优先使用它或镜像摘要。

**滚动标签按设计保持可变。** `latest` 和 `gitee_app` 会在每次发布时指向最新构建。它们便于试用，但在不同日期对同一滚动标签执行 `docker pull` 可能得到两个不同的镜像。

对于你所依赖的任何东西——CI、生产 webhook、固定的 Action 步骤——请引用版本标签（或摘要），而不是滚动标签。这样升级就是你主动做出的变更，而不是在你不知不觉中发生的事。
:::
