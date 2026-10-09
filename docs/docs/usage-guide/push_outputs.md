---
title: "Push outputs to external sinks"
sidebar_position: 7
---

`[push_outputs]` copies finished tool output to external sinks — stdout, a JSONL file, a generic webhook, Slack, or Telegram — without calling the Gitee API. It is off by default, and it is additive: the comment published on the Gitee pull request is still published, and the same result is also sent to the configured sinks.

Gitee cannot `push_code`. This feature does not commit files. `/update_changelog` remains a comment, and that comment's text can also be copied to a sink when the tool emits a record.

## What gets pushed {#what-gets-pushed}

Each finished tool run emits one record. The tools that emit are:

| Tool | `type` in the record |
| --- | --- |
| `/review` | `review` |
| `/describe` | `describe` |
| `/improve` | `improve` |

A record is a JSON object:

```json
{
  "type": "review",
  "timestamp": "2026-09-08T14:03:21+00:00",
  "payload": {},
  "markdown": "# PR Reviewer Guide ..."
}
```

- `type` — which tool produced the output
- `timestamp` — completion time, UTC, ISO-8601
- `payload` — the structured tool result
- `markdown` — the rendered comment text, when the tool produces one

## Configuration {#configuration}

Defaults are at the end of the [configuration file](https://github.com/the-pr-agent/pr-agent/blob/main/pr_agent/settings/configuration.toml):

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

- `enable` — master switch (default `false`). When `false`, nothing is emitted.
- `channels` — which sinks to use. Nothing is emitted until at least one channel is listed.
- `file_path` — the file the `file` channel appends to.
- `webhook_url` — the endpoint the `webhook` channel POSTs the generic record to.
- `slack_webhook_url` — a Slack Incoming Webhook URL. The `slack` channel posts `{"text": ...}`.
- `telegram_bot_token` — bot token for the `telegram` channel. Keep it in host secrets.
- `telegram_chat_id` — the chat that receives Telegram messages.

:::danger[Host-only configuration]
The whole `[push_outputs]` section is **host-only**. Keys in a repository `.pr_agent.toml` are dropped, and CLI arguments (`--push_outputs.webhook_url=...`, `--push_outputs={...}`) are blocked. A pull request must not be able to redirect review output to another host or append to an arbitrary file. Set these values on the host that runs the CLI or the `gitee_app` image `ecloud-tcr.tencentcloudcr.com/ecloud_project/pr-agent:latest`.
:::

### URL requirements {#url-requirements}

`webhook_url` and `slack_webhook_url` must be absolute `https://` URLs with a host. Any other value, including plain `http://`, is ignored with a warning. HTTPS keeps review text, which can quote private code, off plaintext transports. The host is not restricted, so a self-hosted collector or a Slack-compatible endpoint is a valid target.

Warnings log the setting name, never the URL, because a webhook URL is a credential.

## Channels {#channels}

| Channel | Behaviour |
| --- | --- |
| `stdout` | Prints one JSON line (the record) to stdout. |
| `file` | Appends one JSON line per run (JSONL) to `file_path`, creating parent directories as needed. |
| `webhook` | POSTs the generic record as JSON to `webhook_url` (5-second timeout, redirects not followed). |
| `slack` | POSTs `{"text": ...}` to a Slack Incoming Webhook. The text is the markdown, or the payload JSON when the tool produces no markdown. |
| `telegram` | Sends the markdown, or the payload JSON when no markdown is present, as plain text to `telegram_chat_id`. Text is truncated to at most 4096 UTF-16 code units without splitting surrogate pairs. |

Local channels (`stdout`, `file`) run before network channels (`webhook`, `slack`, `telegram`). Network posts never follow redirects. Each destination is attempted independently, so one failure does not block the others.

### Telegram {#telegram}

```toml
[push_outputs]
enable = true
channels = ["telegram"]
telegram_chat_id = "<destination-chat-id>"
```

Set `PUSH_OUTPUTS__TELEGRAM_BOT_TOKEN` in the host environment. The bot must be allowed to message that chat. Missing credentials skip delivery with a warning that names only the missing setting.

Requests use `https://api.telegram.org`, a 5-second timeout, and no redirects. The token is URL-encoded in the path and is never written into PR-Agent warnings. No parse mode is set, so Markdown is sent as plain text. Longer output is truncated, not split. Other configured channels still receive the complete output.

## Error handling {#error-handling}

Failures are non-fatal. `push_outputs` never raises, so a sink outage does not stop the Gitee comment. Exceptions and non-2xx responses are logged with the destination and only the exception type or status code, because the error text can embed the secret-bearing URL.

## Extending delivery {#extending-delivery}

`push_outputs()` in `pr_agent/algo/run_output.py` builds the record once and isolates failures for each destination. Strategies live in `pr_agent/algo/output_sinks.py`. Each implements `OutputSink.send(record, cfg)`, and `create_output_sink()` selects one from `OUTPUT_SINK_TYPES`. Registry order is delivery order, with local writes first. Duplicate channel entries still deliver once.

To add a destination, implement the strategy, register it, and add host-only settings plus tests. HTTP strategies must keep the shared HTTPS, timeout, redirect, and secret-safe logging rules. Provider-specific payload formatting belongs in the strategy, so the generic webhook record stays unchanged.

Retries, rate limits, idempotency, and background delivery are not part of this interface.
