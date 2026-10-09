---
title: "生成标签"
sidebar_position: 7
---

## 概述

`generate_labels` 工具扫描拉取请求中的代码变更，并根据变更的内容和上下文生成自定义标签。

可以在任意拉取请求上评论来手动调用：

```
/generate_labels
```

## 使用示例

在任意拉取请求上评论 `/generate_labels` 来手动调用该工具。

工具会分析拉取请求并添加合适的标签。

## 配置选项

`generate_labels` 工具使用 `[pr_description]` 节中的配置来处理自定义标签。

### 启用自定义标签

要使用自定义标签，需要在配置中启用：

```toml
[config]
enable_custom_labels = true
```

### 定义自定义标签

可以在 `[custom_labels]` 节中定义自己的自定义标签。示例见 [custom_labels.toml](https://github.com/the-pr-agent/pr-agent/blob/main/pr_agent/settings/custom_labels.toml)。

配置示例：

```toml
[custom_labels."Bug fix"]
description = "A fix for a bug in the codebase"

[custom_labels."Feature"]
description = "A new feature or enhancement"

[custom_labels."Documentation"]
description = "Documentation changes only"

[custom_labels."Tests"]
description = "Adding or modifying tests"

[custom_labels."Refactoring"]
description = "Code refactoring without functional changes"
```

### 标签如何应用

1. 工具分析拉取请求 diff 和提交消息
2. 它使用 AI 判断哪些标签最匹配拉取请求内容
3. 标签会自动应用到拉取请求（如果 Git 提供方支持）
4. 如果标签无法直接应用，则会作为评论发布

`/generate_labels` 和 `/describe` 都会在发布前过滤模型生成的标签。
允许集合包含内置 PR 类型（`Bug fix`、`Tests`、`Enhancement`、
`Documentation`、`Other`），以及启用自定义标签时已配置的自定义标签名。启用了自定义标签但未配置自定义集合时，默认集合还会包含 `Bug fix with tests`。匹配忽略大小写，未知的生成标签会被丢弃并记录警告。人工添加的既有标签会被保留，不受此过滤器限制。

`bug_fix`、`RELEASE_READY` 这类提示枚举键会解析为允许的显示名称，忽略大小写。如果非空的模型响应只包含被拒绝的标签，`/generate_labels` 会保持当前标签不变。显式的 `labels: []` 响应则保留原有行为：清除机器人拥有的旧标签，同时保留人工添加的标签。

## 与 `/describe` 标签的比较

`/describe` 工具也会在输出中生成标签。主要区别是：

| 特性 | `/generate_labels` | `/describe` |
|---------|-------------------|-------------|
| 用途 | 专门生成标签 | 完整的拉取请求描述，并附带标签 |
| 输出 | 仅标签 | 标题、摘要、导览和标签 |
| 自定义标签 | ✅ 支持 | ✅ 支持 |
| 使用场景 | 只需要标签时 | 需要完整拉取请求描述时 |

## 提示

- 使用符合团队工作流和标签约定的自定义标签
- 结合自动化，在拉取请求打开时自动打标签
- 检查生成的标签；如果 AI 持续误分类，就调整自定义标签的描述
