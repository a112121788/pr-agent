---
title: "自定义 CA 与自签名证书"
sidebar_position: 11
---

当 PR-Agent 运行在会检查 TLS 的企业代理之后，或访问使用自签名证书的服务器时，对 LLM 提供商的 HTTPS 调用和 git 操作可能因 `certificate verify failed` 错误而失败。修复需要两件事：告诉 HTTP 客户端信任哪一份 CA 证书包，并让 LiteLLM 使用遵循该证书包的传输层。

### 用于 CA 信任的环境变量 {#environment-variables-for-ca-trust}

PR-Agent 在构建 git clone 环境时按下列顺序读取三个环境变量。第一个**已设置**的变量生效；如果它指向的文件不存在，PR-Agent 会记录警告，并且不为 git 配置证书包，而不是继续尝试下一个变量：

| 变量 | 作用范围 | 说明 |
|---|---|---|
| `SSL_CERT_FILE` | git clone 与 Python `requests` | 首选。大多数 Python SSL 上下文都会使用。 |
| `REQUESTS_CA_BUNDLE` | git clone 与 Python `requests` | 回退。`requests` 库会直接遵循。 |
| `GIT_SSL_CAINFO` | 仅 git clone | 最后手段。另外两个都不存在时由 git 使用。 |

如果设置了多个变量且指向不同文件，PR-Agent 会记录警告，并按上面的优先级选取一个。实践中这三个变量应指向同一个 PEM 文件。

示例（运行器环境或 shell 配置）：

```bash
export SSL_CERT_FILE=/etc/ssl/certs/corporate-ca-bundle.crt
```

这些变量从进程环境读取，因此必须在运行器或 shell 配置中导出；`.secrets.toml` 的 `[env]` 节**不会**进入 `os.environ`，不能用来设置它们。

### LiteLLM 传输回退 {#litellm-transport-fallback}

默认情况下 LiteLLM 使用 aiohttp 发起 HTTP 调用，而 aiohttp 不遵循标准 CA 环境变量。设置 `litellm.disable_aiohttp` 会使 LiteLLM 回退到 httpx，后者会读取 `SSL_CERT_FILE`（以及 `SSL_CERT_DIR`）。httpx 不读取 `REQUESTS_CA_BUNDLE`，因此 LLM 调用特别需要 `SSL_CERT_FILE`。

```toml
[litellm]
disable_aiohttp = true
```

该设置在 LiteLLM 处理器初始化时只读取一次，因此必须在进程启动前就存在（运行器环境或 `.secrets.toml`，而不是运行时覆盖）。

### `gitlab.ssl_verify` 的作用范围 {#scope-of-gitlabssl_verify}

`gitlab.ssl_verify` 设置（或环境变量 `gitlab__SSL_VERIFY`）只传给与 GitLab API 通信的 python-gitlab 客户端。它**不会**影响 LLM 调用、git clone 操作，或进程中的任何其他 HTTPS 客户端。如果看到的是来自 LiteLLM 或 git clone 的证书错误，请改用上面的环境变量。

### 汇总 {#putting-it-all-together}

对于使用自定义 CA、位于企业代理之后的运行器：

1. 导出指向你的 CA 证书包的 `SSL_CERT_FILE`。`REQUESTS_CA_BUNDLE` 和 `GIT_SSL_CAINFO` 只覆盖 git clone。
2. 在配置中设置 `litellm.disable_aiohttp = true`。
3. 如果还使用 GitLab API，让 `gitlab.ssl_verify` 指向同一份证书包，供 python-gitlab 客户端使用。
