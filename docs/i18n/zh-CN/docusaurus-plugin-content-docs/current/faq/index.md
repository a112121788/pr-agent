---
title: "常见问题"
sidebar_position: 1
---

<details>
<summary>问：PR-Agent 能否替代人工审查者？</summary>

#### 回答：<span style="display:none;">1</span>

PR-Agent 旨在协助而非替代人工审查者。

审查拉取请求既繁琐又耗时，常被看作一项「杂务」。此外，拉取请求越长，相对反馈往往越短，因为过长的拉取请求会在技术难度和实际审查时间上同时压垮审查者。
PR-Agent 希望缓解这些痛点，并同时协助、增强拉取请求作者与审查者的能力。

不过，PR-Agent 内置了保障措施，确保开发者始终掌握主导权。例如：

1. 保留用户原来的拉取请求标题
2. 把用户的描述放在 AI 生成的拉取请求描述之上
3. 不会批准拉取请求；批准仍由审查者负责
4. 代码建议是可选的，目的在于：
    - 鼓励自我审查与自我反思
    - 标出潜在缺陷或疏漏
    - 提升代码质量并推广最佳实践

关于这一问题的更多讨论见我们的[博客](https://www.qodo.ai/blog/understanding-the-challenges-and-pain-points-of-the-pull-request-cycle/)

</details>

___

<details>
<summary>问：我收到了不正确或不相关的建议。为什么？</summary>

#### 回答：<span style="display:none;">2</span>

- Claude Sonnet、GPT-5 等现代 AI 模型进步很快，但仍然不完美。用户应批判性地评估所有建议，而不是自动接受。
- AI 出错很少见，但有可能。审查代码建议的主要价值，在于它们有较高概率抓住**拉取请求作者造成的错误或缺陷**。我们认为值得花 30–60 秒看一遍建议，即使其中有些并不相关，因为这一做法可以提升代码质量，并避免缺陷进入生产环境。


- 建议的层次结构旨在帮助用户*快速*理解它们，并判断哪些相关、哪些不相关：

    - 只有当 `Category` 标题相关时，用户才应继续看建议的摘要描述。
    - 只有当摘要描述相关时，用户才应点开折叠区域，阅读带代码预览示例的完整建议描述。

- 此外，我们建议使用 [`extra_instructions`](../tools/improve.mdx#extra-instructions-and-best-practices) 字段，引导模型给出更贴合项目具体需求的建议。

</details>

___

<details>
<summary>问：怎样获得更有针对性的建议？</summary>

#### 回答：<span style="display:none;">3</span>

关于如何使用 `extra_instructions` 和 `best_practices` 配置项来引导模型给出更有针对性的建议，请参见[此处](../tools/improve.mdx#extra-instructions-and-best-practices)。

</details>

___

<details>
<summary>问：你们会存储我的代码吗？会用我的代码训练模型吗？</summary>

#### 回答：<span style="display:none;">4</span>

不会。PR-Agent 的严格隐私政策确保你的代码不会被存储，也不会用于训练。

数据隐私政策的详细说明请参见[此链接](../overview/data_privacy.md)

</details>

___

<details>
<summary>问：PR-Agent 能审查草稿 / 离线拉取请求吗？</summary>

#### 回答：<span style="display:none;">6</span>

可以。默认情况下不会自动审查草稿拉取请求，但你可以用 `feedback_on_draft_pr` 参数开启。你也可以通过[在线评论](../usage-guide/automations_and_usage.md#online-usage)手动请求，从而获得任意草稿的反馈。

对于进行中的拉取请求，你可以在[此处](../usage-guide/automations_and_usage.md#pr-agent-automatic-feedback)自定义自动反馈设置，以匹配团队工作流。

</details>

___

<details>
<summary>问：「审查工作量」反馈可以校准或自定义吗？</summary>

#### 回答：<span style="display:none;">7</span>

可以。你可以使用 `extra_instructions` 配置项自定义审查工作量估计（见[文档](../tools/review.md#configuration-options)）。

映射示例：

- 工作量 1：审查时间 < 30 分钟
- 工作量 2：审查时间 30–60 分钟
- 工作量 3：审查时间 60–90 分钟
- ...

注意：工作量等级（1–5）主要用于*比较*，帮助团队优先审查较小的拉取请求。实际审查时长可能不同，重点是提供一致的相对工作量估计。

</details>

___

<details>
<summary>问：如何减少 PR-Agent 产生的噪音？</summary>

#### 回答：<span style="display:none;">3</span>

PR-Agent 的默认配置旨在平衡有用反馈与噪音控制。它通过几种方式降低噪音：

- 自动反馈使用三个高度结构化的工具（`/describe`、`/review` 和 `/improve`），设计成一眼就能看懂，而不会造成大量视觉负担
- 建议以表格呈现，而不是可提交的评论，后者噪音大得多
- 「文件导览」小节默认折叠，因为它往往比较冗长
- 创建新拉取请求时避免中间评论（例如「PR-Agent 正在审查你的拉取请求……」），否则会产生邮件噪音

根据我们的经验，尤其是在大型团队或组织中，关于「噪音」的抱怨有时来自以下问题：

- **多个机器人同时反馈**：多个机器人对同一拉取请求给出反馈时，会造成混乱和噪音。我们建议以 PR-Agent 作为主要反馈工具，以简化流程并减少重复。
- **熟悉这个工具**：与许多只在被要求时才给反馈的工具不同，PR-Agent 会自动分析每一次代码变更并提出改进。这种主动方式一开始可能让人有压力，但它的目的是持续提升代码质量，并在缺陷和问题出现时抓住它们。建议阅读[这份指南](../tools/improve.mdx#understanding-ai-code-suggestions)，以对齐预期并充分发挥 PR-Agent 自动反馈的价值。

因此，在全局配置层面，我们建议使用默认配置，它旨在降低噪音的同时提供有价值的反馈。

不过，如果你仍然觉得反馈太吵，可以调整配置。每个用户和团队的需求不同，针对特定仓库按需调整不仅完全可行，甚至值得推荐。
降低噪音的配置调整方式包括例如：

- [代码建议的分数阈值](../tools/improve.mdx#configuration-options)
- [利用 `extra_instructions` 字段获得更有针对性的反馈](../tools/improve.mdx#extra-instructions)
- [控制哪些工具自动运行](../usage-guide/automations_and_usage.md#github-app-automatic-tools-when-a-new-pr-is-opened)

请注意，有些用户可能希望相反的效果——更彻底、更详细的反馈。PR-Agent 设计为灵活且可定制，让你按团队的具体需求和偏好调整反馈。
增加反馈的方式示例包括：

- [双发布模式](../tools/improve.mdx#dual-publishing-mode)

</details>

___
