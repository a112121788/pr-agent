---
title: "添加文档"
sidebar_position: 6
---

## 概述

`/add_docs` 在拉取请求 diff 里查找没有文档的函数、类和方法，并为它们起草文档。

在拉取请求上评论：

```
/add_docs
```

也可以把 `add_docs` 传给 [Gitee CLI 镜像](./index.md#run)。URL 必须是 `https://gitee.com/owner/repo/pulls/N` 或 `https://e.gitee.com/<enterprise>/repos/owner/repo/pulls/N`。

## 发布内容

建议以 diff 上的行内评论发布。Gitee 不能把它们提交进分支。如果要留在分支里，请自己把文字加进去。

命令运行期间，若启用了 `config.publish_output`，会先发一条临时评论 `正在生成文档...`，行内评论发出前再删掉它。

文档格式跟随变更的语言：

| 语言 | 格式 |
|------|------|
| Python | 文档字符串。`pr_add_docs.docs_style` 选择 Python 风格。 |
| Java | Javadoc |
| JavaScript / TypeScript | JSDoc |
| C++ | Doxygen |
| 其他 | 一段简短的通用说明 |

`pr_add_docs.docs_style` 默认为 `Sphinx`。其他 Python 取值是 `Google Style with Args, Returns, Attributes...etc`、`Numpy Style`、`PEP257` 和 `reStructuredText`。

## 配置

```toml
[pr_add_docs]
docs_style = "Sphinx"
extra_instructions = "Document public methods only."
```

| 键 | 默认值 | 作用 |
|----|--------|------|
| `docs_style` | `Sphinx` | Python 文档字符串风格。 |
| `extra_instructions` | 空 | 这条命令的额外说明。 |

命令上的覆盖像这样：

```
/add_docs --pr_add_docs.docs_style="Numpy Style"
```

如果每一条行内评论都发布失败，命令会记为失败，并尝试发布 **Failed to publish code documentation for this PR.** 部分成功的评论会保留。
