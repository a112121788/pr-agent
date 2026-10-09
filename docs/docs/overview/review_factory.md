---
title: "Review factory"
sidebar_position: 4
---

# Gitee PR-Agent is the factory's core machine

A pull request is a change package with an intent. The review factory records four stages: intake, evidence, verdict, and merge. Gitee PR-Agent is the machine that collects evidence and drafts it in Chinese. It does not write the human verdict, and it does not press merge.

## Where the machine stops

| Stage | Record | Gitee PR-Agent |
|---|---|---|
| Intake | Intent and target line | Reads the title, description, and linked issue when Gitee returns it |
| Evidence | Results bound to the current commit | `/describe`, `/review`, `/improve`, and `/ask` |
| Verdict | Pass, return, or wait | The review comment is a draft. A person writes the verdict |
| Merge | The judged commit enters the recorded line | Stays on Gitee. The machine cannot push code |

`/review` may print **批准**, **请求修改**, or **仅评论**. Those words are evidence for the gatekeeper. They are not the factory's pass, return, or wait, and they do not authorize merge.

## What each command contributes

- `/describe` writes the change package: title, description, and file walkthrough.
- `/review` writes **PR 审查指南**, team rules, coverage, and labels such as `审查工作量N/5`.
- `/improve` writes **PR 代码建议** as a comment or inline comment. Gitee cannot commit the suggestion.
- `/ask` answers one question from the current diff. It adds evidence; it does not close the verdict.

An opened pull request runs `/describe`, `/review`, and `/improve`. A later comment runs only when it starts with `/`.

## What stays outside the machine

The machine must not rewrite the author's intent. A missing spec or a raw `<a>` / `<button>` tag becomes a blocking line in the evidence. The gatekeeper still decides whether the change returns to intake or receives a verdict.

`/review` and `/improve` have been run on `eclouddev/hlzs_web#2896`. That run shows the comments can be published. It does not show that the factory's verdict or merge happened.
