---
title: "纯 diff 本地模式"
sidebar_position: 12
---

在没有平台 API 令牌、也没有 PR URL 的情况下，针对原始 unified diff 运行 PR-Agent。
结果打印到 stdout（也可以同时保存到文件）。这适用于避免使用 HTTP 访问令牌的安全优先
或气隙环境，也适用于在 diff 产物而非实时拉取请求上运行的推送前
钩子或 CI 流水线。

## 用法 {#usage}

直接从 stdin 管道传入 diff：

```bash
git diff main...feature-branch | python -m pr_agent.cli --stdin review
```

也可以传入 diff 文件，并在 stdout 之外保存输出：

```bash
git diff main...feature-branch > changes.diff
python -m pr_agent.cli --diff-file changes.diff --output review.md review
```

### 标志 {#flags}

| 标志 | 说明 |
|---|---|
| `--stdin` | 从 stdin 读取 unified diff |
| `--diff-file <path>` | 从文件读取 unified diff |
| `--output <path>` | 把兼容的纯 diff 命令生成的 Markdown 额外写入文件，同时仍输出到 stdout |
| `--json-output <path>` | 把解析后的审查和令牌用量写入 JSON 文件（仅 `review` 或 `review_pr`） |

`--stdin` 与 `--diff-file` 互斥。进入纯 diff 模式至少要提供其中一个；两者都省略时，
会回退到正常的 `--pr_url` 流程。
输出选项必须出现在命令之前。例如应使用
`--stdin --output result.md review`，而不是 `--stdin review --output result.md`。

### 支持的命令 {#supported-commands}

支持 `review`、`improve`、`describe` 和 `ask`，以及它们的
`review_pr`、`improve_code`、`describe_pr` 和 `ask_question` 别名。因为没有可推送的托管
平台，`improve` 会把代码建议渲染成一份 markdown
文档输出到 stdout（若给出 `--output`，也写入该文件），而不是可提交的行内
建议。需要与实时平台交互的命令（例如
`update_changelog` 或 `similar_issue`）在此模式下没有意义。

会发布 Markdown、且不需要额外平台
状态的现有命令变体（`auto_review`、`config`、`settings` 和 `help`）同样遵循 `--output`。
`answer` 不会：它需要议题评论历史，而输入只是一份独立 diff 时
无法提供这些历史。

## 工作原理 {#how-it-works}

1. **Diff 解析**——在本地把 unified diff 解析为按文件划分的补丁对象。
   二进制文件会自动跳过。

2. **工作树补全**——当 PR-Agent 在仓库工作树内运行时，
   它从磁盘读取每个变更文件，并反向应用 diff，以重建
   基线（变更前）文件内容。同时拥有基线和 head 版本，能给
   LLM 完整的文件上下文，从而得到更高质量的分析。

3. **仅补丁回退**——如果磁盘上找不到某个变更文件（例如 diff 是在
   别处生成的，或文件已被删除），PR-Agent 会对该文件回退到仅补丁模式。
   审查仍会运行，只是上下文更少。

4. **输出**——结果写入 stdout。如果给出了 `--output <path>`，也会
   写入该文件（UTF-8，每次运行覆盖）。对于 `review` 或
   `review_pr`，如果给出了 `--json-output <path>`，解析后的审查加上一个
   含本次运行累计令牌数的 `usage` 对象，也会以 JSON 写入该
   文件。

diff 处理步骤本身不需要平台令牌、PR URL 或互联网访问。
除非配置了本地模型，否则仍然需要 LLM API 密钥。

## 与 `local` Git 提供商的区别 {#difference-from-the-local-git-provider}

现有的 `git_provider = "local"` 模式（通过 `--pr_url` 调用）通过比较本地 Git 仓库中的分支来计算 diff，并且要求工作树干净。
纯 diff 模式在以下方面不同：

| | `local` 提供商 | `plain-diff` 提供商（本页） |
|---|---|---|
| 输入 | 本地仓库中的分支名 | 通过 stdin 或文件提供的 unified diff |
| 是否需要工作树 | 是（干净） | 否 |
| 是否需要平台令牌 | 否 | 否 |
| 输出 | 在本地发布的 GitHub 风格评论 | stdout（+ 可选文件） |
| 行内评论 | 不支持 | 不支持 |

当你已经有 diff 产物（例如来自 CI 步骤或 `git format-patch`），并且希望零配置、无需令牌地进行审查时，使用 `plain-diff` 提供商。
