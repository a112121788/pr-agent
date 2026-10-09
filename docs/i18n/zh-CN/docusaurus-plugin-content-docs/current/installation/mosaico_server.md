---
title: "MOSAICO A2A 服务器"
sidebar_position: 9
---

PR-Agent 可以作为 [A2A](https://a2a-protocol.org/) 1.0 *解决方案代理*，服务于
[MOSAICO](https://mosaico-project.eu/) 生态系统：一个小型 Starlette 服务器，暴露
标准 A2A 接口（代理卡片 + JSON-RPC）以及健康探测。它**不是**分叉，也不是
独立项目——服务器是 [`pr_agent/mosaico/`](https://github.com/the-pr-agent/pr-agent/blob/main/pr_agent/mosaico/server.py) 下的 PR-Agent 代码，
随每个发布 wheel 一起交付，并从 `v0.36.0` 起作为独立 Docker 镜像（`<version>-mosaico_agent`）
交付。服务器对 Git 提供商没有偏向：每个请求都携带
PR URL 或原始 diff。后续消息可以通过复用返回的
`contextId` 来引用该输入；默认情况下，服务器会考虑同一上下文中最多 100 个先前任务，
以找到最新的 PR URL 或 diff。设置 `mosaico.context_history_max_tasks`（1 到 1000）可更改
此上限。任务历史保存在内存中，因此重启后，或
把后续消息路由到另一台服务器副本时，请重新发送该输入。

### 此模式是什么

A2A 服务器暴露三个端点：

| 路径 | 方法 | 用途 |
| --- | --- | --- |
| `/.well-known/agent-card.json` | GET | A2A 代理卡片 |
| `/` | POST | A2A 1.0 JSON-RPC。发送 `SendMessage` 方法，并带上 `A2A-Version: 1.0` 头（该头是必需的：没有它时，服务器会把请求当作协议 0.3 并拒绝）。回复以任务产物形式到达（`result.task.artifacts[].parts[].text`），而不是状态消息。 |
| `/health` | GET | **实时 LLM 连通性探测**——LLM 往返成功时为 `200`，否则为 `503` |

带有健康探测加固的镜像，在提供商
失败时返回 `Unhealthy: LLM probe failed`；健康检查自身的警告只记录异常类型。
`mosaico.health_timeout_seconds` 以秒为单位设置一个有限的正截止时间（默认：10），
用于协作式异步准备、分发、流消费以及清理等待。
超过此截止时间后，流清理可以在后台继续。同步
初始化和阻塞式 SDK 工作仍可能超出该时间。
较旧的镜像可能早于这些保护措施。
在服务器环境中设置 `MOSAICO__HEALTH_TIMEOUT_SECONDS` 可覆盖默认值。
无效值会产生通用的不健康响应（503），而不是使用默认值。
增大该预算时，也要给任何外部健康检查客户端
和容器 healthcheck 留出足够时间；随附的 Compose 探测使用单独的 25 秒 HTTP 超时。

聊天和健康探测流会在完成、失败或取消时尝试清理。
消费者取消不会中断流清理，清理可能在 `/health`
超时之后继续，只要事件循环仍然活动。清理没有单独的等待预算或
配置键，也不会施加本地流准入限制。

对外公布的代理卡片包含技能 `review`、`improve`、`describe` 和 `ask`，
名称 `"PR-Agent Solution Agent"`，一个从正在运行的构建派生的 `version`（从不
手工维护），以及必需的
`https://mosaico-project.eu/extensions/mosaico-observability` 扩展。流式传输
被公布为禁用，这一点至关重要：参考代理会根据该能力在
`message/send` 与 `message/stream` 之间选择。

### 请求限制与调用方身份验证

MOSAICO 使用共享的 `config.max_webhook_request_body_bytes` 限制（默认 5 MiB），
包括没有有效 Content-Length 的流式正文。过大的请求会在 JSON-RPC 解析或工具执行之前返回 HTTP 413。
`mosaico.routing_scan_max_chars`（默认：65536，
一个正整数）限制每个文本片段中的 PR URL 和命令检测。边界处不完整的标记
会被忽略；提供的 diff 仍会被完整处理。请把 PR URL 或
命令放在消息或其周围文字的开头附近。

在密钥设置中把 `mosaico.bearer_tokens` 配置为稳定主体名称到互不相同的不透明密钥的映射，
或通过 Dynaconf 的 JSON 环境变量语法：

```bash
export MOSAICO__BEARER_TOKENS='@json {"reference-agent":"replace-with-generated-secret"}'
```

映射非空时，JSON-RPC 和 `/health` 要求 `Authorization: Bearer <secret>`。
缺失或无效的凭据会在读取正文或运行 LLM 之前返回 HTTP 401。
代理卡片的 GET 保持公开，并公布 bearer 要求，但不会暴露密钥。
请在入口处使用 HTTPS，并配置调用方发送其凭据。任务、产物、
历史和上下文后续消息都限定在已配置的主体范围内；共享同一
密钥的调用方共享该主体。轮换密钥时请保持主体名称稳定。无效的
凭据映射（包括重复密钥）会导致应用构建失败。

默认的空映射为受信任的、
单租户网络保留匿名访问和共享的任务所有权。在把服务暴露给其他调用方之前，请配置身份验证。
这些限制并不提供任务保留策略、速率限制或并发配额：
内存存储仍会把任务保留到重启为止，而且每一次已授权的健康探测都会执行
一次实时补全。

可观测性的根/超级任务 ID 必须是规范 UUID。无效 ID 会被各自省略；
有效 ID 在生成 Langfuse 追踪上下文之前会被规范化为小写。元数据错误
不会导致审查失败。

对于随附的冒烟测试，当服务器映射已配置时，请在
脚本环境中以 `MOSAICO_BEARER_TOKEN` 提供客户端凭据。对于 Compose 叠加层，请为 healthcheck 提供
`PR_AGENT_BEARER_TOKEN`，并通过你的密钥配置把 `MOSAICO__BEARER_TOKENS` 加入服务的
`environment` 映射。请单独配置参考调用方的
凭据。两种探测在匿名模式下没有令牌也能继续工作。

### 运行独立容器

服务器从一次裸 `docker pull` 启动只需几秒——无需克隆仓库，也无需构建：

```bash
docker pull pragent/pr-agent:0.41.0-mosaico_agent
docker run -d --name pr-agent-mosaico -p 9000:9000 \
  -e API_BASE=https://your-openai-compatible-endpoint/v1 \
  -e API_KEY=sk-... \
  -e MODEL_NAME=openai/your-model-slug \
  pragent/pr-agent:0.41.0-mosaico_agent

curl -s http://localhost:9000/.well-known/agent-card.json | python3 -m json.tool
```

生产环境请固定版本标签（见[安装页面](./index.md)上的「不可变版本与版本标签」说明）；普通的 `mosaico_agent`
滚动标签会在每次发布时指向最新构建。

### 环境变量

| 变量 | 默认值 | 用途 |
| --- | --- | --- |
| `API_BASE` | — | OpenAI 兼容 LLM 端点的基址 URL |
| `API_KEY` | — | 该端点的 API 密钥 |
| `MODEL_NAME` | — | 要调用的模型标识 |
| `HOST` | `0.0.0.0` | 绑定地址 |
| `PORT` | `9000` | 绑定端口 |
| `AGENT_CARD_HOST`、`AGENT_CARD_PORT` | 未设置 | 在卡片的 `supportedInterfaces` 中公布的 URL；见下方警告 |
| `MODEL_MAX_TOKENS` | `32000` | 对 pr-agent 尚不知道上下文大小的模型所使用的 token 预算 |
| `LANGFUSE_HOST`、`LANGFUSE_PUBLIC_KEY`、`LANGFUSE_SECRET_KEY` | 未设置 | 可选的 Langfuse 可观测性 |

:::warning[AGENT_CARD_HOST / AGENT_CARD_PORT——唯一必须弄对的一项]

这两个变量设置代理在 `supportedInterfaces` 中公布的 URL。如果保持
未设置，卡片会公布 `http://localhost:9000/`，而该地址只能从
容器内部访问。由此造成的失败是**静默且滞后的**：向 MOSAICO
注册会成功，仓库会存下这个不可达的 URL，参考代理
只有在尝试把任务路由到此代理时才会解引用失败。请把它们设为
*调用方*用来访问该容器的主机/端口，并用以下方式验证：

```bash
curl -s http://<host>:<port>/.well-known/agent-card.json \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['supportedInterfaces'][0]['url'])"
```

如果打印出的是 `localhost` URL，则部署是错误的。
:::

### 部署到 mosaico-demonstrator

[`docker/mosaico/`](https://github.com/the-pr-agent/pr-agent/tree/main/docker/mosaico)
目录是一套完整的部署包（compose 叠加层、注册模板、环境变量模板、
冒烟测试、LICENSE，以及权威 README）。要把该代理作为任务代理运行在
[mosaico-demonstrator](https://gitlab.eclipse.org/eclipse-research-labs/mosaico-project/mosaico-demonstrator) 中：

1. 把 `docker-compose.pr-agent.yml` 复制到 demonstrator 的 `compose/` 目录，与
   `base-definitions.yml` 放在一起（叠加层的 `extends:` 引用是相对于该
   目录解析的）。
2. 把 `pr-agent-solution-agent.json` 复制到 demonstrator 的
   `docker/agent-registrations/` 目录。
3. 把 `pr-agent.env.example` 中的「demonstrator overlay」块追加到 demonstrator 的
   `env/llm.env`，并填入 `PR_AGENT_MODEL`（`PR_AGENT_HOST` 可以留空，以使用
   demonstrator 自动检测的局域网 IP；`PR_AGENT_PORT` 默认为 `23000`）。
4. 在 demonstrator 的 `01-compose.sh` 中，于其他任务代理叠加层旁边加入
   `-f compose/docker-compose.pr-agent.yml`。
5. 运行 `./01-compose.sh up -d`。

注册模板只包含 `description`、`role`、`objective`、`version`；
demonstrator 的 `register-agent.py` 会在注册时注入 `name`、`a2aAgentCardUrl` 和
`deployment.mode = ENDPOINT`。有两个名称故意不同，
不应被「修正」：仓库条目是 `pr-agent-solution-agent`（`register-agent.py`
据此查找该代理），而卡片自身的 `name` 是
`"PR-Agent Solution Agent"`（展示用字符串）。

### 验证

```bash
./smoke_test.sh
```

在部署包目录中会得到两种结果之一：

- **`SMOKE PASSED`**——没有可用的 LLM 凭据；脚本拉取了固定的镜像，
  将其启动，并只验证了代理卡片。
- **`FULL ROUND-TRIP PASSED`**——凭据存在（通过脚本旁的 `.env` 文件，
  从 `pr-agent.env.example` 复制而来）；脚本还会额外执行 `GET /health`，以及针对内联 diff 的
  A2A `SendMessage` 审查。

### 故障排除

- **容器一直处于 `unhealthy`，注册从未运行。** `/health` 是实时 LLM
  探测，凭据错误或缺失时会返回 `503`——这是预期行为。请检查
  `API_BASE` / `API_KEY` / `MODEL_NAME`，而不是 compose 文件。
- **代理已注册，但参考代理始终无法访问它。** 公布的卡片 URL 是
  `localhost`；见上方关于 `AGENT_CARD_HOST` / `AGENT_CARD_PORT` 的警告。
- **注册容器本身无法获取代理卡片。** `01-compose.sh` 会回退到
  `get_fallback_ip`，它可能解析为 `localhost`——从宿主机可以访问，但从
  Docker 网络内的注册容器无法访问。请把 `PR_AGENT_HOST` 显式设为从
  Docker 内部可达的地址（例如宿主机的局域网 IP，或 `host.docker.internal`）。

### 继续阅读

[部署包 README](https://github.com/the-pr-agent/pr-agent/blob/main/docker/mosaico/README.md)
是此接口的权威深入说明，也是上文摘要的来源；它在一处涵盖了
升级步骤、注册流程以及完整的环境变量约定。
