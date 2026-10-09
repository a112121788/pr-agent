---
title: "工具"
sidebar_position: 1
---

每个 PR-Agent 工具都有独立页面，说明其行为与用法：

| 工具 | 说明 |
|------|-------------|
| **[PR 描述（`/describe`）](./describe.md)** | 生成拉取请求标题、类型、摘要、代码导览和标签。 |
| **[PR 审查（`/review`）](./review.md)** | 生成拉取请求审查，反馈可能的问题、安全顾虑、测试和审查工作量。 |
| **[代码建议（`/improve`）](./improve.mdx)** | 生成可执行的代码建议，用于改进拉取请求。 |
| **[问答（`/ask ...`）](./ask.md)** | 回答关于拉取请求或特定代码行的自由文本问题。 |
| **[添加文档（`/add_docs`）](./add_docs.md)** | 为缺少文档的代码组件生成文档。 |
| **[生成标签（`/generate_labels`）](./generate_labels.md)** | 根据代码变更生成自定义标签。 |
| **[相似议题（`/similar_issue`）](./similar_issues.md)** | 根据当前议题在仓库中查找相似议题。 |
| **[帮助（`/help`）](./help.md)** | 列出所有可用工具。 |
| **[文档帮助（`/help_docs`）](./help_docs.md)** | 基于 git 文档目录回答自由文本问题。 |
| **[更新变更日志（`/update_changelog`）](./update_changelog.md)** | 根据拉取请求变更自动更新 CHANGELOG.md。 |

## 使用示例

每个工具都可以通过两种方式触发：

- **作为评论** — 把命令（例如 `/review`）写成评论，PR-Agent 会回复。大多数工具评论在拉取请求上；`similar_issue` 这类以议题为范围的工具则评论在议题上。
- **通过 [CLI](../usage-guide/automations_and_usage.md#local-repo-cli)** — 运行 `python -m pr_agent.cli --pr_url=<PR_URL> <tool>`。以议题为范围的工具改用 `--issue_url=<ISSUE_URL>`，而不是 `--pr_url`。模块形式只在可以导入 `pr_agent` 包的环境中可用（例如 `uv sync` 创建的虚拟环境）。如果 `pr-agent` 已在 `PATH` 中，可以直接运行。

两种方式接受相同的工具参数和[配置覆盖](../usage-guide/configuration_options.md)。

| 工具                                     | 评论                          | CLI                                                             |
|------------------------------------------|----------------------------------|----------------------------------------------------------------|
| [描述](./describe.md)                | `/describe`                      | `python -m pr_agent.cli --pr_url=<PR_URL> describe`             |
| [审查](./review.md)                    | `/review`                        | `python -m pr_agent.cli --pr_url=<PR_URL> review`              |
| [改进](./improve.mdx)                  | `/improve`                       | `python -m pr_agent.cli --pr_url=<PR_URL> improve`             |
| [提问](./ask.md)                          | `/ask "How does X work?"`        | `python -m pr_agent.cli --pr_url=<PR_URL> ask "How does X work?"` |
| [添加文档](./add_docs.md)                | `/add_docs`                      | `python -m pr_agent.cli --pr_url=<PR_URL> add_docs`           |
| [生成标签](./generate_labels.md)  | `/generate_labels`               | `python -m pr_agent.cli --pr_url=<PR_URL> generate_labels`     |
| [相似议题](./similar_issues.md)    | `/similar_issue`                 | `python -m pr_agent.cli --issue_url=<ISSUE_URL> similar_issue` |
| [帮助](./help.md)                        | `/help`                          | `python -m pr_agent.cli --pr_url=<PR_URL> help`                |
| [更新变更日志](./update_changelog.md)| `/update_changelog`              | `python -m pr_agent.cli --pr_url=<PR_URL> update_changelog`    |

`/help_docs` 暂时禁用（见 [#2445](https://github.com/The-PR-Agent/pr-agent/issues/2445)），因此未列入上表。

截图、参数以及典型用例的演练，见上方各工具页面的**使用示例**一节。
