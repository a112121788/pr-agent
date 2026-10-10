---
title: "支持的平台"
sidebar_position: 3
---

Gitee PR-Agent 只支持 Gitee。令牌、Webhook 和 Docker 服务按 [Gitee 安装指南](../installation/gitee.md) 配置。

命令行接受 Gitee 拉取请求地址，例如 `https://gitee.com/<owner>/<repo>/pulls/<number>`。

这次审查的默认值：

- 模型 `glm-5.3`，备用 `gpt-6.1-sol`。见 [更换模型](../usage-guide/changing_a_model.md)。
- 响应语言 `zh-CN`。
- 大拉取请求分段处理。见 [压缩策略](../core-abilities/compression_strategy.md)。
- 行内评论使用 Gitee 的 diff `position`。

GitHub、GitLab、Bitbucket、Azure DevOps、Gitea、Gerrit 和 CodeCommit 不可用。不要把命令行或 Webhook 指到这些托管。
