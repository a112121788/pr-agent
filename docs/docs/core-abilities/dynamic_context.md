---
title: "Dynamic Context"
sidebar_position: 4
---

`Supported Git platform: Gitee`

Gitee PR-Agent uses an **asymmetric and dynamic context** around each hunk. It keeps more lines before a change than after it, and it widens that window when the change sits inside a function or class. The goal is enough context for an accurate comment without a needle-in-a-haystack prompt that blows the token budget. The default model is `gpt-6.1-sol` (`glm-5.3` is the fallback), and that budget is what the packer in [Compression strategy](./compression_strategy.md) enforces.

## What Gitee returns

Changed lines arrive as a unified diff. A typical hunk shows three context lines before and after the edit. Additions are marked `+` and deletions `-`.

```diff
@@ -12,5 +12,5 @@ def func1():
 code line that already existed in the file...
 code line that already existed in the file...
 code line that already existed in the file....
-code line that was removed in the PR
+new code line added in the PR
 code line that already existed in the file...
 code line that already existed in the file...
 code line that already existed in the file...

@@ -26,2 +26,4 @@ def func2():
...
```

That format is a poor prompt by itself. Three lines often hide the enclosing function, and the `+` / `-` / ` ` markers are not how models usually see source code.

## Why not send the whole file every time

A wider window helps the model place the edit. It also has a cost:

- Too little context and the model misreads the change.
- Too much context hides the lines that actually changed. Quality drops as the prompt grows, and a Gitee pull request often touches many files.
- Extra lines spend tokens. They add latency and can force the segmented review described in [Compression strategy](./compression_strategy.md).

## Asymmetric and dynamic windows

**Asymmetric.** The lines above a change usually explain it better than the lines below it. The before-window and the after-window are separate settings.

**Dynamic.** The useful window is often the enclosing function or class, not a fixed line count. Gitee PR-Agent walks upward from the hunk until it hits that boundary, and it stops after a configured number of extra lines so one large function cannot consume the budget.

## Configuration

These defaults live in `configuration.toml`:

```toml
[config]
patch_extension_skip_types = [".md", ".txt"]  # do not extend context for these extensions
allow_dynamic_context = true                   # walk up to an enclosing function or class
max_extra_lines_before_dynamic_context = 10    # extra lines to search before the hunk
patch_extra_lines_before = 5                   # extra lines before each hunk, on top of the 3 in the diff
patch_extra_lines_after = 1                    # extra lines after each hunk, on top of the 3 in the diff
```
