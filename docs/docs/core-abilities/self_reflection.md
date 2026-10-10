---
title: "自我反思"
sidebar_position: 7
---

`支持的 Git 平台：Gitee`

Gitee PR-Agent 对 `/improve` 做一次**自我反思**。模型给自己的建议打分、重排，并丢掉它标成无关或错误的条目。留下的内容以 `zh-CN` 发布。可以把分数阈值调高，再多丢掉一些。

## 分层展示

不是每条建议都该采纳。评论的结构让审查者几秒内就能否掉一条：

- 分类标题把建议分组。不适用的分类直接跳过。
- 每条建议先是一行。展开后才是完整说明和代码示例。
- 示例只供对照。要落到 Gitee 上，需要另一次编辑。启用行内发布时，锚定用的是 Gitee 的 diff `position`；这个位置算不出来就不会发。见 [Gitee 安装](../installation/gitee.md#已验证的行为)。

:::note[快速看完]
这种布局是为了快速过一遍，每条建议大约几秒。
:::

## 先打分，再重排

第一次调用生成建议，并试图排序。模型不擅长在同一次调用里又写建议又排好序，第一份列表里也常有明显错误的条目。

后续调用会：

1. 把整份列表一次交给模型。
2. 要求每条打 0 到 10 分，并给一句理由。
3. 按分数重排，丢掉 0 分的条目。
4. 可选：丢掉低于 `suggestions_score_threshold` 的条目。

整表一起打分，比逐条打分的上下文更完整。

## 示例

<img src="/img/self_reflection1.png" alt="自我反思分数" width="768" />
<img src="/img/self_reflection2.png" alt="重排后的建议" width="768" />

## 配置

```toml
[pr_code_suggestions]
suggestions_score_threshold = 0 # 丢掉低于该分数的建议（0-10）
```

这一步与命令的其余部分使用同一条模型链：`glm-5.3`，主调用失败后再用 `gpt-6.1-sol`。见 [更换模型](../usage-guide/changing_a_model.md)。
