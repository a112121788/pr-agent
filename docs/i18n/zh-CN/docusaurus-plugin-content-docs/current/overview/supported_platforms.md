---
title: "支持的平台"
sidebar_position: 3
---

各 Git 平台支持哪些工具、触发方式与核心能力。

|       |    | <span class="pra-provider"><span class="pra-logo pra-logo--github" aria-hidden="true"></span>GitHub</span> | <span class="pra-provider"><span class="pra-logo pra-logo--gitlab" aria-hidden="true"></span>GitLab</span> | <span class="pra-provider"><span class="pra-logo pra-logo--bitbucket" aria-hidden="true"></span>Bitbucket</span> | <span class="pra-provider"><span class="pra-logo pra-logo--azuredevops" aria-hidden="true"></span>Azure DevOps</span> | <span class="pra-provider"><span class="pra-logo pra-logo--gitea" aria-hidden="true"></span>Gitea</span> | Gitee |
| ----- |---------------------------------------------------------------------------------------|:------:|:------:|:---------:|:------------:|:-----:|:-----:|
| [工具](../tools/index.md) | [描述](../tools/describe.md)                                     |   ✅   |   ✅   |    ✅     |      ✅       |  ✅   |  ✅   |
|       | [审查](../tools/review.md)                                                           |   ✅   |   ✅   |    ✅     |      ✅       |  ✅   |  ✅   |
|       | [改进](../tools/improve.mdx)                                                         |   ✅   |   ✅   |    ✅     |      ✅       |  ✅   |  ✅   |
|       | [提问](../tools/ask.md)                                                                 |   ✅   |   ✅   |    ✅     |      ✅       |  ✅   |  ✅   |
|       | [针对代码行提问](../tools/ask.md#ask-lines)                                         |   ✅   |   ✅   |           |      ✅       |       |       |
|       | [添加文档](../tools/add_docs.md)                                                       |   ✅   |   ✅   |    ✅     |      ✅       |  ✅   |       |
|       | [生成标签](../tools/generate_labels.md)                                         |   ✅   |   ✅   |   💬    |      ✅       |       |  ✅   |
|       | [相似议题](../tools/similar_issues.md)                                           |   ✅   |        |           |              |       |       |
|       | [帮助](../tools/help.md)                                                               |   ✅   |   ✅   |    ✅     |      ✅       |  ✅   |       |
|       | [帮助文档](../tools/help_docs.md) ⚠️                                                   |        |        |           |              |       |       |
|       | [更新 CHANGELOG](../tools/update_changelog.md)                                       |   ✅   |   ✅   |    ✅     |      💬       |  💬  |  💬  |
|       |                                                                                       |        |        |           |              |       |       |
| [用法](../usage-guide/index.md) | [CLI](../usage-guide/automations_and_usage.md#local-repo-cli)      |   ✅   |   ✅   |    ✅     |      ✅       |  ✅   |  ✅   |
|       | [应用 / webhook](../usage-guide/automations_and_usage.md#github-app)                    |   ✅   |   ✅   |    ✅     |      ✅       |  ✅   |  ✅   |
|       | [提及机器人](https://github.com/the-pr-agent/pr-agent#try-it-now)                       |   ✅   |        |           |              |       |       |
|       | [Actions](../installation/github.md#run-as-a-github-action) <br /> [GitLab 流水线](../installation/gitlab.md#run-as-a-gitlab-pipeline) <br /> [Bitbucket 流水线](../installation/bitbucket.md#run-as-a-bitbucket-pipeline) <br /> [Azure DevOps 流水线](../installation/azure.md#azure-devops-pipeline) |   ✅   |   ✅   |    ✅     |      ✅       |       |       |
|       |                                                                                       |        |        |           |              |       |       |
| [核心能力](../core-abilities/index.md) | [自适应且感知 token 的文件补丁适配](../core-abilities/compression_strategy.md) |   ✅   |   ✅   |    ✅     |      ✅       |  ✅   |  ✅   |
|       | [代理技能（`SKILL.md`）](../core-abilities/agent_skills.md)                         |   ✅   |   ✅   |    ✅     |      ✅       |  ✅   |       |
|       | [仓库上下文文件（`AGENTS.md`）](../usage-guide/additional_configurations.md#bringing-per-repo-context-files-to-pr-agent) |   ✅   |   ✅   |    ✅     |      ✅       |  ✅   |  ✅   |
|       | [压缩策略](../core-abilities/compression_strategy.md)                      |   ✅   |   ✅   |    ✅     |      ✅       |  ✅   |  ✅   |
|       | [动态上下文](../core-abilities/dynamic_context.md)                                |   ✅   |   ✅   |    ✅     |      ✅       |  ✅   |       |
|       | [获取工单上下文](../core-abilities/fetching_ticket_context.md)                |   ✅   |  ✅   |    ✅     |      ✅       |  ✅   |       |
|       | [本地与全局元数据](../core-abilities/metadata.md)                             |   ✅   |   ✅   |    ✅     |      ✅       |  ✅   |  ✅   |
|       | [多模型支持](../usage-guide/changing_a_model.md)                          |   ✅   |   ✅   |    ✅     |      ✅       |  ✅   |  ✅   |
|       | [自我反思](../core-abilities/self_reflection.md)                                |   ✅   |   ✅   |    ✅     |      ✅       |  ✅   |  ✅   |

⚠️ 自 v0.36.1 起，`/help_docs` 因凭证泄露问题待修复而暂时禁用（[#2445](https://github.com/The-PR-Agent/pr-agent/issues/2445)）；参见[帮助文档](../tools/help_docs.md)。

图例：✅ = 已支持。💬 = 工具会运行，但其输出以拉取请求评论发布，而不是直接生效（在提供商无法推送文件时的「更新 CHANGELOG」，以及无法设置标签时的「生成标签」）。空白 = 不支持，或尚未验证（Gitea 上的「生成标签」）。Gitee 的安装说明见[Gitee 集成](../installation/gitee.md)；其空白单元格尚未验证，而其 webhook 会路由已打开的拉取请求和斜杠命令评论。

## Gerrit 与 CodeCommit

Gerrit 和 CodeCommit 是已注册的提供商，但为了表格可读而未放入主表。支持情况如下：

|       |    | <span class="pra-provider"><span class="pra-logo pra-logo--gerrit" aria-hidden="true"></span>Gerrit</span> | <span class="pra-provider"><span class="pra-logo pra-logo--codecommit" aria-hidden="true"></span>CodeCommit</span> |
| ----- |---------------------------------------------------------------------------------------|:------:|:----------:|
| [工具](../tools/index.md) | [描述](../tools/describe.md)、[审查](../tools/review.md)、[改进](../tools/improve.mdx)、[提问](../tools/ask.md)、[添加文档](../tools/add_docs.md)、[帮助](../tools/help.md) |   ✅   |     ✅     |
|       | [针对代码行提问](../tools/ask.md#ask-lines)                                         |        |            |
|       | [生成标签](../tools/generate_labels.md)                                         |   💬   |     💬     |
|       | [更新 CHANGELOG](../tools/update_changelog.md)                                       |   💬   |     💬     |
|       | [相似议题](../tools/similar_issues.md)                                           |        |            |
| [用法](../usage-guide/index.md) | [CLI](../usage-guide/automations_and_usage.md#local-repo-cli)                  |   ✅   |     ✅     |
|       | [应用 / webhook](../usage-guide/automations_and_usage.md#github-app)                    |   ✅   |            |
|       | 提及机器人 / Actions 与流水线                                                   |        |            |
| [核心能力](../core-abilities/index.md) | [代理技能（`SKILL.md`）](../core-abilities/agent_skills.md)及其他核心能力 |   ✅   |     ✅     |
|       | [仓库上下文文件（`AGENTS.md`）](../usage-guide/additional_configurations.md#bringing-per-repo-context-files-to-pr-agent) |        |            |

Gerrit 和 CodeCommit 不支持 `gfm_markdown`，因此 `/describe` 会省略语义文件类型以及其他若干小节。CodeCommit 的安装说明目前位于 [GitHub 安装页面](../installation/github.md)；Gerrit 尚无专门的安装页面。

对于 Gerrit，变更文件列表和被审查的 diff 都会遵循 `ignore.glob` 与 `ignore.regex`。重命名的文件使用目标路径，删除的文件则保留原始路径。内容非 UTF-8 的文件仍会参与基于文件名的语言检测，但会从交给模型的 diff 中省略。
