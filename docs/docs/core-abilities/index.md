---
title: "核心能力"
sidebar_position: 1
---

Gitee PR-Agent 审查 Gitee 上的拉取请求。下面这些能力决定提示词里放什么、过大的 diff 如何拆开，以及结果如何发回拉取请求：

- [代理技能](./agent_skills.md)
- [压缩策略](./compression_strategy.md)
- [动态上下文](./dynamic_context.md)
- [获取工单上下文](./fetching_ticket_context.md)
- [本地与全局元数据](./metadata.md)
- [自我反思](./self_reflection.md)

## 本构建的默认值

- 平台：仅 Gitee。安装见 [Gitee 安装指南](../installation/gitee.md)。其他 Git 托管不在支持范围内，见 [支持的平台](../overview/supported_platforms.md)。
- 模型：`glm-5.3`。备用模型是 `gpt-6.1-sol`。更换方式见 [更换模型](../usage-guide/changing_a_model.md)。
- 响应语言：`zh-CN`（`config.response_language`）。
- 大拉取请求：`/review` 和 `/describe` 默认分段处理。见 [压缩策略](./compression_strategy.md)。
- 行内评论锚定在 Gitee 的 diff `position` 上，从该文件补丁里第一个 `@@` 差异块头的下一行起算。无法映射的行会跳过。见 [Gitee 安装](../installation/gitee.md#已验证的行为)。
