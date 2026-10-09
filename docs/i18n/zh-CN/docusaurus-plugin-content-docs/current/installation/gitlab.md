---
title: "GitLab 集成"
sidebar_position: 5
---

## 合并请求 diff 限制

PR-Agent 需要 GitLab 15.7 或更高版本，并从合并请求的
[`/diffs` 端点](https://docs.gitlab.com/api/merge_requests/#list-merge-request-diffs)获取全部分页。
分页不会绕过 GitLab 的服务端 diff 限制。如果返回的文件数与精确的 `changes_count` 不一致，或该计数
表明溢出或尚未就绪，PR-Agent 会抛出提供商
错误。GitLab 省略了补丁的文件（`too_large`，或
GitLab 19.2 之前的 `collapsed`）会改由其两个修订在本地做 diff。

`/diffs` 端点必须可用。PR-Agent 不会回退到已弃用的
`/changes` 端点或其原始 diff 重试。

PR-Agent 会在收集 diff 分页之前和之后读取最新的合并请求元数据。
如果收集过程中修订或文件数发生变化，它会重试一次，若再次变化则抛出
提供商错误。非空结果还要求有可用的 base/head
引用，以便加载文件内容。如果合并请求在增量
设置之后移动，PR-Agent 会回退到完整审查，而不是混用不同修订。

## 可选的子模块 diff 展开

启用 `GITLAB.EXPAND_SUBMODULE_DIFFS` 时，PR-Agent 会比较子模块提交，
以加入子文件补丁。如果比较超时，或某个子补丁被省略
（`collapsed` 或 `too_large`），它会记录警告并跳过该可选展开。
父级子模块 gitlink 仍留在合并请求 diff 中。这一仓库
比较回退与上面的合并请求 `/diffs` 行为是分开的。

## 作为 GitLab 流水线运行 {#run-as-a-gitlab-pipeline}

你可以使用预构建的 Action Docker 镜像，把 PR-Agent 作为 GitLab 流水线运行。这是开始使用 PR-Agent 的简单方式，无需搭建自己的服务器。

流水线模式会在 GitLab 创建合并请求流水线时自动运行已配置的命令。它不会接收 GitLab 评论事件。如果你希望用户在合并请求评论中调用 `/review` 或 `/improve` 等命令，请改为部署 [GitLab webhook 服务器](#run-a-gitlab-webhook-server)，并启用 **Comments** webhook 触发器。

(1) 在仓库中添加以下文件，路径为 `.gitlab-ci.yml`：

```yaml
stages:
  - pr_agent

pr_agent_job:
  stage: pr_agent
  image:
    name: pragent/pr-agent:latest
    entrypoint: [""]
  script:
    - cd /app
    - echo "Running PR Agent action step"
    - export MR_URL="$CI_MERGE_REQUEST_PROJECT_URL/merge_requests/$CI_MERGE_REQUEST_IID"
    - echo "MR_URL=$MR_URL"
    - export gitlab__url=$CI_SERVER_PROTOCOL://$CI_SERVER_FQDN
    - export gitlab__PERSONAL_ACCESS_TOKEN=$GITLAB_PERSONAL_ACCESS_TOKEN
    - export config__git_provider="gitlab"
    - export openai__key=$OPENAI_KEY
    - python -m pr_agent.cli --pr_url="$MR_URL" describe
    - python -m pr_agent.cli --pr_url="$MR_URL" review
    - python -m pr_agent.cli --pr_url="$MR_URL" improve
  rules:
    - if: '$CI_PIPELINE_SOURCE == "merge_request_event"'
```

此脚本会在创建合并请求流水线时运行 PR-Agent，包括打开合并请求以及向其源分支推送新提交时。你可以修改 `rules` 小节，使 PR-Agent 在不同事件上运行。
你也可以修改 `script` 小节，以运行不同的 PR-Agent 命令，或通过导出不同的环境变量使用不同参数。

### CI 产物上下文 {#ci-artifact-context}

先前作业产生的文件——测试报告、覆盖率摘要、linter 或 SAST 输出——可以作为额外上下文交给 `/review`、`/describe` 和 `/improve`，这样模型在审查合并请求时就能带上你流水线自己的发现。把该文件保存为作业产物，用 `needs:` 让 PR-Agent 作业依赖该作业，并用 `ARTIFACT_PATH` 指向它。上面的作业从 `/app` 运行，因此请给出完整路径：

```yaml
pr_agent_job:
  stage: pr_agent
  needs: ["test_job"]
  image:
    name: pragent/pr-agent:latest
    entrypoint: [""]
  script:
    - cd /app
    - export ARTIFACT_PATH="$CI_PROJECT_DIR/reports/pytest.xml"
    - export ARTIFACT_INSTRUCTIONS="These are the failing tests from this MR's pipeline. Call out any suggestion that would not fix them."
    - python -m pr_agent.cli --pr_url="$MR_URL" review
```

设置 `ARTIFACT_PATH` 本身就会开启该功能。其余旋钮——哪些工具接收上下文、标签、大小限制——是 GitHub Action 的 [CI 产物上下文](./github.md#ci-artifact-context) 下所描述的 `[artifacts]` 设置，它们对 CLI 同样适用。

### 忽略机器人创建的合并请求

依赖更新机器人通常使用可预测的源分支前缀。在通用合并请求规则之前添加一条优先级更高的 `when: never` 规则，以跳过这些分支：

```yaml
  rules:
    - if: '$CI_PIPELINE_SOURCE == "merge_request_event" && $CI_MERGE_REQUEST_SOURCE_BRANCH_NAME =~ /^(dependabot|renovate)\//'
      when: never
    - if: '$CI_PIPELINE_SOURCE == "merge_request_event"'
```

请调整正则表达式，以匹配你的机器人所使用的分支命名约定。按 `CI_MERGE_REQUEST_SOURCE_BRANCH_NAME` 过滤比 `GITLAB_USER_LOGIN` 更可靠，因为 `GITLAB_USER_LOGIN` 标识的是启动流水线的用户，在手动运行流水线时可能会变。

webhook 服务器可以通过仓库级 `.pr_agent.toml` 文件，对自动合并请求事件应用等效过滤器：

```toml
[config]
ignore_pr_source_branches = ["^(dependabot|renovate)/"]
```

关于所有受支持的过滤器，请参见[忽略拉取请求中的自动命令](../usage-guide/additional_configurations.md#ignoring-automatic-commands-in-prs)。

(2) 向你的 GitLab 仓库添加以下掩码变量（CI/CD -> Variables）：

- `GITLAB_PERSONAL_ACCESS_TOKEN`：你的 GitLab 个人访问令牌。

- `OPENAI_KEY`：你的 OpenAI 密钥。

请注意，如果你的基线分支未受保护，不要把这些变量设为 `protected`，否则流水线将无法访问它们。

> **注意**：`$CI_SERVER_FQDN` 变量从 GitLab 16.10 起可用。如果你使用更早的版本，该变量将不可用。不过，你可以组合 `$CI_SERVER_HOST` 和 `$CI_SERVER_PORT` 达到同样效果。请确保使用兼容版本，或相应调整配置。

> **注意**：环境变量 `gitlab__SSL_VERIFY` 可用于指定自定义 CA 证书包路径，以进行 SSL 验证。GitLab 暴露了 `$CI_SERVER_TLS_CA_FILE` 变量，它指向你的 GitLab 实例中配置的自定义 CA 证书文件。
> 也可以通过设置 `gitlab__SSL_VERIFY=false` 完全禁用 SSL 验证，但不建议这样做。
> 此设置只影响 GitLab API 客户端。关于 LLM 调用或 git clone 操作的证书问题，请参见[自定义 CA 与自签名证书](../usage-guide/custom_ca_and_self_signed_certificates.md)。

## 运行 GitLab webhook 服务器 {#run-a-gitlab-webhook-server}

1. 在 GitLab 中创建一个新用户，并为其赋予目标群组或项目的「Developer」角色。
   > **注意：** 对于 `/improve` 或 `/review` 等添加评论的操作，「Reporter」角色就足够了，
   > 但使用 `/describe` 命令更新合并请求描述时需要「Developer」角色。

2. 为第 1 步中的用户生成具有 `api` 访问权限的 `personal_access_token`。

3. 为你的应用生成一个随机密钥，并保存备用（`shared_secret`）。例如可以使用：

```bash
SHARED_SECRET=$(python -c "import secrets; print(secrets.token_hex(10))")
```

4. 克隆此仓库：

```bash
git clone https://github.com/the-pr-agent/pr-agent.git
```

5. 准备变量和密钥。如果你打算在运行代理时把它们设为环境变量，可跳过此步：
    1. 在配置文件/变量中：
        - 将 `config.git_provider` 设为 "gitlab"

    2. 在密钥文件/变量中：
        - 在相应小节设置你的 AI 模型密钥
        - 在 [gitlab] 小节中，设置 `personal_access_token`（使用第 2 步的令牌）和 `shared_secret`（使用第 3 步的密钥）
        - **身份验证类型**：将 `auth_type` 设为 `"private_token"`，以便在 `PRIVATE-TOKEN` 头中发送令牌；或使用默认的 `"oauth_token"`，对应 `Authorization: Bearer` 头。两者在 GitLab.com 和自托管实例上都受支持。

6. 为应用构建 Docker 镜像，并可选地推送到 Docker 仓库。下面以 Dockerhub 为例：

```bash
docker build . -t pr-agent:gitlab_webhook --target gitlab_webhook -f docker/Dockerfile

# Optional, to push it to your own Docker repository:
docker tag pr-agent:gitlab_webhook <your-registry>/pr-agent:gitlab_webhook
docker push <your-registry>/pr-agent:gitlab_webhook
```

7. 设置环境变量，方法取决于你的 Docker 运行时。如果你已把密钥/配置直接放进 Docker 镜像，可跳过此步。

```bash
CONFIG__GIT_PROVIDER=gitlab
GITLAB__PERSONAL_ACCESS_TOKEN=<personal_access_token>
GITLAB__SHARED_SECRET=<shared_secret>
GITLAB__URL=https://gitlab.com
GITLAB__AUTH_TYPE=oauth_token  # Use "private_token" for the PRIVATE-TOKEN header
OPENAI__KEY=<your_openai_api_key>
PORT=3000  # Optional: override the webhook server port
```

8. 在 GitLab 项目中创建 webhook。将 URL 设为 `http[s]://<PR_AGENT_HOSTNAME>/webhook`，将密钥令牌设为第 3 步生成的密钥，并启用触发器 `push`、`comments` 和 `merge request events`。

9. 打开一个合并请求，或使用 PR Agent 的命令之一在合并请求上评论，以测试安装。

10. webhook 服务器在 gunicorn 下以多个工作进程运行。关于 `GUNICORN_WORKERS` / `GUNICORN_MAX_WORKERS` 旋钮和内存建议，请参见[为自托管 webhook 服务器估算规格](./index.md#sizing-a-self-hosted-webhook-server)——在设置内存限制之前值得一读。

## 部署为 Lambda 函数

请注意，由于 AWS Lambda 环境变量名中不能包含 "."，你可以把环境变量中的每个 "." 替换为 "__"。<br>
例如：`GITLAB.PERSONAL_ACCESS_TOKEN` --> `GITLAB__PERSONAL_ACCESS_TOKEN`

1. 按照[运行 GitLab webhook 服务器](#run-a-gitlab-webhook-server)的第 1–5 步操作。
2. 构建一个可用作 Lambda 函数的 Docker 镜像

    ```shell
    docker buildx build --platform=linux/amd64 . -t pr-agent:gitlab_lambda --target gitlab_lambda -f docker/Dockerfile.lambda
   ```

3. 将镜像推送到 ECR

    ```shell
    docker tag pr-agent:gitlab_lambda <AWS_ACCOUNT>.dkr.ecr.<AWS_REGION>.amazonaws.com/pr-agent:gitlab_lambda
    docker push <AWS_ACCOUNT>.dkr.ecr.<AWS_REGION>.amazonaws.com/pr-agent:gitlab_lambda
    ```

4. 创建一个使用该已上传镜像的 Lambda 函数。将 Lambda 超时至少设为 3 分钟。
5. 为该 Lambda 函数配置函数 URL。
6. 在 Lambda 函数的环境变量中，将 `AZURE_DEVOPS_CACHE_DIR` 指定为可写位置，例如 /tmp。（见[链接](https://github.com/the-pr-agent/pr-agent/pull/450#issuecomment-1840242269)）
7. 回到[运行 GitLab webhook 服务器](#run-a-gitlab-webhook-server)的第 8–9 步，把函数 URL 作为你的 Webhook URL。
    Webhook URL 形如 `https://<LAMBDA_FUNCTION_URL>/webhook`

### 使用 AWS Secrets Manager

对于生产环境的 Lambda 部署，请使用 AWS Secrets Manager，而不是环境变量：

1. 为每个项目生成单独的随机 webhook 令牌，例如使用 `openssl rand -hex 32`。
   为每个 GitLab webhook 创建一个单独的密钥，JSON 格式如下（例如密钥名：`project-webhook-secret-001`）：

```json
{
  "gitlab_token": "glpat-xxxxxxxxxxxxxxxxxxxxxxxx",
  "webhook_token": "<generated-random-webhook-token>",
  "token_name": "project-webhook-001"
}
```

2. 为通用设置创建一个主配置密钥（例如密钥名：`pr-agent-main-config`）

```json
{
  "openai.key": "sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
}
```

3. 在 Lambda 中设置这些环境变量：

```bash
CONFIG__SECRET_PROVIDER=aws_secrets_manager
AWS_SECRETS_MANAGER__SECRET_ARN=arn:aws:secretsmanager:us-east-1:123456789012:secret:pr-agent-main-config-AbCdEf
```

4. 在 GitLab webhook 配置中，将 **Secret Token** 设为 `<secret-name>:<webhook-token>`：
   - 示例：`project-webhook-secret-001:<generated-random-webhook-token>`
   - 使用存储在 `webhook_token` 字段中的随机令牌，而不是 GitLab 个人访问令牌。
   - 最后一个冒号把令牌与密钥名分开，因此 webhook 令牌不得包含冒号。

PR-Agent 按密钥名取回 JSON，并在
使用 `gitlab_token` 之前把所提供的令牌与 `webhook_token` 比较。两个字段都必须是非空字符串。仅有密钥名并不是凭据。

5. 为你的 Lambda 执行角色添加 IAM 权限 `secretsmanager:GetSecretValue`

:::important 现有密钥提供商部署的迁移
部署此版本时，请为每个项目密钥添加 `webhook_token`，并把对应的 GitLab **Secret Token** 更新为
`<secret-name>:<webhook-token>`。仅含名称的现有令牌会被拒绝并返回
HTTP 401；请协调服务器与 webhook 的更新，以避免投递中断。同样的格式
也适用于 Google Cloud Storage 密钥提供商。

使用 `GITLAB.SHARED_SECRET` 的部署保留其现有令牌。匹配的共享密钥会
先被检查，并使用已配置的 `GITLAB.PERSONAL_ACCESS_TOKEN`，而不会联系云提供商。
:::
