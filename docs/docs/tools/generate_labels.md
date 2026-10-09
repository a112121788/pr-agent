---
title: "Generate Labels"
sidebar_position: 7
---

## Overview

`/generate_labels` reads the pull-request diff and applies labels that match the change. It does not rewrite the description. Use [`/describe`](./describe.md) when you want the summary as well.

Comment on the pull request:

```
/generate_labels
```

Or pass `generate_labels` to the [Gitee CLI image](./index.md#run). The URL must be `https://gitee.com/owner/repo/pulls/N` or `https://e.gitee.com/<enterprise>/repos/owner/repo/pulls/N`.

## What is published

Labels are written through the Gitee API. The token needs permission to edit pull-request labels. Publishing replaces the label set, so labels a person added are read first and kept. If that read fails, nothing is published, because a blind write would remove them.

A temporary comment says `正在准备 PR 标签...` while the command runs, then it is removed.

The allowed names are the built-in types `Bug fix`, `Tests`, `Enhancement`, `Documentation`, and `Other`, plus any custom names you configure. Matching ignores case. Unknown names are dropped. If the model returns only unknown names, the current labels stay as they are.

## Custom labels

```toml
[config]
enable_custom_labels = true

[custom_labels."Bug fix"]
description = "A fix for a bug in the codebase"

[custom_labels."sql_changes"]
description = "Use when a PR contains changes to SQL queries"
```

Write each description as a condition, so the model knows when the label applies. A custom label that no longer matches is removed on the next `/generate_labels` or `/describe` run. Human-added labels outside this set are not removed by that filter.

`/describe` uses the same label set, but `pr_description.publish_labels` defaults to `false`. `/generate_labels` is the command that publishes labels on its own.
