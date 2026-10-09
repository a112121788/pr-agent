---
title: "添加文档"
sidebar_position: 6
---

## 概述

`add_docs` 工具扫描拉取请求中的代码变更，并为缺少文档的代码组件（例如函数、类和方法）建议文档。

可以在任意拉取请求上评论来手动调用：

```
/add_docs
```

## 使用示例

在任意拉取请求上评论 `/add_docs` 来手动调用该工具：

<img src="/img/add_docs_comment.png" alt="添加文档" width="512" />

工具会把文档建议生成为行内代码建议。

### 各语言的文档风格

工具会自动检测编程语言，并按相应格式生成文档：

| 语言 | 文档格式 |
|----------|---------------------|
| Python | 文档字符串（Sphinx、Google、Numpy 风格） |
| Java | Javadocs |
| JavaScript/TypeScript | JSdocs |
| C++ | Doxygen |
| 其他 | 通用文档 |

## 配置选项

在 `[pr_add_docs]` 节下可以使用以下选项：

| 选项 | 类型 | 默认值 | 说明 |
|--------|------|---------|-------------|
| `extra_instructions` | string | `""` | 给 AI 模型的附加指令 |
| `docs_style` | string | `"Sphinx"` | Python 文档风格。可选：`"Sphinx"`、`"Google Style with Args, Returns, Attributes...etc"`、`"Numpy Style"`、`"PEP257"`、`"reStructuredText"` |
| `file` | string | `""` | 要编写文档的特定文件（多个组件同名时有用） |
| `class_name` | string | `""` | 要针对的特定类名（同一文件中方法同名时有用） |

### 配置示例

要自定义文档风格，把以下内容加入配置文件：

```toml
[pr_add_docs]
docs_style = "Google Style with Args, Returns, Attributes...etc"
extra_instructions = "Focus on documenting public methods and include usage examples"
```

### 命令行选项

可以直接在命令中传入配置选项：

```
/add_docs --pr_add_docs.docs_style="Numpy Style"
```

## 工作原理

1. 工具分析拉取请求 diff，找出缺少文档的代码组件（函数、类、方法）
2. 它根据代码上下文和语言，用 AI 生成合适的文档
3. 文档建议以行内代码建议的形式发布，单击即可应用

### 发布失败

启用 `CONFIG.PUBLISH_OUTPUT` 时，PR-Agent 会把未成功的批量发布逐条重试。如果批量和每一次单独重试都明确报告失败，它会尝试发布 **Failed to publish code documentation for this PR.**，并把该命令记为失败。部分成功或提供方结果未确认时，不会触发这种全部失败的结果。
