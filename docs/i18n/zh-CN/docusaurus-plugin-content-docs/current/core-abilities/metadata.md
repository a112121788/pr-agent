---
title: "通过多阶段分析注入本地与全局元数据"
sidebar_position: 6
---

`支持的 Git 平台：GitHub、GitLab、Bitbucket、Azure DevOps、Gitea`

1\.
PR-Agent 最初会为每个拉取请求检索以下数据：

- 拉取请求标题和分支名
- 拉取请求原始描述
- 提交消息历史
- 拉取请求 diff 补丁，采用 [hunk diff](https://loicpefferkorn.net/2014/02/diff-files-what-are-hunks-and-how-to-extract-them/) 格式
- 拉取请求中被修改文件的完整内容

:::tip[提示：组织级元数据]
除上述输入外，PR-Agent 还可以纳入用户提供的补充偏好，例如 [`extra_instructions` 和组织最佳实践](../tools/improve.mdx#extra-instructions-and-best-practices)。这些信息可用于增强拉取请求分析。
:::

2\.
默认情况下，PR-Agent 执行的第一条命令是 [`describe`](../tools/describe.md)，它生成三类输出：

- 拉取请求类型（例如缺陷修复、功能、重构等）
- 拉取请求描述——拉取请求的项目符号摘要
- 变更导览——对每个被修改文件，提供一行摘要，随后是变更的详细项目符号列表。

这些 AI 生成的输出现在被视为拉取请求元数据的一部分，并可在后续的 `review` 和 `improve` 等命令中使用。
这实际上实现了多阶段思维链分析，而无需任何额外的 API 调用，那些调用会花费时间和金钱。

例如，在为不同文件生成代码建议时，PR-Agent 可以把 AI 生成的 [“Changes walkthrough”](https://github.com/the-pr-agent/pr-agent/pull/1202#issue-2511546839) 文件摘要注入提示词：

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

3\. 检索到的完整拉取请求文件也会用来扩展和增强拉取请求上下文（见[动态上下文](./dynamic_context.md)）。

4\. 上面描述的所有元数据代表若干层累积分析——从差异块级，到文件级，到拉取请求级，再到组织级。
这种全面的方法使 PR-Agent 的 AI 模型能够生成更精确、更符合上下文的建议和反馈。
