---
title: "Custom CA and Self-Signed Certificates"
sidebar_position: 11
---

When PR-Agent runs behind a TLS-inspecting proxy, or calls a Gitee host or model endpoint that uses a private certificate, HTTPS can fail with `certificate verify failed`. Trust has two parts: the CA bundle used by git and the HTTP clients, and a LiteLLM transport that actually reads that bundle.

The webhook install is in the [Gitee integration guide](../installation/gitee.md). A repository `.pr_agent.toml` cannot override `gitee.ssl_ca_cert` or `gitee.skip_ssl_verification`.

### Environment variables for CA trust

PR-Agent reads three environment variables when it builds the git clone environment. The first one that is **set** wins. If it points at a file that does not exist, PR-Agent logs a warning and configures no bundle for git, rather than falling through to the next variable:

| Variable | Scope | Notes |
| --- | --- | --- |
| `SSL_CERT_FILE` | git clone and Python `requests` | Preferred. Used by most Python SSL contexts. |
| `REQUESTS_CA_BUNDLE` | git clone and Python `requests` | Fallback. Honoured by `requests` directly. |
| `GIT_SSL_CAINFO` | git clone only | Last resort, used by git when the other two are absent. |

If more than one variable is set and the paths differ, PR-Agent logs a warning and keeps the precedence above. Point all three at the same PEM file.

```bash
export SSL_CERT_FILE=/etc/ssl/certs/corporate-ca-bundle.crt
```

These variables come from the process environment. Export them in the shell or container that runs `gitee_app`. A `.secrets.toml` `[env]` section does not reach `os.environ` and cannot set them.

### Gitee host certificate

For the Gitee API client, set the CA bundle on the host:

```bash
GITEE__SSL_CA_CERT=/etc/ssl/certs/corporate-ca-bundle.crt
```

The same value can live under `[gitee]` as `ssl_ca_cert` in the host configuration. Set `GITEE__SKIP_SSL_VERIFICATION=true` only for a trusted private endpoint. Leaving verification off on a public network accepts any certificate.

`GITEE__SSL_CA_CERT` configures the Gitee API client. It does not replace `SSL_CERT_FILE` for model calls or git clones.

### LiteLLM transport fallback

LiteLLM uses aiohttp by default, and aiohttp does not honour the standard CA environment variables. `litellm.disable_aiohttp` makes LiteLLM use httpx, which reads `SSL_CERT_FILE` and `SSL_CERT_DIR`. httpx does not read `REQUESTS_CA_BUNDLE`, so the model call needs `SSL_CERT_FILE`.

```toml
[litellm]
disable_aiohttp = true
```

The handler reads this once at startup. Put it in the host configuration before the process starts.

### Checklist

1. Export `SSL_CERT_FILE` to the CA bundle. `REQUESTS_CA_BUNDLE` and `GIT_SSL_CAINFO` cover git clone only.
2. Set `GITEE__SSL_CA_CERT` to that same bundle for the Gitee API.
3. Set `litellm.disable_aiohttp = true` so model calls use the bundle.
4. Do not set `GITEE__SKIP_SSL_VERIFICATION` unless the endpoint is private and trusted.
