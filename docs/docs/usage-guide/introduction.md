---
title: "Introduction"
sidebar_position: 2
---

Gitee PR-Agent reviews pull requests on Gitee. This build does not run against GitHub, GitLab, Bitbucket, or Azure DevOps.

After [installation](../installation/gitee.md), invoke it in either of these ways:

1. Locally, with the CLI and a Gitee pull-request URL.
2. Online, with the Gitee webhook. The server accepts `POST /api/v1/gitee_webhooks`.

Opening a pull request runs `/describe`, `/review`, and `/improve`. A comment on the pull request runs only when the comment starts with `/`.

The published image is `ecloud-tcr.tencentcloudcr.com/ecloud_project/pr-agent:latest`. The webhook service target is `gitee_app`. See [Usage and Automation](./automations_and_usage.md) for commands, signature checks, and environment variables.
