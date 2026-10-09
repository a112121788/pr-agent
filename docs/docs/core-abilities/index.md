---
title: "Core Abilities"
sidebar_position: 1
---

Gitee PR-Agent reviews pull requests on Gitee. The abilities below decide what goes into the prompt, how a large diff is split, and what gets published back on the pull request:

- [Agent skills](./agent_skills.md)
- [Compression strategy](./compression_strategy.md)
- [Dynamic context](./dynamic_context.md)
- [Fetching ticket context](./fetching_ticket_context.md)
- [Local and global metadata](./metadata.md)
- [Self-reflection](./self_reflection.md)

## Defaults in this build

- Platform: Gitee only. Setup is in the [Gitee installation guide](../installation/gitee.md). Other git hosts are listed on [Supported platforms](../overview/supported_platforms.md).
- Model: `gpt-6.1-sol`. The fallback is `glm-5.3`. Override either in [Changing a model](../usage-guide/changing_a_model.md).
- Response language: `zh-CN` (`config.response_language`).
- Large pull requests: `/review` and `/describe` segment the diff by default. See [Compression strategy](./compression_strategy.md).
- Inline comments are anchored with Gitee's diff `position`, counted from the line below the first `@@` hunk header. A line that cannot be mapped is skipped. See [Gitee installation](../installation/gitee.md#verified-behavior).
