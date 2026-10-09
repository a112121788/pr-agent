---
title: "自定义 CA 与自签名证书"
sidebar_position: 11
---

当 PR-Agent 运行在会检查 TLS 的代理之后，或者 Gitee 主机、模型端点使用私有证书时，HTTPS 可能因 `certificate verify failed` 失败。信任分两部分：git 和 HTTP 客户端使用的 CA 证书包，以及确实会读取该证书包的 LiteLLM 传输层。

Webhook 的安装步骤见 [Gitee 集成指南](../installation/gitee.md)。仓库的 `.pr_agent.toml` 不能覆盖 `gitee.ssl_ca_cert` 或 `gitee.skip_ssl_verification`。

### 用于 CA 信任的环境变量 {#environment-variables-for-ca-trust}

PR-Agent 在构建 git clone 环境时按下列顺序读取三个环境变量。第一个**已设置**的变量生效。如果它指向的文件不存在，PR-Agent 会记录警告，并且不为 git 配置证书包，而不会继续尝试下一个变量：

| 变量 | 范围 | 说明 |
| --- | --- | --- |
| `SSL_CERT_FILE` | git clone 与 Python `requests` | 优先使用。大多数 Python SSL 上下文都会读取。 |
| `REQUESTS_CA_BUNDLE` | git clone 与 Python `requests` | 回退。`requests` 会直接使用。 |
| `GIT_SSL_CAINFO` | 仅 git clone | 最后手段。前两个都未设置时由 git 使用。 |

如果设置了多个变量且路径不同，PR-Agent 会记录警告并按上表的优先级选择。实践中三个变量应指向同一份 PEM 文件。

```bash
export SSL_CERT_FILE=/etc/ssl/certs/corporate-ca-bundle.crt
```

这些变量来自进程环境。请在运行 `gitee_app` 的 shell 或容器里导出。`.secrets.toml` 的 `[env]` 节不会进入 `os.environ`，不能用来设置它们。

### Gitee 主机证书 {#gitee-host-certificate}

Gitee API 客户端的 CA 包在主机上设置：

```bash
GITEE__SSL_CA_CERT=/etc/ssl/certs/corporate-ca-bundle.crt
```

也可以在主机配置的 `[gitee]` 中设置 `ssl_ca_cert`。仅对受信任的私有端点设置 `GITEE__SKIP_SSL_VERIFICATION=true`。在公网上关闭校验会接受任意证书。

`GITEE__SSL_CA_CERT` 只配置 Gitee API 客户端，不能代替模型调用和 git clone 所用的 `SSL_CERT_FILE`。

### LiteLLM 传输回退 {#litellm-transport-fallback}

LiteLLM 默认使用 aiohttp，而 aiohttp 不遵循标准 CA 环境变量。`litellm.disable_aiohttp` 会让 LiteLLM 改用 httpx，httpx 会读取 `SSL_CERT_FILE` 和 `SSL_CERT_DIR`。httpx 不读取 `REQUESTS_CA_BUNDLE`，因此模型调用必须设置 `SSL_CERT_FILE`。

```toml
[litellm]
disable_aiohttp = true
```

处理程序在启动时读取该值一次。请在进程启动前把它写进主机配置。

### 检查清单 {#putting-it-all-together}

1. 导出指向 CA 包的 `SSL_CERT_FILE`。`REQUESTS_CA_BUNDLE` 和 `GIT_SSL_CAINFO` 只覆盖 git clone。
2. 为 Gitee API 把 `GITEE__SSL_CA_CERT` 设为同一份证书包。
3. 设置 `litellm.disable_aiohttp = true`，让模型调用使用该证书包。
4. 除非端点是私有且受信任的，否则不要设置 `GITEE__SKIP_SSL_VERIFICATION`。
