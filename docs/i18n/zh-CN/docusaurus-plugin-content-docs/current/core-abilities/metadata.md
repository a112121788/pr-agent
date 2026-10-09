---
title: "通过多阶段分析注入本地与全局元数据"
sidebar_position: 6
---

`支持的 Git 平台：Gitee`

Gitee PR-Agent 分层组装提示词：拉取请求本身、`/describe` 的摘要、文件周围的上下文，以及主机或仓库指令。后面的命令复用这些层，而不是再叫一次模型才把它们找回来。评论使用 `zh-CN`。

1. 对每个 Gitee 拉取请求，它会读取：

- 标题和分支名
- 已有描述
- 提交说明
- diff，以 [hunk](https://loicpefferkorn.net/2014/02/diff-files-what-are-hunks-and-how-to-extract-them/) 形式
- 本次拉取请求改过的文件的全文
- 所引用 Gitee 议题的标题和正文（议题 API 有返回时）。见 [获取工单上下文](./fetching_ticket_context.md)。

:::tip[仓库指令]
[`extra_instructions`](../tools/improve.mdx#额外说明和仓库文件) 这类仓库偏好会加在上述输入之上。它们用来引导建议，不会改 Gitee 令牌、模型端点或 `skills.paths`。
:::

2. 拉取请求打开后，第一条自动命令是 [`/describe`](../tools/describe.md)。它产出：

- 拉取请求类型（缺陷修复、功能、重构等）
- 简短的要点摘要
- 变更导览：每个修改过的文件一行，再加几条这次改了什么

这些输出成为后续 `/review` 和 `/improve` 的拉取请求元数据。模型可以直接用导览，不必再来回一次。

`/improve` 对某个文件给建议时，提示词可以把该文件的导览和差异块放在一起：

```diff
## File: 'src/file1.py'
### AI-generated file summary:
- edited function `func1` that does X
- Removed function `func2` that was not used
- ....

@@ ... @@ def func1():
__new hunk__
11  unchanged code line0
12  unchanged code line1
13 +new code line2 added
14  unchanged code line3
__old hunk__
 unchanged code line0
 unchanged code line1
-old code line2 removed
 unchanged code line3

@@ ... @@ def func2():
__new hunk__
...
__old hunk__
...
```

3. 文件全文用来扩展差异块上下文。见 [动态上下文](./dynamic_context.md)。

4. 这几层从差异块到文件，再到拉取请求，再到仓库指令。一次调用放不下的 `/review` 会把这些元数据分到各段里，再合并成一条评论。见 [压缩策略](./compression_strategy.md)。
