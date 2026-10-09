---
title: "MOSAICO A2A Server"
sidebar_position: 9
---

Gitee PR-Agent can run as an [A2A](https://a2a-protocol.org/) 1.0 *solution agent* for the [MOSAICO](https://mosaico-project.eu/) ecosystem. The process is a small Starlette server: the standard A2A surface (agent card and JSON-RPC) plus a health probe. It is not a fork. The code is [`pr_agent/mosaico/`](https://github.com/the-pr-agent/pr-agent/blob/main/pr_agent/mosaico/server.py), it ships in the release wheel, and it ships as its own image (`<version>-mosaico_agent`) from `v0.36.0`.

Each request carries a **Gitee pull-request URL** or a **unified diff**. There is no setup for any other git host. A Gitee URL looks like `https://gitee.com/<owner>/<repo>/pulls/<number>`. The server downloads a public `.diff` for that URL. It does not use the Gitee token. Private repositories should paste the unified diff into the message.

A follow-up can reuse the returned `contextId`. The server looks through up to 100 earlier tasks in that context for the latest URL or diff. `mosaico.context_history_max_tasks` (1 to 1000) changes the limit. History is in memory. After a restart, or when a follow-up lands on another replica, send the URL or the diff again.

Reviews inside this server use the same defaults as the Gitee webhook: `gpt-6.1-sol`, fallback `glm-5.3`, responses in `zh-CN`, and segmented review for a large diff. See [Core abilities](../core-abilities/index.md).

### Endpoints

| Path | Method | Purpose |
| --- | --- | --- |
| `/.well-known/agent-card.json` | GET | The A2A agent card |
| `/` | POST | A2A 1.0 JSON-RPC. Send `SendMessage` with an `A2A-Version: 1.0` header. Without that header the server treats the request as protocol 0.3 and rejects it. The reply is a task artifact (`result.task.artifacts[].parts[].text`), not a status message. |
| `/health` | GET | A live LLM probe. `200` when a round trip succeeds, `503` otherwise. |

Images with the health-probe hardening return `Unhealthy: LLM probe failed` when the provider fails. The health check's own warning records only the exception type. `mosaico.health_timeout_seconds` is a finite positive deadline in seconds (default 10) for cooperative asynchronous preparation, dispatch, stream consumption, and cleanup waiting. Stream cleanup can continue in the background after the deadline. Synchronous initialization and blocking SDK work can still exceed it. Older images may predate these protections. Set `MOSAICO__HEALTH_TIMEOUT_SECONDS` to override the default. An invalid value yields the generic unhealthy response (503) instead of the default. If you raise the budget, give the external health-check client and the container healthcheck at least as long. The bundled Compose probe uses a separate 25-second HTTP timeout.

Chat and health-probe streams attempt cleanup on completion, failure, or cancellation. Cancelling the consumer does not interrupt stream cleanup. Cleanup can continue after `/health` times out while the event loop is still running. Cleanup has no separate wait budget and does not impose a local stream admission limit.

The agent card advertises the skills `review`, `improve`, `describe`, and `ask`, the name `"PR-Agent Solution Agent"`, a `version` taken from the running build, and the required `https://mosaico-project.eu/extensions/mosaico-observability` extension. Streaming is advertised as disabled. That flag is load-bearing: the reference agent chooses `message/send` or `message/stream` from it.

### Model and language

Leave `MODEL_NAME` unset to keep the product defaults: `config.model = "gpt-6.1-sol"` and `config.fallback_models = ["glm-5.3"]`. Responses use `config.response_language` (`zh-CN`).

If `MODEL_NAME` is set, it replaces `config.model` and **clears** `fallback_models`. A value without a `/` is sent as `openai/<MODEL_NAME>`. `MODEL_MAX_TOKENS` (default 32000) is the context budget for a model this build does not already know.

`API_BASE` and `API_KEY` are the OpenAI-compatible endpoint. They are required for a live probe whether or not you override the model.

### Request limits and caller authentication

The server uses `config.max_webhook_request_body_bytes` (5 MiB by default), including a streamed body with no valid Content-Length. Larger requests return HTTP 413 before JSON-RPC parsing or tool execution. `mosaico.routing_scan_max_chars` (default 65536, a positive integer) bounds URL and command detection per text segment. An incomplete token at the boundary is ignored. A supplied diff is still processed in full. Put the Gitee URL or the command near the start of the message.

Configure `mosaico.bearer_tokens` as a map of stable principal names to distinct opaque secrets, in secret settings or with Dynaconf's JSON environment syntax:

```bash
export MOSAICO__BEARER_TOKENS='@json {"reference-agent":"replace-with-generated-secret"}'
```

With a nonempty map, JSON-RPC and `/health` require `Authorization: Bearer <secret>`. Missing or invalid credentials return HTTP 401 before the body is read or the model runs. The agent-card GET stays public and advertises the bearer requirement without exposing secrets. Terminate TLS at the ingress and configure the caller to send its credential. Tasks, artifacts, histories, and context follow-ups are scoped to the configured principal. Callers that share a secret share that principal. Keep principal names stable when rotating secrets. An invalid map, including duplicate secrets, fails application startup.

The default empty map is anonymous access and shared task ownership for a trusted single-tenant network. Set authentication before exposing the service. These limits are not a retention policy, a rate limit, or a concurrency quota. The in-memory store keeps tasks until restart, and each authorized health probe performs a live completion.

Observability root and super task IDs must be canonical UUIDs. Invalid IDs are omitted independently. Valid IDs are lowercased before Langfuse trace context is produced. A metadata error does not fail the review.

For the bundled smoke test, pass the client credential as `MOSAICO_BEARER_TOKEN` when the server map is set. For the Compose overlay, set `PR_AGENT_BEARER_TOKEN` for the healthcheck and add `MOSAICO__BEARER_TOKENS` to the service `environment` through your secret configuration. Configure the reference caller's credential separately. Both probes still work without a token in anonymous mode.

### Run the standalone container

```bash
docker pull pragent/pr-agent:0.41.0-mosaico_agent
docker run -d --name pr-agent-mosaico -p 9000:9000 \
  -e API_BASE=https://your-openai-compatible-endpoint/v1 \
  -e API_KEY=sk-... \
  -e MODEL_NAME=gpt-6.1-sol \
  pragent/pr-agent:0.41.0-mosaico_agent

curl -s http://localhost:9000/.well-known/agent-card.json | python3 -m json.tool
```

`MODEL_NAME=gpt-6.1-sol` selects the default primary model and, as noted above, clears the `glm-5.3` fallback. Omit `MODEL_NAME` if the fallback must stay. Pin a version tag in production (see [Installation](./index.md)); the moving `mosaico_agent` tag tracks the newest build.

### Environment variables

| Variable | Default | Purpose |
| --- | --- | --- |
| `API_BASE` | — | Base URL of the OpenAI-compatible endpoint |
| `API_KEY` | — | API key for that endpoint |
| `MODEL_NAME` | unset | Model slug. Unset keeps `gpt-6.1-sol` and fallback `glm-5.3`. Set clears the fallback. |
| `HOST` | `0.0.0.0` | Bind address |
| `PORT` | `9000` | Bind port |
| `AGENT_CARD_HOST`, `AGENT_CARD_PORT` | unset | URL advertised in the card's `supportedInterfaces`. See the warning below. |
| `MODEL_MAX_TOKENS` | `32000` | Token budget when the model is not already known |
| `LANGFUSE_HOST`, `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY` | unset | Optional Langfuse tracing |

:::warning[AGENT_CARD_HOST / AGENT_CARD_PORT]
These two variables set the URL advertised in `supportedInterfaces`. Leave them unset and the card advertises `http://localhost:9000/`, which is reachable only from inside the container. Registration with MOSAICO can succeed, the repository stores that URL, and the reference agent fails later when it tries to route a task. Set them to the host and port the *caller* will use, then check:

```bash
curl -s http://<host>:<port>/.well-known/agent-card.json \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['supportedInterfaces'][0]['url'])"
```

If that prints a `localhost` URL, the deployment is wrong.
:::

### Deploy into the mosaico-demonstrator

[`docker/mosaico/`](https://github.com/the-pr-agent/pr-agent/tree/main/docker/mosaico) is the deployment bundle (compose overlay, registration template, env template, smoke test, LICENSE, and the README). To run the agent in the [mosaico-demonstrator](https://gitlab.eclipse.org/eclipse-research-labs/mosaico-project/mosaico-demonstrator):

1. Copy `docker-compose.pr-agent.yml` into the demonstrator's `compose/` directory, next to `base-definitions.yml`. The overlay's `extends:` paths resolve relative to that directory.
2. Copy `pr-agent-solution-agent.json` into the demonstrator's `docker/agent-registrations/` directory.
3. Append the "demonstrator overlay" block from `pr-agent.env.example` to the demonstrator's `env/llm.env`. Fill in `PR_AGENT_MODEL` (`gpt-6.1-sol` matches this build's primary model and clears the fallback). `PR_AGENT_HOST` may stay empty to use the demonstrator's auto-detected LAN IP. `PR_AGENT_PORT` defaults to `23000`.
4. Add `-f compose/docker-compose.pr-agent.yml` to the demonstrator's `01-compose.sh`, next to the other task-agent overlays.
5. Run `./01-compose.sh up -d`.

The registration template carries only `description`, `role`, `objective`, and `version`. The demonstrator's `register-agent.py` injects `name`, `a2aAgentCardUrl`, and `deployment.mode = ENDPOINT` at registration time. Two names are different on purpose: the repository entry is `pr-agent-solution-agent` (what `register-agent.py` looks up), and the card's `name` is `"PR-Agent Solution Agent"` (a display string).

### Verify

```bash
./smoke_test.sh
```

in the bundle directory ends in one of:

- **`SMOKE PASSED`** — no LLM credentials were available. The script pulled the pinned image, booted it, and checked the agent card.
- **`FULL ROUND-TRIP PASSED`** — credentials were present (a `.env` file beside the script, copied from `pr-agent.env.example`). The script also called `GET /health` and an A2A `SendMessage` review over an inline diff.

### Troubleshooting

- **The container stays `unhealthy` and registration never runs.** `/health` is a live model probe and returns `503` when credentials or the model are wrong. Check `API_BASE`, `API_KEY`, and `MODEL_NAME`.
- **The agent registers, but the reference agent never reaches it.** The card URL is `localhost`. See the `AGENT_CARD_HOST` / `AGENT_CARD_PORT` warning.
- **The registration container cannot fetch the agent card.** `01-compose.sh` falls back to `get_fallback_ip`, which can resolve to `localhost`. That address works from the host and fails from the registration container on the Docker network. Set `PR_AGENT_HOST` to an address reachable from inside Docker, such as the host's LAN IP or `host.docker.internal`.
- **A Gitee URL produces no review.** The server only fetches a public `.diff`. Private repositories, and enterprise hosts that do not serve that URL, need the unified diff pasted into the message.

### Keep reading

The [bundle README](https://github.com/the-pr-agent/pr-agent/blob/main/docker/mosaico/README.md) is the longer version of this page: upgrade steps, registration, and the env-var contract.
