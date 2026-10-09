---
title: "Agent Skills"
sidebar_position: 2
---

`Supported tools: Review, Improve, Describe, Ask`

## Overview

Agent skills distribute reusable review guidance to Gitee PR-Agent in the [agent-skills (`SKILL.md`) format](https://github.com/The-PR-Agent/pr-agent/issues/2384). A skill is a directory that contains a `SKILL.md` file: YAML front matter (`name` and `description`) followed by a markdown body.

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

When skills are enabled, Gitee PR-Agent discovers every `SKILL.md` under the configured paths, parses it, and injects the skill's `name`, `description`, and body into the `/review`, `/improve`, `/describe`, and top-level `/ask` prompts next to `extra_instructions`. The model applies the guidance it judges relevant. Each skill's `description` is the signal for when that skill applies. Published comments stay in `zh-CN` unless `config.response_language` is changed.

The useful pattern is a host-level library: install one curated set of skills on the Gitee PR-Agent deployment and reuse it across Gitee repositories, without checking the guidance into each repository.

## Configuration

Skills are **disabled by default**. Set them in the host `configuration.toml` (or another host-level config source):

```toml
[skills]
enabled = false
paths = []                # directories scanned recursively for "*/SKILL.md"; supports ~ and $VAR
max_skills_tokens = 8000  # token budget for the combined skills block
```

- `enabled` — turn the feature on.
- `paths` — directories scanned recursively for `*/SKILL.md`, or direct paths to a `SKILL.md` file. `~` and `$VAR` / `${VAR}` are expanded.
- `max_skills_tokens` — caps the combined size of the injected skills block. Skills past the cap are dropped from the end, with a warning. If the first skill alone exceeds the budget, it is clipped and marked `[truncated]`.

:::warning[`skills.paths` is host-level only]
`skills.paths` **cannot be set from a repository's `.pr_agent.toml`**. It is configurable only where the deployment is administered. The setting reads files from the Gitee PR-Agent host. A repository that could set it could point the process at sensitive host files and send their contents to the model. A repo-supplied `skills.paths` is ignored, with a warning.

A repository *may* set `skills.enabled` and `skills.max_skills_tokens` in its own `.pr_agent.toml`, for example to opt in to the host library or to size the block. It cannot redirect the filesystem scan.
:::

## Bundled resources

The agent-skills layout allows extra files next to `SKILL.md`. Gitee PR-Agent inlines the **text** ones:

- Every `*.md` file in the skill directory tree, including a `references/` subdirectory, is appended after the `SKILL.md` body. A resource file larger than 256 KB is skipped, with a warning.
- `scripts/` and `assets/` are **skipped**. Each command is a single model call with no tool-use loop, so the process cannot run scripts or load binary assets on demand.
- A nested directory that contains its own `SKILL.md` is a separate skill. It is not inlined into its parent.

Gitee PR-Agent supports **text-only** agent skills. `/ask_line` is outside this injection. Its prompt is budgeted around one selected diff hunk and optional thread history.

## Limitations

Commands are single-shot model calls. The agent-skills *progressive disclosure* model — read `SKILL.md` only after selecting it by `description`, then read `references/*.md` only on demand — is not available on this architecture. Until that changes, every enabled skill's text is loaded into the prompt, bounded by `max_skills_tokens`. Skills that depend on script execution or binary assets do not run.
