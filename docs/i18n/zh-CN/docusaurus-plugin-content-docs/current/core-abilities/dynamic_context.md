---
title: "动态上下文"
sidebar_position: 4
---

`支持的 Git 平台：Gitee`

Gitee PR-Agent 在每个差异块周围使用**非对称且动态的上下文**。变更之前的行比变更之后的行更多，若变更落在函数或类内部，窗口还会再加宽。目标是让评论足够准确，又避免提示词变成大海捞针，撑破令牌预算。默认模型是 `gpt-6.1-sol`（备用 `glm-5.3`）。[压缩策略](./compression_strategy.md) 里的装箱按的就是这份预算。

## Gitee 返回什么

变更行以统一 diff 到来。典型差异块在编辑前后各有三行上下文。新增标为 `+`，删除标为 `-`。

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

只拿这份 diff 做提示词并不合适。三行上下文经常看不到外层函数，而 `+` / `-` / 空格这些标记也不是模型平时见到的源码写法。

## 为什么不每次都送整文件

窗口更宽，模型更容易定位修改，但也有代价：

- 上下文太少，模型会误读变更。
- 上下文太多，真正改过的行会被淹没。提示词变长后质量下降，而一个 Gitee 拉取请求常常改很多文件。
- 多出来的行消耗令牌，增加延迟，也可能触发 [压缩策略](./compression_strategy.md) 里的分段审查。

## 非对称窗口和动态窗口

**非对称。** 变更上方的行通常比下方的行更能解释这次修改。前后窗口是分开的设置。

**动态。** 有用的窗口往往是外层函数或类，而不是固定行数。Gitee PR-Agent 从差异块向上找，直到碰到这个边界，并在配置的额外行数处停下，避免一个超大函数吃掉预算。

## 配置

下列默认值在 `configuration.toml` 中：

```toml
[config]
patch_extension_skip_types = [".md", ".txt"]  # 这些扩展名不扩展上下文
allow_dynamic_context = true                   # 向上找到外层函数或类
max_extra_lines_before_dynamic_context = 10    # 在差异块之前最多再搜索的行数
patch_extra_lines_before = 5                   # 每个差异块之前的额外行，加在 diff 自带的 3 行之上
patch_extra_lines_after = 1                    # 每个差异块之后的额外行，加在 diff 自带的 3 行之上
```
