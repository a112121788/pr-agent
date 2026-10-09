---
title: "Gitea 集成"
sidebar_position: 8
---

## 运行 Gitea webhook 服务器

1. 在 Gitea 中创建一个新用户，并为其赋予目标群组或项目的「Reporter」角色。

2. 为第 1 步中的用户生成具有 `api` 访问权限的 `personal_access_token`。

3. 为你的应用生成一个随机密钥，并保存备用（`webhook_secret`）。例如可以使用：

    ```bash
    WEBHOOK_SECRET=$(python -c "import secrets; print(secrets.token_hex(10))")
    ```

    webhook 密钥是必需的：如果未配置 `GITEA.WEBHOOK_SECRET`，服务器会以 HTTP 403 拒绝每一个传入的 webhook。

4. 克隆此仓库：

    ```bash
    git clone https://github.com/the-pr-agent/pr-agent.git
    ```

5. 准备变量和密钥。如果你打算在运行代理时把它们设为环境变量，可跳过此步：
    - 在配置文件/变量中：
        - 将 `config.git_provider` 设为 "gitea"
    - 在密钥文件/变量中：
        - 在相应小节设置你的 AI 模型密钥
        - 在 [Gitea] 小节中，设置 `personal_access_token`（使用第 2 步的令牌）和 `webhook_secret`（使用第 3 步的密钥）

6. 为应用构建 Docker 镜像，并可选地推送到 Docker 仓库。下面以 Dockerhub 为例：

    ```bash
    docker build . -t pr-agent:gitea_app --target gitea_app -f docker/Dockerfile

    # Optional, to push it to your own Docker repository:
    docker tag pr-agent:gitea_app <your-registry>/pr-agent:gitea_app
    docker push <your-registry>/pr-agent:gitea_app
    ```

7. 设置环境变量，方法取决于你的 Docker 运行时。如果你已把密钥/配置直接放进 Docker 镜像，可跳过此步。

    ```bash
    CONFIG__GIT_PROVIDER=gitea
    GITEA__PERSONAL_ACCESS_TOKEN=<personal_access_token>
    GITEA__WEBHOOK_SECRET=<webhook_secret>
    GITEA__URL=https://gitea.com # Or self host
    GITEA__WEB_URL=https://git.example.com # Optional: user-facing URL for links published in comments (see below)
    OPENAI__KEY=<your_openai_api_key>
    GITEA__SKIP_SSL_VERIFICATION=false
    GITEA__SSL_CA_CERT=/path/to/cacert.pem
    ```

    > **注意：** 可以通过设置 `GITEA__SKIP_SSL_VERIFICATION=true` 禁用 SSL 验证，但不建议这样做。

    评论中发布的链接在设置了 `GITEA__WEB_URL` 时由其构建；否则，当 `GITEA__URL`
    不同于随附的默认值（`https://gitea.com`）时由其构建；再否则，从拉取请求的
    `html_url` 推导（Gitea/Forgejo 根据自身的 `ROOT_URL` 构建该字段）。
    当 `GITEA__URL` 是用户无法浏览的内部地址
    （例如 Docker 服务名），或服务器的 `ROOT_URL` 配置错误时，请显式设置 `GITEA__WEB_URL`。

8. 在 Gitea 项目中创建 webhook。将 URL 设为 `http[s]://<PR_AGENT_HOSTNAME>/api/v1/gitea_webhooks`，将密钥令牌设为第 3 步生成的密钥，并启用触发器 `push`、`comments` 和 `merge request events`。

9. 打开一个合并请求，或使用 PR Agent 的命令之一在合并请求上评论，以测试安装。

10. webhook 服务器在 gunicorn 下以多个工作进程运行。关于 `GUNICORN_WORKERS` / `GUNICORN_MAX_WORKERS` 旋钮和内存建议，请参见[为自托管 webhook 服务器估算规格](./index.md#sizing-a-self-hosted-webhook-server)——在设置内存限制之前值得一读。

## 不完整的拉取请求文件

当 Gitea 无法提供完整、有效的变更文件数据时，PR-Agent 会停止该命令，而不是分析不完整的变更集。

启用 `CONFIG.PUBLISH_OUTPUT` 时，PR-Agent 会尝试发布一条 **PR-Agent command was not run** 通知，并附上 Gitea 专用说明。发布该通知是尽力而为；如果提供商无法发布，它可能不会出现。

请重试该命令。如果问题仍然存在，请在 Gitea 中检查该拉取请求的变更文件和 diff。
