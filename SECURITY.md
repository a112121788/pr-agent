# 安全策略

Gitee PR-Agent 是审核工厂的核心机，只为 Gitee 拉取请求收集审查证据。

本文描述开源项目 Gitee PR-Agent 的安全策略，不覆盖独立商业产品 [Qodo](https://www.qodo.ai/)。

## 自托管

使用你自己的模型密钥时，安全关系存在于你和模型服务之间。Gitee PR-Agent 不会把代码发送到项目运营的服务器。

当前部署方式：

- 本地命令行
- Gitee Webhook 服务 `gitee_app`

镜像发布在：

```text
ecloud-tcr.tencentcloudcr.com/ecloud_project/pr-agent
```

`latest` 会随新构建移动。需要固定版本时，使用提交标签或镜像摘要。

```bash
docker buildx imagetools inspect \
  ecloud-tcr.tencentcloudcr.com/ecloud_project/pr-agent:latest \
  --format '{{.Manifest.Digest}}'
```

## 支持的版本

安全更新面向当前仓库的最新提交和由它构建的镜像。历史 Docker Hub 标签不再接收本仓库的新镜像。

## 报告漏洞

请通过 GitHub 的私人漏洞报告提交：

[**报告漏洞**](https://github.com/The-PR-Agent/pr-agent/security/advisories/new)

请包含漏洞描述、复现步骤和受影响版本。不要先开公开议题，以免修复发布前暴露漏洞。
