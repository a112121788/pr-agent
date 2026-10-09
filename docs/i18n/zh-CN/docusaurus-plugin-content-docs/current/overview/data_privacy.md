---
title: "数据隐私"
sidebar_position: 2
---

Gitee PR-Agent 由你自行托管。它用你的令牌读取 Gitee 拉取请求，再把提示词发到你配置的模型端点。本构建不会为了训练模型保存拉取请求内容。

## 会送出什么

- 调用 Gitee API 使用主机令牌（`GITEE__PERSONAL_ACCESS_TOKEN`，或主机密钥文件里的 `[gitee].personal_access_token`）。仓库的 `.pr_agent.toml` 不能设置该令牌、API 基址或 Webhook 密钥。
- 提示词可以包含标题、描述、提交、diff、文件上下文、仓库指令，以及议题 API 成功返回时的 Gitee 议题标题和正文。
- 默认模型是 `gpt-6.1-sol`。调用失败后改走 `glm-5.3`。响应语言为 `zh-CN`（`config.response_language`）。
- 这些调用发生在你和 API 密钥背后的端点之间。见 [更换模型](../usage-guide/changing_a_model.md)。

## 不会送出什么

- Gitee API 返回 HTTP 404 的议题会被跳过。部分企业仓库网页上能看到议题，接口仍会这样。那段正文不会到达模型。见 [获取工单上下文](../core-abilities/fetching_ticket_context.md)。
- 行内评论发回 Gitee，不是另一次数据导出。锚点是 Gitee 的 diff `position`。

## 留在主机上的内容

- 令牌和模型密钥放在环境变量或主机密钥文件里。
- [MOSAICO A2A 服务器](../installation/mosaico_server.md) 只在内存里保留任务历史。重启即丢。这份历史不是训练语料。
