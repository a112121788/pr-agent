---
title: "压缩策略"
sidebar_position: 3
---

`支持的 Git 平台：Gitee`

## 概述

Gitee PR-Agent 分两步准备 Gitee 拉取请求的 diff。先把 diff 装进模型的令牌预算。仍然放不下时，`/review` 和 `/describe` 默认分段，而不是把剩下的文件悄悄丢掉。

1. 拉取请求足够小，一条提示词放得下（系统提示词加用户提示词）。
2. 拉取请求太大，一条提示词放不下。

两种情形都从同一套文件排序开始。

#### 按仓库语言优先

1. 去掉二进制文件和非代码文件（图片、PDF 等）。
2. 取仓库里的主要语言。
3. 按这些语言把拉取请求文件分组，最常用的语言在前：

   * `[[file.py, file2.py], [file3.js, file4.jsx], [readme.md]]`

### 小拉取请求

整份 diff 能放进一条提示词：

1. 去掉二进制文件和非代码文件。
2. 扩展每个差异块周围的上下文。多加多少行由 [动态上下文](./dynamic_context.md) 的设置决定。

### 大拉取请求

#### 为什么要装箱

Gitee 拉取请求可以很长，也不是每个差异块都同样重要。装箱是在发起额外模型调用之前，在令牌预算内尽量留下相关代码。

#### 压缩什么

新增优先于删除：

* 被删除的文件收成一份 `deleted files` 列表。
* 文件补丁里只含删除的差异块会被去掉。

#### 按令牌装入

上述处理之后，用 [tiktoken](https://github.com/openai/tiktoken) 给补丁计数，再按下面的顺序装入：

1. 在每个语言组内按令牌数排序，大的在前：
    * `[[file2.py, file.py], [file4.jsx, file3.js], [readme.md]]`
2. 按这个顺序遍历补丁。
3. 持续加入补丁，直到提示词距模型令牌上限还留有一段缓冲。
4. 若仍有补丁，把它们放进 `other modified files`，直到硬上限，然后停止。
5. 若还有空位，再加入 `deleted files`，直到硬上限，然后停止。

#### 分段审查与描述

装箱不是最后一步。本构建里，文件装不下时两个工具都会继续：

| 工具 | 默认 | 行为 |
| --- | --- | --- |
| `/review` | `pr_reviewer.enable_large_pr_chunking = true` | diff 最多拆成 `pr_reviewer.max_number_of_calls` 段（默认 `3`）。逐段审查后合并成一条评论。 |
| `/describe` | `pr_description.enable_large_pr_handling = true` | 再发起模型调用并合并结果，从而覆盖更多文件。 |

仍然放不下的文件会列在审查覆盖范围页脚里。失败的分段会先改走备用模型（主模型为 `glm-5.3` 时，备用是 `gpt-6.1-sol`），然后才把成功的分段作为部分审查发出。分段开关在 [其他选项](../tools/review.md#其他选项)。描述工具的开关是 [Describe 配置](../tools/describe.md#配置) 里的 `enable_large_pr_handling`。

分段里发出的行内评论同样使用 Gitee 的 diff `position`。见 [Gitee 安装](../installation/gitee.md#已验证的行为)。

#### 示例

<img src="/img/git_patch_logic.png" alt="Gitee 拉取请求补丁如何装箱" width="768" />
