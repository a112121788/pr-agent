---
title: "代理技能"
sidebar_position: 2
---

`支持的工具：Review、Improve、Describe、Ask`

## 概述

代理技能让你可以使用 [agent-skills（`SKILL.md`）格式](https://github.com/The-PR-Agent/pr-agent/issues/2384)，向 PR-Agent 分发经过整理、可复用的审查指引。技能是一个目录，其中包含 `SKILL.md` 文件：YAML frontmatter（`name` + `description`）之后是 markdown 正文：

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

启用后，PR-Agent 会发现已配置路径下的每个 `SKILL.md`，解析它，并把技能的 `name`、`description` 和正文注入 `/review`、`/improve`、`/describe` 以及顶层 `/ask` 提示词，与 `extra_instructions` 并列。模型会应用它判断与该拉取请求或问题相关的指引，并以每个技能的 `description` 作为该技能何时适用的信号。

其价值在于**组织范围、主机级的技能库**：在 PR-Agent 部署上安装一套经过整理的技能，并在许多仓库中复用，而无需把指引提交到每个仓库。

## 配置

技能**默认禁用**，并在 `configuration.toml`（或任何主机级配置源）中配置：

```toml
[skills]
enabled = false
paths = []                # directories scanned recursively for "*/SKILL.md"; supports ~ and $VAR
max_skills_tokens = 8000  # token budget for the combined skills block
```

- `enabled` — 打开该功能。
- `paths` — 目录列表（递归扫描 `*/SKILL.md`）或直接指向 `SKILL.md` 文件的路径。会展开 `~` 和 `$VAR`/`${VAR}`。
- `max_skills_tokens` — 限制注入的技能块的合计大小。超出上限的技能会从末尾丢弃并记录警告；如果第一个技能单独就超出预算，它会被截断并标记为 `[truncated]`。

:::warning[`skills.paths` 仅限主机级]
`skills.paths` **不能从仓库的 `.pr_agent.toml` 设置**，只能在部署被管理的地方配置。因为它读取 PR-Agent 主机文件系统上的文件，如果允许仓库设置它，恶意仓库就可以让 PR-Agent 指向敏感的主机文件（例如 `~/.ssh/*`），并把其内容外泄到模型提示词中。仓库提供的 `skills.paths` 会被忽略并记录警告。

仓库*可以*在自己的 `.pr_agent.toml` 中设置安全的按仓库偏好 `skills.enabled` 和 `skills.max_skills_tokens`——例如选择加入（或调整大小）主机上由管理员整理的技能库。它绝不能重定向文件系统扫描。
:::

## 捆绑资源

agent-skills 标准支持与 `SKILL.md` 一起捆绑文件。PR-Agent 会内联其中的**文本**文件：

- 技能目录树中的所有 `*.md` 文件（包括 `references/` 子目录）会追加在 `SKILL.md` 正文之后。大于 256&nbsp;KB 的单个资源文件会被跳过并记录警告。
- `scripts/` 和 `assets/` 子目录会被**跳过**：PR-Agent 运行的是没有工具使用循环的单次模型调用，因此无法按需执行脚本或加载二进制资源。
- 包含自己的 `SKILL.md` 的嵌套目录会被视为独立技能，不会内联到其父技能中。

简而言之，PR-Agent 支持**纯文本**代理技能。`/ask_line` 仍在技能注入范围之外，因为它的提示词是围绕所选 diff 差异块和可选讨论历史单独编制预算的。

## 限制

PR-Agent 分发的是单次模型调用，因此 agent-skills 标准的*渐进式披露*模型（模型只在根据 `description` 选中之后才读取 `SKILL.md`，并且只在需要时读取 `references/*.md`）在当前架构上无法实现——支持这一点的架构变更计划在未来进行。在此之前，每个已启用技能的文本都会加载到每个拉取请求的提示词中，并由 `max_skills_tokens` 限制。依赖脚本执行或二进制资源的技能
