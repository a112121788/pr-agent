---
title: "代理技能"
sidebar_position: 2
---

`支持的工具：Review、Improve、Describe、Ask`

## 概述

代理技能用 [agent-skills（`SKILL.md`）格式](https://github.com/The-PR-Agent/pr-agent/issues/2384) 把可复用的审查指引发给 Gitee PR-Agent。一个技能是一个目录，里面有一份 `SKILL.md`：YAML front matter（`name` 和 `description`）后面是 Markdown 正文。

```markdown
---
name: terraform-standards
description: Use when reviewing Terraform code — checks state safety and risky deletions.
---

# Terraform Review Guidance

- Flag any resource deletion that is not explicitly called out in the PR description.
- Require `prevent_destroy` on stateful resources.
- ...
```

启用后，Gitee PR-Agent 会发现配置路径下的每一份 `SKILL.md`，解析后把技能的 `name`、`description` 和正文注入 `/review`、`/improve`、`/describe` 以及顶层 `/ask` 的提示词，与 `extra_instructions` 并列。模型自行判断哪些指引与当前拉取请求或问题有关。`description` 是「这条技能何时适用」的信号。除非改了 `config.response_language`，发出的评论保持 `zh-CN`。

有用的用法是主机级技能库：在 Gitee PR-Agent 的部署上安装一套整理好的技能，多个 Gitee 仓库共用，不必把指引提交进每个仓库。

## 配置

技能**默认关闭**。在主机的 `configuration.toml`（或其他主机级配置）里设置：

```toml
[skills]
enabled = false
paths = []                # 递归扫描 "*/SKILL.md" 的目录；支持 ~ 和 $VAR
max_skills_tokens = 8000  # 注入技能块的令牌预算
```

- `enabled`：打开该功能。
- `paths`：递归扫描 `*/SKILL.md` 的目录，或直接指向某个 `SKILL.md` 文件。会展开 `~` 和 `$VAR` / `${VAR}`。
- `max_skills_tokens`：限制注入技能块的总大小。超出预算的技能从末尾丢弃，并打出警告。若第一条技能单独超预算，则截断并标成 `[truncated]`。

:::warning[`skills.paths` 只能在主机上设置]
`skills.paths` **不能**由仓库的 `.pr_agent.toml` 设置，只能在部署的管理侧配置。它读取的是 Gitee PR-Agent 主机上的文件。若仓库能改这个路径，就可以把进程指到敏感文件，并把内容送进模型。仓库提供的 `skills.paths` 会被忽略，并记一条警告。

仓库*可以*在自己的 `.pr_agent.toml` 里设置 `skills.enabled` 和 `skills.max_skills_tokens`，例如加入主机技能库，或限制块的大小。它不能改扫描路径。
:::

## 附带资源

agent-skills 布局允许在 `SKILL.md` 旁边放其他文件。Gitee PR-Agent 只内联其中的**文本**：

- 技能目录树里的每个 `*.md`（含 `references/` 子目录）都接在 `SKILL.md` 正文后面。大于 256 KB 的资源文件会跳过，并打出警告。
- `scripts/` 和 `assets/` **会跳过**。每条命令都是一次模型调用，没有工具循环，因此不能执行脚本，也不能按需加载二进制资源。
- 嵌套目录若自带 `SKILL.md`，则视为另一个技能，不会并进父技能。

Gitee PR-Agent 只支持**纯文本**代理技能。`/ask_line` 不在注入范围内。它的提示词按选中的一个差异块，以及可选的讨论串历史单独预算。

## 限制

命令是单次模型调用。agent-skills 的*渐进披露*（先按 `description` 选中技能再读 `SKILL.md`，需要时才读 `references/*.md`）在当前架构上不可用。在此之前，每条已启用技能的文本都会进提示词，并由 `max_skills_tokens` 封顶。依赖脚本执行或二进制资源的技能不会运行。
