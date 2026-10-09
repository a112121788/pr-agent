---
title: "为拉取请求获取工单上下文"
sidebar_position: 5
---

`支持的 Git 平台：Gitee`

Gitee PR-Agent 会读取 Gitee 议题，把标题和正文放进审查提示词。`/describe` 和 `/review` 再拿 diff 对照这段文字。议题读取已经实现。部分企业仓库的议题 API 会返回 HTTP 404；这些议题会被跳过，命令继续执行，只是没有它们的上下文。

## 读到什么

API 成功返回的每条议题，提示词里只有：

1. 标题
2. 正文

不会从 Gitee 读取标签、子议题或附件。议题 API 返回 HTTP 404 时，该议题的内容不会送给模型。部分企业仓库即使网页上能打开议题，接口仍会 404。此时把需求写进拉取请求描述；描述始终在提示词里。见 [本地与全局元数据](./metadata.md)。

## 拉取请求如何指向议题

引用的读取顺序是：拉取请求描述，然后源分支名，然后标题。重复引用只取一次。最多把三条议题放进提示词。

完整议题 URL 只在配置的 Gitee 网页源站上识别（`gitee.url`，默认 `https://gitee.com`）：

- `https://gitee.com/<owner>/<repo>/issues/<number>`
- `<owner>/<repo>#<number>`
- 同一仓库内的 `#<number>`，最多六位数字

`config.extract_issue_from_branch` 为 true（默认）时会扫描分支名。默认模式是：分支开头，或 `/` 之后，有一到六位数字，后面是 `-` 或名字结束：

- `123-fix-bug`
- `feature/123-fix-bug`

可选模式：

```toml
[config]
extract_issue_from_branch = true
# 恰好一个捕获组，用来取议题编号。无效模式会被忽略。
branch_issue_regex = ""
# 只作用于拉取请求描述。恰好一个捕获组，用来取议题编号。
description_issue_regex = ""
```

实际请求是 Gitee OpenAPI v5 上的 `GET /repos/{owner}/{repo}/issues/{number}`，使用主机令牌。404 视为「未找到」并写入日志。审查的其余部分仍会继续。

## 描述与审查

`/describe` 把议题标题和正文当作摘要的额外上下文。

`/review` 同样使用这段文字，并且默认写出工单符合度（`pr_reviewer.require_ticket_analysis_review = true`）。每条取到的议题按模型列出的需求标注：

- Fully compliant（完全符合）
- Partially compliant（部分符合）
- Not compliant（不符合）
- PR Code Verified（代码已核对）—— diff 覆盖了能在代码里核对的需求，其余仍要人来看（例如界面检查）

<img src="/img/ticket_compliance_review.png" alt="Gitee 审查中的工单符合度" width="768" />

关闭该块：

```toml
[pr_reviewer]
require_ticket_analysis_review = false
```

没有取到议题内容时不会写符合度，包括引用的议题全部返回 HTTP 404 的情况。
