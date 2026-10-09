---
title: "Self-Reflection"
sidebar_position: 7
---

`Supported Git platform: Gitee`

Gitee PR-Agent runs a **self-reflection** pass on `/improve`. The model scores and re-ranks its own suggestions and drops the ones it marks as irrelevant or wrong. What remains is published in `zh-CN`. You can raise a score threshold to drop more of them.

## Hierarchical presentation

Not every suggestion should be applied. The comment is arranged so a reviewer can reject one in a few seconds:

- A category heading groups suggestions. Skip a category that does not apply.
- Each suggestion starts as one line. Open it for the full explanation and a code example.
- The example is illustrative. Applying it on Gitee is a separate edit. Inline publication, when it is enabled, uses Gitee's diff `position` and is skipped when that position cannot be resolved. See [Gitee installation](../installation/gitee.md#verified-behavior).

:::note[Fast review]
The layout is meant for a quick pass, on the order of a few seconds per suggestion.
:::

## Score, then re-rank

The first call generates suggestions and tries to order them. Models are weak at writing suggestions and ranking them in the same pass, and the first list often contains items that are obviously wrong.

The follow-up call:

1. Shows the model the whole list at once.
2. Asks for a score from 0 to 10 and a short reason for each item.
3. Re-ranks by that score and drops anything scored 0.
4. Optionally drops anything below `suggestions_score_threshold`.

Scoring the list together gives the model more context than scoring each item alone.

## Example

<img src="/img/self_reflection1.png" alt="Self-reflection scores" width="768" />
<img src="/img/self_reflection2.png" alt="Suggestions after re-ranking" width="768" />

## Configuration

```toml
[pr_code_suggestions]
suggestions_score_threshold = 0 # drop suggestions scored below this (0-10)
```

The pass uses the same model chain as the rest of the command: `gpt-6.1-sol`, then `glm-5.3` if the primary call falls over. See [Changing a model](../usage-guide/changing_a_model.md).
