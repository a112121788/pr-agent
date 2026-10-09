---
title: "MOSAICO A2A 服务器"
sidebar_position: 9
---

Gitee PR-Agent 可以作为 [A2A](https://a2a-protocol.org/) 1.0 *解决方案代理*，服务于 [MOSAICO](https://mosaico-project.eu/) 生态。进程是一个小型 Starlette 服务器：标准 A2A 接口（代理卡片和 JSON-RPC）加上健康探测。它不是分叉。代码在 [`pr_agent/mosaico/`](https://github.com/the-pr-agent/pr-agent/blob/main/pr_agent/mosaico/server.py)，随发布 wheel 交付，并从 `v0.36.0` 起作为独立镜像（`<version>-mosaico_agent`）交付。

每个请求携带一条 **Gitee 拉取请求地址**，或一份 **统一 diff**。没有其他 Git 托管的配置步骤。Gitee 地址形如 `https://gitee.com/<owner>/<repo>/pulls/<number>`。服务器为该地址下载公开的 `.diff`，不使用 Gitee 令牌。私有仓库应把统一 diff 贴进消息。

后续消息可以复用返回的 `contextId`。服务器在同一上下文里向前查看最多 100 个任务，寻找最新的地址或 diff。`mosaico.context_history_max_tasks`（1 到 1000）可改这个上限。历史在内存中。重启之后，或后续消息落到另一台副本上时，请重新发送地址或 diff。

这台服务器里的审查与 Gitee Webhook 使用同一套默认值：`gpt-6.1-sol`、备用 `glm-5.3`、响应语言 `zh-CN`，大 diff 分段审查。见 [核心能力](../core-abilities/index.md)。

### 端点

| 路径 | 方法 | 用途 |
| --- | --- | --- |
| `/.well-known/agent-card.json` | GET | A2A 代理卡片 |
| `/` | POST | A2A 1.0 JSON-RPC。发送 `SendMessage`，并带上 `A2A-Version: 1.0` 头。没有该头时，服务器把请求当作协议 0.3 并拒绝。回复是任务产物（`result.task.artifacts[].parts[].text`），不是状态消息。 |
| `/health` | GET | 实时 LLM 探测。往返成功为 `200`，否则为 `503`。 |

带有健康探测加固的镜像，在提供方失败时返回 `Unhealthy: LLM probe failed`。健康检查自己的警告只记录异常类型。`mosaico.health_timeout_seconds` 是以秒为单位的有限正截止时间（默认 10），用于协作式的异步准备、分发、消费流和等待清理。截止之后，流清理仍可能在后台继续。同步初始化和阻塞的 SDK 工作仍可能超出该时间。更早的镜像可能还没有这些保护。用 `MOSAICO__HEALTH_TIMEOUT_SECONDS` 覆盖默认值。非法值得到通用的不健康响应（503），而不是退回默认值。若加大预算，外部健康检查客户端和容器健康检查至少要给同样长的时间。随包的 Compose 探测另有 25 秒的 HTTP 超时。

对话流和健康探测流会在完成、失败或取消时尝试清理。取消消费者不会打断流清理。`/health` 超时后，只要事件循环还在，清理仍可能继续。清理没有单独的等待预算，也不设本地流准入限制。

代理卡片公布技能 `review`、`improve`、`describe` 和 `ask`，名称 `"PR-Agent Solution Agent"`，`version` 取自正在运行的构建，以及必需的扩展 `https://mosaico-project.eu/extensions/mosaico-observability`。流式能力公布为关闭。这个标志有实际作用：参考代理据此选择 `message/send` 或 `message/stream`。

### 模型与语言

不设置 `MODEL_NAME` 时，保留产品默认值：`config.model = "gpt-6.1-sol"`，`config.fallback_models = ["glm-5.3"]`。响应使用 `config.response_language`（`zh-CN`）。

若设置了 `MODEL_NAME`，它会替换 `config.model`，并**清空** `fallback_models`。不含 `/` 的值会按 `openai/<MODEL_NAME>` 发送。`MODEL_MAX_TOKENS`（默认 32000）是本构建尚不认识的模型的上下文预算。

`API_BASE` 和 `API_KEY` 是 OpenAI 兼容端点。无论是否覆盖模型，实时探测都需要它们。

### 请求限制与调用方认证

服务器使用 `config.max_webhook_request_body_bytes`（默认 5 MiB），包括没有有效 Content-Length 的流式正文。更大的请求在 JSON-RPC 解析或工具执行之前返回 HTTP 413。`mosaico.routing_scan_max_chars`（默认 65536，正整数）限制每个文本段里的地址和命令检测。边界上的半个记号会被忽略。提供的 diff 仍会完整处理。请把 Gitee 地址或命令放在消息靠前的位置。

把 `mosaico.bearer_tokens` 配成稳定主体名到互不相同的不透明密钥的映射，写在密钥配置里，或用 Dynaconf 的 JSON 环境变量语法：

```bash
export MOSAICO__BEARER_TOKENS='@json {"reference-agent":"replace-with-generated-secret"}'
```

映射非空时，JSON-RPC 和 `/health` 需要 `Authorization: Bearer <secret>`。缺少或无效的凭据在读取正文或调用模型之前返回 HTTP 401。代理卡片的 GET 保持公开，只公布需要 Bearer，不暴露密钥。在入口终止 TLS，并让调用方发送自己的凭据。任务、产物、历史和上下文后续消息都限定在配置的主体上。共用一个密钥的调用方共用该主体。轮换密钥时保持主体名不变。非法映射（含重复密钥）会导致应用无法启动。

默认的空映射是匿名访问，任务归属在受信任的单租户网络里共享。把服务暴露给其他调用方之前先配认证。这些限制不是保留策略、速率限制或并发配额。内存存储会把任务留到重启，每次经授权的健康探测都会做一次真实补全。

可观测性的根任务 ID 和超级任务 ID 必须是规范 UUID。非法 ID 各自省略。合法 ID 在生成 Langfuse 追踪上下文之前会转成小写。元数据错误不会让审查失败。

随包冒烟测试在服务器映射已配置时，用 `MOSAICO_BEARER_TOKEN` 传入客户端凭据。Compose 叠加层里，给健康检查设置 `PR_AGENT_BEARER_TOKEN`，并通过密钥配置把 `MOSAICO__BEARER_TOKENS` 加进服务的 `environment`。参考调用方的凭据单独配置。匿名模式下，两个探测在没有令牌时仍然可用。

### 运行独立容器

```bash
docker pull pragent/pr-agent:0.41.0-mosaico_agent
docker run -d --name pr-agent-mosaico -p 9000:9000 \
  -e API_BASE=https://your-openai-compatible-endpoint/v1 \
  -e API_KEY=sk-... \
  -e MODEL_NAME=gpt-6.1-sol \
  pragent/pr-agent:0.41.0-mosaico_agent

curl -s http://localhost:9000/.well-known/agent-card.json | python3 -m json.tool
```

`MODEL_NAME=gpt-6.1-sol` 选中默认主模型，并如上所述清空 `glm-5.3` 备用。若必须保留备用模型，不要设置 `MODEL_NAME`。生产环境请固定版本标签（见 [安装](./index.md)）；滚动的 `mosaico_agent` 标签会跟着最新构建走。

### 环境变量

| 变量 | 默认 | 用途 |
| --- | --- | --- |
| `API_BASE` | — | OpenAI 兼容端点的基址 |
| `API_KEY` | — | 该端点的 API 密钥 |
| `MODEL_NAME` | 未设置 | 模型标识。未设置时保留 `gpt-6.1-sol` 和备用 `glm-5.3`。设置后清空备用。 |
| `HOST` | `0.0.0.0` | 绑定地址 |
| `PORT` | `9000` | 绑定端口 |
| `AGENT_CARD_HOST`、`AGENT_CARD_PORT` | 未设置 | 卡片 `supportedInterfaces` 里公布的 URL。见下面的警告。 |
| `MODEL_MAX_TOKENS` | `32000` | 模型尚不被识别时的令牌预算 |
| `LANGFUSE_HOST`、`LANGFUSE_PUBLIC_KEY`、`LANGFUSE_SECRET_KEY` | 未设置 | 可选的 Langfuse 追踪 |

:::warning[AGENT_CARD_HOST / AGENT_CARD_PORT]
这两个变量决定 `supportedInterfaces` 里公布的 URL。不设置时，卡片公布 `http://localhost:9000/`，只有容器内部能访问。向 MOSAICO 注册可能成功，仓库记下这个地址，参考代理稍后路由任务时才会失败。把它们设成*调用方*将使用的主机和端口，然后检查：

```bash
curl -s http://<host>:<port>/.well-known/agent-card.json \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['supportedInterfaces'][0]['url'])"
```

若打印出 `localhost` 地址，部署就是错的。
:::

### 部署进 mosaico-demonstrator

[`docker/mosaico/`](https://github.com/the-pr-agent/pr-agent/tree/main/docker/mosaico) 是部署包（compose 叠加层、注册模板、环境变量模板、冒烟测试、LICENSE 和 README）。要在 [mosaico-demonstrator](https://gitlab.eclipse.org/eclipse-research-labs/mosaico-project/mosaico-demonstrator) 里运行该代理：

1. 把 `docker-compose.pr-agent.yml` 复制到 demonstrator 的 `compose/` 目录，与 `base-definitions.yml` 并列。叠加层的 `extends:` 路径相对该目录解析。
2. 把 `pr-agent-solution-agent.json` 复制到 demonstrator 的 `docker/agent-registrations/` 目录。
3. 把 `pr-agent.env.example` 里的 “demonstrator overlay” 块追加到 demonstrator 的 `env/llm.env`。填上 `PR_AGENT_MODEL`（`gpt-6.1-sol` 与本构建的主模型一致，并会清空备用模型）。`PR_AGENT_HOST` 可以留空，使用 demonstrator 自动检测到的局域网 IP。`PR_AGENT_PORT` 默认 `23000`。
4. 在 demonstrator 的 `01-compose.sh` 里，和其他任务代理叠加层一起加上 `-f compose/docker-compose.pr-agent.yml`。
5. 运行 `./01-compose.sh up -d`。

注册模板只带 `description`、`role`、`objective` 和 `version`。demonstrator 的 `register-agent.py` 在注册时注入 `name`、`a2aAgentCardUrl` 和 `deployment.mode = ENDPOINT`。两个名字故意不同：仓库条目是 `pr-agent-solution-agent`（`register-agent.py` 用它查找），卡片自己的 `name` 是 `"PR-Agent Solution Agent"`（展示字符串）。

### 验证

在部署包目录中运行：

```bash
./smoke_test.sh
```

结果是二者之一：

- **`SMOKE PASSED`** — 没有 LLM 凭据。脚本拉取固定镜像、启动，并只检查代理卡片。
- **`FULL ROUND-TRIP PASSED`** — 有凭据（脚本旁边的 `.env`，从 `pr-agent.env.example` 复制）。脚本还会调用 `GET /health`，并对一段内联 diff 做一次 A2A `SendMessage` 审查。

### 排错

- **容器一直 `unhealthy`，注册从未运行。** `/health` 是实时模型探测，凭据或模型不对时返回 `503`。检查 `API_BASE`、`API_KEY` 和 `MODEL_NAME`。
- **代理注册成功，但参考代理始终访问不到。** 卡片地址是 `localhost`。见上面的 `AGENT_CARD_HOST` / `AGENT_CARD_PORT` 警告。
- **注册容器取不到代理卡片。** `01-compose.sh` 会退回到 `get_fallback_ip`，结果可能是 `localhost`。该地址在宿主机上通，在 Docker 网络里的注册容器上不通。把 `PR_AGENT_HOST` 设成容器内能访问的地址，例如宿主机局域网 IP 或 `host.docker.internal`。
- **Gitee 地址没有产出审查。** 服务器只拉取公开的 `.diff`。私有仓库，以及不提供该地址的企业实例，需要把统一 diff 贴进消息。

### 继续阅读

[部署包 README](https://github.com/the-pr-agent/pr-agent/blob/main/docker/mosaico/README.md) 是本页的详细版：升级步骤、注册流程，以及环境变量约定。
