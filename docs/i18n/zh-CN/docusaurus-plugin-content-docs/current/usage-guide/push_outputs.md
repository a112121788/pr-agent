---
title: "将输出推送到外部接收端"
sidebar_position: 7
---

`[push_outputs]` 功能把已完成的工具输出路由到外部接收端——stdout、JSONL 文件、通用 webhook、Slack 或 Telegram——而不调用 Git 提供商 API。它默认关闭，并且是在正常发布之外额外进行的：工具完成后，作为拉取请求评论发布的同一结果，也会发送到已配置的接收端。

## 会推送什么 {#what-gets-pushed}

每次完成的工具运行发出一条记录。目前会发出记录的工具有：

| 工具 | 记录中的 `type` |
|---|---|
| `/review` | `review` |
| `/describe` | `describe` |
| `/improve` | `improve` |

记录是一个 JSON 对象：

```json
{
  "type": "review",
  "timestamp": "2026-09-08T14:03:21+00:00",
  "payload": {},
  "markdown": "# PR Reviewer Guide ..."
}
```

- `type`——产出该输出的工具
- `timestamp`——运行完成时间，UTC，ISO-8601
- `payload`——结构化的工具结果
- `markdown`——渲染后的评论文本；工具会产生评论文本时才出现

## 配置 {#configuration}

默认值定义在[配置文件](https://github.com/the-pr-agent/pr-agent/blob/main/pr_agent/settings/configuration.toml)末尾：

```toml
[push_outputs]
enable = false
channels = []                          # any of: "stdout", "file", "webhook", "slack", "telegram"
file_path = "pr-agent-outputs/reviews.jsonl"
webhook_url = ""                       # must be an absolute https:// URL
slack_webhook_url = ""                 # Slack Incoming Webhook; must be an absolute https:// URL
telegram_bot_token = ""                # Telegram bot token; host-only secret
telegram_chat_id = ""                  # destination chat for the Telegram bot
```

- `enable`——总开关（默认 `false`）。为 `false` 时不发送任何内容。
- `channels`——要使用哪些接收端。至少在此列出一个通道后才会发送。
- `file_path`——`file` 通道追加写入的文件。
- `webhook_url`——`webhook` 通道把通用记录 POST 到的端点。
- `slack_webhook_url`——Slack Incoming Webhook URL，`slack` 通道向它提交 `{"text": ...}` 载荷。
- `telegram_bot_token`——`telegram` 通道使用的机器人令牌。请放在主机密钥中，不要放进仓库文件。
- `telegram_chat_id`——接收 Telegram 消息的聊天。

:::danger[仅主机配置]
整个 `[push_outputs]` 节**仅限主机**。仓库不能设置这些键：
通过仓库本地 `.pr_agent.toml` 提供的键会被丢弃，CLI 参数
（`--push_outputs.webhook_url=...`、`--push_outputs={...}`）也会被阻止。这可以防止
拉取请求把审查输出重定向到攻击者控制的主机、访问
内部端点，或追加写入任意主机文件。请在
PR-Agent 主机自己的设置中配置这些值。
:::

### URL 要求 {#url-requirements}

`webhook_url` 和 `slack_webhook_url` 必须是带主机的绝对 `https://` URL。任何其他
值（例如普通的 `http://` URL 或裸路径）都会被忽略并给出警告。要求
HTTPS 是为了避免审查文本（其中可能引用私有代码）走明文传输。主机
有意不做限制，因此自托管收集器和兼容 Slack 的端点
（Mattermost、Rocket.Chat）都是合法目标。

警告日志只记录设置名，绝不记录 URL 值，因为 webhook 或 Slack URL 本身就是
凭据。

## 通道 {#channels}

| 通道 | 行为 |
|---|---|
| `stdout` | 向 stdout 打印一行 JSON（该记录）。 |
| `file` | 每次运行向 `file_path` 追加一行 JSON（JSONL），并按需创建父目录。 |
| `webhook` | 把通用记录作为 JSON POST 到 `webhook_url`（超时 5 秒，不跟随重定向）。 |
| `slack` | 向 Slack Incoming Webhook POST `{"text": ...}`；文本为 markdown，若工具不产生 markdown，则为载荷 JSON。 |
| `telegram` | 把 markdown（没有 markdown 时则为载荷 JSON）作为纯文本发送到 `telegram_chat_id`。文本截断到最多 4096 个 UTF-16 码元，且不会拆开代理对。 |

本地通道（`stdout`、`file`）在网络通道（`webhook`、`slack`、`telegram`）之前运行，网络
投递从不跟随重定向。每个已配置的目标都会独立尝试，因此某一处失败
不会阻止后续目标接收输出。

### Telegram {#telegram}

在主机设置中启用该通道，并通过主机环境提供机器人令牌：

```toml
[push_outputs]
enable = true
channels = ["telegram"]
telegram_chat_id = "<destination-chat-id>"
```

在主机的密钥环境中把 `PUSH_OUTPUTS__TELEGRAM_BOT_TOKEN` 设为你的机器人令牌。
该机器人必须能够向目标聊天发送消息。缺少凭据时会跳过投递，
警告中只写出缺失的设置名。

请求使用固定主机 `https://api.telegram.org`，超时 5 秒，且不跟随重定向。
令牌在请求路径中做 URL 编码，绝不会出现在 PR-Agent 的警告消息里。
不设置 Telegram 解析模式：Markdown 语法按纯文本发送。更长的输出会被截断，
而不是拆成多条消息；其他已配置的通道仍会收到完整输出。

## 错误处理 {#error-handling}

失败是非致命的：`push_outputs` 从不抛出异常，因此接收端中断不会打断审查
流程。异常和非 2xx HTTP 响应会连同目标一起记录，且只记录异常
类型或状态码，因为请求错误消息可能嵌入（含密钥的）URL。

## 扩展投递 {#extending-delivery}

`pr_agent/algo/run_output.py` 中的 `push_outputs()` 只构建一次记录，并隔离每个所选目标的失败。投递策略位于 `pr_agent/algo/output_sinks.py`：
每个策略实现 `OutputSink.send(record, cfg)`，`create_output_sink()` 根据 `OUTPUT_SINK_TYPES` 选择策略。注册表顺序决定投递顺序，本地写入在前；
重复的通道条目仍然只投递一次。

要添加目标，请实现其策略并注册，然后补充所需的仅主机
设置、文档和提供商专用测试。HTTP 策略必须校验目标，
并保持共享的 HTTPS、超时、重定向和密钥安全日志策略。提供商专用的
载荷格式应放在策略中，这样通用 webhook 记录保持不变。

这个接口用来组织各提供商的实现；它并不省去维护
其 API 的工作。重试、限流、幂等和后台投递是各自独立的策略
决定，并不是由这一结构引入的。
