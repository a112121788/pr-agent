---
title: "Compression Strategy"
sidebar_position: 3
---

`Supported Git platform: Gitee`

## Overview

Gitee PR-Agent prepares a Gitee pull-request diff in two passes. First it packs the diff into the model's token budget. When the diff still does not fit, `/review` and `/describe` segment it by default instead of dropping the rest silently.

1. The pull request is small enough for one prompt (system prompt plus user prompt).
2. The pull request is too large for one prompt.

Both cases start with the same file ordering.

#### Repository language priority

1. Drop binary files and non-code files (images, PDFs, and similar).
2. Take the main languages used in the repository.
3. Sort the pull-request files by those languages, most common first:

   * `[[file.py, file2.py], [file3.js, file4.jsx], [readme.md]]`

### Small pull request

The whole diff fits in one prompt:

1. Drop binary files and non-code files.
2. Expand the context around each hunk. The dynamic-context settings in [Dynamic context](./dynamic_context.md) control how many extra lines are added.

### Large pull request

#### Why pack the diff

A Gitee pull request can be long, and not every hunk matters equally. The packer keeps as much relevant code as the token budget allows before any extra model call.

#### What is compressed

Additions are kept ahead of deletions:

* Deleted files are folded into one `deleted files` list.
* Hunks that only delete lines are removed from the file patch.

#### Token-aware fitting

Patches are tokenized with [tiktoken](https://github.com/openai/tiktoken) after the steps above, then fitted as follows:

1. Inside each language group, sort files by token count, largest first:
    * `[[file2.py, file.py], [file4.jsx, file3.js], [readme.md]]`
2. Walk the patches in that order.
3. Add patches until the prompt is within a buffer of the model's token limit.
4. If patches remain, add them as `other modified files` until the hard token limit, then stop.
5. If there is still room, add `deleted files` until the hard token limit, then stop.

#### Segmented review and description

Packing is not the last step. In this build both tools continue when files are left out:

| Tool | Default | What happens |
| --- | --- | --- |
| `/review` | `pr_reviewer.enable_large_pr_chunking = true` | The diff is split into at most `pr_reviewer.max_number_of_calls` chunks (default `3`). Each chunk is reviewed, then the answers are merged into one comment. |
| `/describe` | `pr_description.enable_large_pr_handling = true` | The tool makes further model calls and combines them so more files are covered. |

Files that still do not fit are listed in the review coverage footer. A failed chunk is retried on the fallback model (`glm-5.3` when the primary model is `gpt-6.1-sol`) before the successful chunks are published as a partial review. The chunk switch is under [Other options](../tools/review.md#other-options). The describe switch is `enable_large_pr_handling` on the [Describe configuration](../tools/describe.md#configuration).

Inline comments published from a chunk still use Gitee's diff `position`. See [Gitee installation](../installation/gitee.md#verified-behavior).

#### Example

<img src="/img/git_patch_logic.png" alt="How a Gitee pull-request patch is packed" width="768" />
