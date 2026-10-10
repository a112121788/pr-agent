---
title: "常见问题"
sidebar_position: 1
---

<details>
<summary>问：Gitee PR-Agent 能代替人工审查者吗？</summary>

#### 回答：<span style="display:none;">1</span>

不能。它协助作者和审查者，不会批准 Gitee 拉取请求。

拉取请求越长，这种协助越有用：diff 变大后，审查者花在每一行上的时间会变少。决定权仍在拉取请求上的人：

1. 保留原来的标题。
2. 把作者的描述放在生成的描述上面。
3. 不会批准。批准仍由审查者完成。
4. 代码建议是可选的。它们用来标出缺陷、疏漏和仓库约定，不会自己提交。

拉取请求打开后会运行 `/describe`、`/review` 和 `/improve`。在拉取请求上评论可以再次运行工具。见 [Gitee 安装指南](../installation/gitee.md) 和 [在线用法](../usage-guide/automations_and_usage.md#online-usage)。

</details>

___

<details>
<summary>问：我收到了不正确或不相关的建议。为什么？</summary>

#### 回答：<span style="display:none;">2</span>

- 默认模型是 `glm-5.3`，备用模型是 `gpt-6.1-sol`。两者都会出错。先读再决定要不要改。评论使用 `zh-CN`。
- 有价值的情况是建议抓住了 diff 里的错误。花半分钟看完列表通常值得，即使有些条目不适用。
- `/improve` 会给自己的列表打分，并丢掉它标成错误的条目。见 [自我反思](../core-abilities/self_reflection.md)。
- 评论故意分成几层。先看分类，再看一行摘要，摘要相关时再展开。
- 用 [`extra_instructions`](../tools/improve.mdx#额外说明和仓库文件) 告诉模型这个仓库在意什么。

</details>

___

<details>
<summary>问：怎样让建议更贴合仓库？</summary>

#### 回答：<span style="display:none;">3</span>

为仓库设置 `extra_instructions` 和最佳实践文本。见 [附加指令与最佳实践](../tools/improve.mdx#额外说明和仓库文件)。

主机级 [代理技能](../core-abilities/agent_skills.md) 可以把同类指引用到多个 Gitee 仓库。仓库不能把 `skills.paths` 指到主机文件系统。

</details>

___

<details>
<summary>问：会保存我的代码，或拿去训练模型吗？</summary>

#### 回答：<span style="display:none;">4</span>

本构建不会为了训练留下拉取请求内容。提示词发到你配置的模型端点（`glm-5.3`，失败后备用 `gpt-6.1-sol`）。

见 [数据隐私](../overview/data_privacy.md)。

</details>

___

<details>
<summary>问：大拉取请求怎么审查？</summary>

#### 回答：<span style="display:none;">5</span>

默认分段。

- `/review` 的 `enable_large_pr_chunking = true`，最多 `max_number_of_calls` 次分段调用（默认 3），再合并成一条评论。
- `/describe` 的 `enable_large_pr_handling = true`，会再调用并合并，从而覆盖更多文件。

仍然放不下的文件会写在审查覆盖范围页脚里。主模型是 `glm-5.3`；失败的分段可以改走 `gpt-6.1-sol`。细节见 [压缩策略](../core-abilities/compression_strategy.md) 和 [其他选项](../tools/review.md#其他选项)。

</details>

___

<details>
<summary>问：行内评论锚在哪里？</summary>

#### 回答：<span style="display:none;">6</span>

Gitee 用 diff `position` 锚定行内评论：该文件补丁里，从第一个 `@@` 差异块头的下一行起算的行号。Gitee PR-Agent 根据拉取请求 diff 计算这个下标。文件或行映射不上时，评论不会发出。

见 Gitee 安装指南里的 [已验证的行为](../installation/gitee.md#已验证的行为)。

</details>

___

<details>
<summary>问：引用的 Gitee 议题被忽略了。为什么？</summary>

#### 回答：<span style="display:none;">7</span>

议题读取已经实现。拉取请求可以用 Gitee 议题 URL、`owner/repo#编号`、`#编号`，或 `123-fix-bug` 这样的分支名指向议题。命令随后调用 `GET /repos/{owner}/{repo}/issues/{number}`。

部分企业仓库即使浏览器能打开议题页，该 API 仍返回 HTTP 404。这条议题会被跳过，`/describe` 和 `/review` 在没有它的标题和正文的情况下继续。若仍希望需求进入提示词，把需求写进拉取请求描述。

见 [获取工单上下文](../core-abilities/fetching_ticket_context.md)。

</details>

___

<details>
<summary>问：审查工作量分数能校准吗？</summary>

#### 回答：<span style="display:none;">8</span>

可以。用 `pr_reviewer.extra_instructions` 说明每一档对你们团队意味着什么。见 [其他选项](../tools/review.md#其他选项)。

示例：

- 工作量 1：不到 30 分钟
- 工作量 2：30–60 分钟
- 工作量 3：60–90 分钟

1–5 分是相对的，用来让更小的拉取请求先被看。它不是计时器。

</details>

___

<details>
<summary>问：怎样减少噪音？</summary>

#### 回答：<span style="display:none;">9</span>

默认已经收过一轮：

- 拉取请求打开后只跑三个结构化工具：`/describe`、`/review`、`/improve`，而不是一串状态评论。
- `/improve` 的建议在一张表里。只有算出 Gitee diff `position` 时才会发成行内评论。
- 文件导览默认折叠。
- 大 diff 合并成一条审查，而不是每个文件一条。见 [压缩策略](../core-abilities/compression_strategy.md)。

若对某个仓库仍然太多：

- 提高 [建议分数阈值](../tools/improve.mdx#配置)。
- 用 [`extra_instructions`](../tools/improve.mdx#额外说明和仓库文件) 收窄模型。
- 把 `gitee.pr_commands` 设为 `[]`，停掉自动工具。以 `/` 开头的评论命令仍然会运行。见 [自动反馈](../usage-guide/automations_and_usage.md#pr-agent-automatic-feedback)。

若要保留自动审查，又想让建议更容易落地，见 [发布内容](../tools/improve.mdx#发布内容) 和 [会生成多少条](../tools/improve.mdx#会生成多少条)。

</details>

___
