---
title: "Bitbucket 集成"
sidebar_position: 6
---

## 作为 Bitbucket 流水线运行 {#run-as-a-bitbucket-pipeline}

你可以使用 Bitbucket Pipeline，在每次打开或更新拉取请求时运行 PR-Agent。

1. 在仓库中添加以下文件 bitbucket-pipelines.yml

```yaml
pipelines:
    pull-requests:
      '**':
        - step:
            name: PR Agent Review
            image: pragent/pr-agent:latest
            script:
              - pr-agent --pr_url=https://bitbucket.org/$BITBUCKET_WORKSPACE/$BITBUCKET_REPO_SLUG/pull-requests/$BITBUCKET_PR_ID review
```

2. 在仓库设置 > Pipelines > Repository variables 下，为仓库添加以下安全变量。

   - CONFIG__GIT_PROVIDER: `bitbucket`
   - OPENAI__KEY: `<your key>`
   - BITBUCKET__AUTH_TYPE: `basic` 或 `bearer`（默认为 `bearer`）
   - BITBUCKET__BEARER_TOKEN: `<your token>`（auth_type 为 bearer 时必需）
   - BITBUCKET__BASIC_TOKEN: `<your token>`（auth_type 为 basic 时必需）

你可以按照 Repository Settings -> Security -> Access Tokens 为仓库获取 Bitbucket 令牌。
对于基本身份验证，你可以用用户名:密码组合生成 base64 编码的令牌。

请注意，Bitbucket Pipeline 不支持在拉取请求上发表评论。

### Bitbucket Cloud 上的持久评论

审查和代码建议的身份标记在 Bitbucket Cloud 上使用不可见的 Markdown 链接引用。
带有较旧 HTML 身份标记的现有评论仍会被识别并就地更新。
无需更改配置。

### 不完整的拉取请求 diff

当 Bitbucket Cloud 返回的补丁数量与
过滤后的变更文件列表条目数不一致时，PR-Agent 会停止，而不是把 diff 当作空来处理。
受影响的 `/add_docs`、`/generate_labels`、`/describe`、`/review` 或 `/improve`
运行可能会发布 **PR-Agent command was not run**，并附上 Bitbucket 专用说明，
前提是启用了 `CONFIG.PUBLISH_OUTPUT`。这条提供商专用通知会替换
通用的 `/review` 和 `/improve` 失败输出，以避免重复评论。

请重试该命令。如果问题仍然存在，请在
Bitbucket 中检查该拉取请求的 diff。PR-Agent 不会自动恢复缺失的补丁。

## Bitbucket Server 与 Data Center

使用服务账号的用户名和密码登录你的 Bitbucket 本地实例。
进入 `Manage account`、`HTTP Access tokens`、`Create Token`。
生成令牌，并将其添加到 .secret.toml 的 `bitbucket_server` 小节

```toml
[bitbucket_server]
bearer_token = "<your key>"
```

不要忘记同时设置 Bitbucket Server 实例的 URL（写在 `.secret.toml` 或 `configuration.toml` 中）：

```toml
[bitbucket_server]
url = "<full URL to your Bitbucket instance, e.g.: https://git.bitbucket.com>"
```

### 作为 CLI 运行

修改 `configuration.toml`：

```toml
git_provider="bitbucket_server"
```



并传入拉取请求 URL：

```shell
python cli.py --pr_url https://git.on-prem-instance-of-bitbucket.com/projects/PROJECT/repos/REPO/pull-requests/1 review
```

### 作为服务运行

要把 PR-Agent 作为 webhook 运行，请构建 Docker 镜像：

```bash
docker build . -t pr-agent:bitbucket_server_webhook --target bitbucket_server_webhook -f docker/Dockerfile

# Optional, to push it to your own Docker repository:
docker tag pr-agent:bitbucket_server_webhook <your-registry>/pr-agent:bitbucket_server_webhook
docker push <your-registry>/pr-agent:bitbucket_server_webhook
```

进入 `Projects` 或 `Repositories`、`Settings`、`Webhooks`、`Create Webhook`。
填写名称和 URL。配置 webhook **Secret**，并在 PR-Agent 的 `.secrets.toml` 中设置相同的值：

```toml
[bitbucket_server]
webhook_secret = "<webhook secret>"
```

Bitbucket 使用该密钥在 `X-Hub-Signature` 头中为 webhook 载荷签名。PR-Agent 要求提供该密钥；如果缺失或为空，会以 HTTP 403 拒绝 webhook 请求。没有有效签名的正常 webhook 投递同样会收到 HTTP 403。配置密钥之后，Bitbucket 的连接测试仍然可用。

单独的 Authentication 选项可以保持为「None」，因为此服务器验证的是基于密钥的签名，而不是基本身份验证。勾选「Pull Request Opened」，以便将该事件作为 webhook 接收。

URL 应以 `/webhook` 结尾，例如：https://domain.com/webhook

webhook 服务器在 gunicorn 下以多个工作进程运行。关于 `GUNICORN_WORKERS` / `GUNICORN_MAX_WORKERS` 旋钮和内存建议，请参见[为自托管 webhook 服务器估算规格](./index.md#sizing-a-self-hosted-webhook-server)——在设置内存限制之前值得一读。
