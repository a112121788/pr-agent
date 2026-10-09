---
title: "动态上下文"
sidebar_position: 4
---

`支持的 Git 平台：GitHub、GitLab、Bitbucket、Azure DevOps、Gitea`

PR-Agent 使用**非对称且动态的上下文策略**，改进 AI 对拉取请求中代码变更的分析。
它在变更之前提供的上下文多于变更之后，并根据代码结构（例如外层函数或类）动态调整上下文。
这种方法在提供足够上下文以进行准确分析的同时，避免“大海捞针”式的信息过载，以免降低 AI 表现或超出令牌限制。

## 介绍

拉取请求的代码变更以统一 diff 格式获取，在每个修改节的前后各显示三行上下文，新增用 “+” 标记，删除用 “-” 标记。

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

这种统一 diff 格式对 AI 模型来说可能难以准确解释，因为它为理解代码变更的完整范围提供的上下文有限。
用 “+”、“-” 和 “ ” 符号分别表示新增、删除和未变更行的代码呈现方式，也不同于通常用来训练 AI 模型的标准代码格式。

## 扩大上下文窗口的挑战

虽然扩大上下文窗口在技术上可行，但它带来更根本的权衡：

优点：

- 增强的上下文让模型更好地理解和定位代码变更，（可能）得到更精确的分析和建议。没有足够的上下文，模型可能难以理解代码变更并提供相关反馈。

缺点：

- 过多上下文可能用无关信息淹没模型，形成“大海捞针”的情形，难以聚焦相关细节（实际发生变化的代码）。
已知当上下文变大时，LLM 质量会下降。
拉取请求常常涵盖许多文件中的多处变更，修改的代码可能长达数百行。这种复杂性确实存在用过多上下文淹没模型的风险。

- 上下文增加会扩大令牌数，增加处理时间和成本，并可能使模型无法在单次处理中处理整个拉取请求。

## 非对称且动态的上下文

为应对这些挑战，PR-Agent 采用**非对称**且**动态**的上下文策略，为每次代码变更向模型提供更聚焦、更相关的上下文信息。

**非对称：**

我们首先认识到，代码变更之前的上下文对于理解修改通常比之后的上下文更关键。
因此，PR-Agent 实现非对称上下文策略，把上下文窗口拆成两段：一段用于变更之前的代码，另一段用于变更之后的代码。

通过独立调整每个上下文窗口，PR-Agent 可以为单次代码变更向模型提供更贴合、更相关的上下文。

**动态：**

我们也采用“动态”上下文策略。
我们首先认识到，代码变更的最优上下文常常对应其外层代码组件（例如函数、类），而不是固定行数。
因此，我们根据代码结构动态调整上下文窗口，确保模型收到每次修改最相关的信息。

为避免用过多上下文淹没模型，我们在识别外层组件时限制搜索的行数。
这种平衡既能全面理解，又能保持效率并限制上下文令牌用量。

## 附录——相关配置选项

```toml
[config]
patch_extension_skip_types =[".md",".txt"]  # Skip files with these extensions when trying to extend the context
allow_dynamic_context=true                  # Allow dynamic context extension
max_extra_lines_before_dynamic_context = 8  # will try to include up to X extra lines before the hunk in the patch, until we reach an enclosing function or class
patch_extra_lines_before = 3                # Number of extra lines (+3 default ones) to include before each hunk in the patch
patch_extra_lines_after = 1                 # Number of extra lines (+3 default ones) to include after each hunk in the patch
```
