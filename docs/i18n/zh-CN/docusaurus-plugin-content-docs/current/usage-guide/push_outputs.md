---
title: "将输出推送到外部接收端"
sidebar_position: 7
---

`[push_outputs]` 把已完成的工具输出复制到外部接收端——stdout、JSONL 文件、通用 webhook、Slack 或 Telegram——而不调用 Gitee API。它默认关闭，并且是额外进行的：发表到 Gitee 拉取请求上的评论仍然会发表，同一结果也会发到已配置的接收端。

Gitee 不能 `push_code`。此功能不会提交文件。`/update_changelog` 仍然是一条评论；当该工具发出记录时，评论正文也可以被复制到接收端。

## 会推送什么 {#what-gets-pushed}

每次完成的工具运行发出一条记录。目前会发出记录的工具有：

| 工具 | 记录中的 `type` |
| --- | --- |
| `/review` | `review` |
| `/describe` | `describe` |
| `/improve` | `improve` |

一条记录是一个 JSON 对象：

```json
{
  "type": "review",
  "timestamp": "2026-09-08T14:03:21+00:00",
  "payload": {},
  "markdown": "# PR Reviewer Guide ..."
}
```

- `type` — 产生输出的工具
- `timestamp` — 完成时间，UTC，ISO-8601
- `payload` — 结构化的工具结果
- `markdown` — 渲染后的评论文本；工具产生评论文本时才有

## 配置 {#configuration}

默认值在[配置文件](https://github.com/the-pr-agent/pr-agent/blob/main/pr_agent/settings/configuration.toml)末尾：

```toml
[push_outputs]
enable = false
channels = []                          # 可选："stdout"、"file"、"webhook"、"slack"、"telegram"
file_path = "pr-agent-outputs/reviews.jsonl"
webhook_url = ""                       # 必须是绝对的 https:// URL
slack_webhook_url = ""                 # Slack Incoming Webhook；必须是绝对的 https:// URL
telegram_bot_token = ""                # Telegram 机器人令牌；仅限主机的密钥
telegram_chat_id = ""                  # Telegram 机器人的目标会话
```

- `enable` — 总开关（默认 `false`）。为 `false` 时不发出任何内容。
- `channels` — 使用哪些接收端。至少列出一个通道后才会发出。
- `file_path` — `file` 通道追加写入的文件。
- `webhook_url` — `webhook` 通道投递通用记录的端点。
- `slack_webhook_url` — Slack Incoming Webhook URL。`slack` 通道投递 `{"text": ...}`。
- `telegram_bot_token` — `telegram` 通道使用的机器人令牌。请放在主机密钥中。
- `telegram_chat_id` — 接收 Telegram 消息的会话。

:::danger[仅限主机的配置]
整个 `[push_outputs]` 节**仅限主机**。仓库 `.pr_agent.toml` 里的键会被丢弃，CLI 参数（`--push_outputs.webhook_url=...`、`--push_outputs={...}`）也会被阻止。拉取请求不能把审查输出重定向到其他主机，也不能追加到任意文件。请在运行 CLI 或镜像 `ecloud-tcr.tencentcloudcr.com/ecloud_project/pr-agent:latest`（`gitee_app`）的主机上设置这些值。
:::

### URL 要求 {#url-requirements}

`webhook_url` 和 `slack_webhook_url` 必须是带主机的绝对 `https://` URL。其他值，包括普通的 `http://`，会被忽略并记录警告。HTTPS 可以避免可能引用私有代码的审查文本走明文传输。主机本身不受限制，因此自建收集器或兼容 Slack 的端点都是合法目标。

警告只记录设置名，绝不记录 URL 值，因为 webhook URL 本身就是凭据。

## 通道 {#channels}

| 通道 | 行为 |
| --- | --- |
| `stdout` | 向 stdout 打印一行 JSON（该记录）。 |
| `file` | 每次运行向 `file_path` 追加一行 JSON（JSONL），并按需创建父目录。 |
| `webhook` | 把通用记录以 JSON POST 到 `webhook_url`（超时 5 秒，不跟随重定向）。 |
| `slack` | 向 Slack Incoming Webhook POST `{"text": ...}`。文本是 markdown；工具没有 markdown 时则为 payload JSON。 |
| `telegram` | 把 markdown（没有 markdown 时为 payload JSON）作为纯文本发到 `telegram_chat_id`。文本最多截断到 4096 个 UTF-16 码元，且不会拆开代理对。 |

本地通道（`stdout`、`file`）先于网络通道（`webhook`、`slack`、`telegram`）运行。网络投递从不跟随重定向。每个目标独立尝试，因此一个失败不会挡住其他目标。

### Telegram {#telegram}

```toml
[push_outputs]
enable = true
channels = ["telegram"]
telegram_chat_id = "<destination-chat-id>"
```

在主机环境中设置 `PUSH_OUTPUTS__TELEGRAM_BOT_TOKEN`。机器人必须能向该会话发消息。缺少凭据时会跳过投递，警告里只写出缺少的设置名。

请求使用 `https://api.telegram.org`，超时 5 秒，不跟随重定向。令牌在路径中做 URL 编码，绝不会写进 PR-Agent 的警告。不设置解析模式，因此 Markdown 按纯文本发送。更长的输出会被截断，而不是拆成多条消息。其他已配置的通道仍会收到完整输出。

## 错误处理 {#error-handling}

失败是非致命的。`push_outputs` 从不抛出异常，因此接收端中断不会阻止 Gitee 评论。异常和非 2xx 响应会连同目标一起记录，并且只记录异常类型或状态码，因为错误文本可能包含带密钥的 URL。

## 扩展投递 {#extending-delivery}

`pr_agent/algo/run_output.py` 中的 `push_outputs()` 只构建一次记录，并隔离每个目标的失败。策略位于 `pr_agent/algo/output_sinks.py`。每个策略实现 `OutputSink.send(record, cfg)`，`create_output_sink()` 从 `OUTPUT_SINK_TYPES` 中选择。注册顺序就是投递顺序，本地写入在前。重复的通道条目仍然只投递一次。

要增加目标，请实现策略、登记它，并加上仅限主机的设置和测试。HTTP 策略必须保持共享的 HTTPS、超时、重定向和避免泄露密钥的日志规则。特定提供商的载荷格式属于策略本身，这样通用 webhook 记录才保持不变。

重试、速率限制、幂等和后台投递不属于这个接口。
