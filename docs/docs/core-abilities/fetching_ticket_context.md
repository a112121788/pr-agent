---
title: "Fetching Ticket Context for PRs"
sidebar_position: 5
---

`Supported Git platform: Gitee`

Gitee PR-Agent reads Gitee issues and adds their title and body to the review prompt. `/describe` and `/review` then judge the diff against that text. Issue reading is implemented. On some enterprise repositories the issues API returns HTTP 404; those issues are skipped and the command continues without them.

## What is fetched

For each issue that the API returns, the prompt receives:

1. Title
2. Body

Labels, sub-issues, and attachments are not read from Gitee. If the issues API responds with HTTP 404, nothing from that issue is sent to the model. This happens on some enterprise repositories even when the issue is visible in the web UI. Put the requirements in the pull-request description when that occurs; the description is always part of the prompt. See [Local and global metadata](./metadata.md).

## How a pull request points at an issue

References are taken from the pull-request description, then the source branch name, then the title. Repeated references are fetched once. At most three issues are added to the prompt.

Full issue URLs are recognized only on the configured Gitee web origin (`gitee.url`, default `https://gitee.com`):

- `https://gitee.com/<owner>/<repo>/issues/<number>`
- `<owner>/<repo>#<number>`
- `#<number>` in the same repository, up to six digits

Branch names are scanned when `config.extract_issue_from_branch` is true (the default). The default pattern is one to six digits at the start of the branch, or after a `/`, followed by `-` or the end of the name:

- `123-fix-bug`
- `feature/123-fix-bug`

Optional patterns:

```toml
[config]
extract_issue_from_branch = true
# One capturing group for the issue number. Invalid patterns are ignored.
branch_issue_regex = ""
# Applied only to the pull-request description. One capturing group for the issue number.
description_issue_regex = ""
```

The read is `GET /repos/{owner}/{repo}/issues/{number}` on the Gitee OpenAPI v5 base, with the host token. A 404 is treated as "not found" and logged. The rest of the review still runs.

## Describe and review

`/describe` uses the issue title and body as extra context for the summary.

`/review` does the same, and by default it also writes a ticket compliance block (`pr_reviewer.require_ticket_analysis_review = true`). Each fetched issue is labeled from the requirements the model lists:

- Fully compliant
- Partially compliant
- Not compliant
- PR Code Verified — the diff covers the requirements that can be checked in code, and something else still needs a person (for example a UI check)

<img src="/img/ticket_compliance_review.png" alt="Ticket compliance on a Gitee review" width="768" />

Turn the block off with:

```toml
[pr_reviewer]
require_ticket_analysis_review = false
```

Compliance is omitted when no issue content was fetched, including when every referenced issue returned HTTP 404.
