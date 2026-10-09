---
title: "Add Docs"
sidebar_position: 6
---

## Overview

`/add_docs` looks through the pull-request diff for functions, classes, and methods that have no documentation, and drafts docs for them.

Comment on the pull request:

```
/add_docs
```

Or pass `add_docs` to the [Gitee CLI image](./index.md#run). The URL must be `https://gitee.com/owner/repo/pulls/N` or `https://e.gitee.com/<enterprise>/repos/owner/repo/pulls/N`.

## What is published

Suggestions are inline comments on the diff. Gitee cannot commit them. Apply the text yourself if you want it in the branch.

While the command runs, and when `config.publish_output` is enabled, a temporary comment says `正在生成文档...` and is removed before the inline comments are posted.

The docs style follows the language of the change:

| Language | Format |
|----------|--------|
| Python | Docstring. `pr_add_docs.docs_style` chooses the Python style. |
| Java | Javadoc |
| JavaScript / TypeScript | JSDoc |
| C++ | Doxygen |
| Other | A short generic block |

`pr_add_docs.docs_style` defaults to `Sphinx`. Other Python values are `Google Style with Args, Returns, Attributes...etc`, `Numpy Style`, `PEP257`, and `reStructuredText`.

## Configuration

```toml
[pr_add_docs]
docs_style = "Sphinx"
extra_instructions = "Document public methods only."
```

| Key | Default | Effect |
|-----|---------|--------|
| `docs_style` | `Sphinx` | Python docstring style. |
| `extra_instructions` | empty | Extra directions for this command. |

A command override looks like this:

```
/add_docs --pr_add_docs.docs_style="Numpy Style"
```

If every inline comment fails to publish, the command records a failure and tries to post **Failed to publish code documentation for this PR.** A partial success is kept.
