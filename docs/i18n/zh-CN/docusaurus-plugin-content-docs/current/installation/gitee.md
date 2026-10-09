---
title: "Gitee 集成"
sidebar_position: 9
---

## 运行 Gitee webhook 服务器

1. 创建一个能够读取目标仓库并在其拉取请求上评论的 Gitee 用户。如果你希望 `/describe` 和 `/generate_labels` 发布相应变更，请授予它编辑拉取请求描述和标签的权限。

2. 为该用户创建个人访问令牌。Gitee 会把此令牌作为 `access_token` 查询参数发送，因此请把它放在主机密钥中，而不是仓库设置文件里。

3. 生成 webhook 密钥：

    ```bash
    WEBHOOK_SECRET=$(python -c "import secrets; print(secrets.token_hex(32))")
    ```

    `GITEE.WEBHOOK_SECRET` 是必需的。当它为空时，服务器会以 HTTP 403 拒绝每一个 webhook。

4. 克隆此仓库：

    ```bash
    git clone https://github.com/the-pr-agent/pr-agent.git
    ```

5. 配置主机密钥：

    - 将 `config.git_provider` 设为 `gitee`。
    - 在对应的提供商小节中设置 AI 模型凭据。
    - 在 `[gitee]` 小节中，用第 2 步的值设置 `personal_access_token`，用第 3 步的值设置 `webhook_secret`。

    仓库的 `.pr_agent.toml` 不能覆盖 `api_base`、`webhook_secret`、`skip_ssl_verification` 或 `ssl_ca_cert`。

6. 构建 webhook 镜像：

    ```bash
    docker build . -t pr-agent:gitee_app --target gitee_app -f docker/Dockerfile
    ```

7. 提供运行时配置：

    ```bash
    CONFIG__GIT_PROVIDER=gitee
    GITEE__PERSONAL_ACCESS_TOKEN=<personal_access_token>
    GITEE__WEBHOOK_SECRET=<webhook_secret>
    GITEE__URL=https://gitee.com
    OPENAI__KEY=<your_openai_api_key>
    ```

    仅当代理暴露的是同一套 Gitee OpenAPI v5 时，才使用 `GITEE__API_BASE`。仅对受信任的私有端点设置 `GITEE__SKIP_SSL_VERIFICATION=true`。

8. 在 Gitee 仓库中添加 webhook：

    - URL：`https://<PR_AGENT_HOSTNAME>/api/v1/gitee_webhooks`
    - 密钥：第 3 步的值
    - 事件：Pull Request 和评论

    PR-Agent 会在解析 JSON 正文之前检查 `X-Gitee-Timestamp` 和 `X-Gitee-Token`。签名是对 `<timestamp>\n<secret>` 做 HMAC-SHA256 后以 Base64 编码，超过一小时的时间戳会被拒绝。

9. 打开一个拉取请求，或在某个拉取请求上评论 `/review`。打开拉取请求时会运行 `/describe`、`/review` 和 `/improve`。评论仅在以 `/` 开头时才会运行。

10. 服务器使用共享的 gunicorn 配置。在施加内存限制之前，请参见[为自托管 webhook 服务器估算规格](./index.md#sizing-a-self-hosted-webhook-server)。

## 已验证的行为

Gitee 提供商会读取拉取请求元数据、提交、变更文件和评论。它可以发布描述、评论和已有标签。行内评论使用 Gitee diff 的 `position`，从第一个 `@@` hunk 头的下一行开始计数。

webhook 将已打开拉取请求的 `merge_request_hooks` 以及拉取请求评论的 `note_hooks` 进行路由。推送事件目前不会触发命令。

## 不完整的拉取请求文件

当 Gitee 无法返回完整的变更文件列表时，PR-Agent 会停止该命令。启用 `CONFIG.PUBLISH_OUTPUT` 时，它会尝试发布一条 **PR-Agent command was not run** 通知。请重试该命令；如果通知仍然出现，请在 Gitee 中检查变更文件。
