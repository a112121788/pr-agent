---
title: "Introduction"
sidebar_position: 2
---

After [installation](../installation/index.md), there are three basic ways to invoke PR-Agent:

1. Locally running a CLI command
2. Online usage - by <a href="https://github.com/the-pr-agent/pr-agent/pull/229#issuecomment-1695021901" target="_blank" rel="noopener noreferrer">commenting</a> on a PR
3. Enabling PR-Agent tools to run automatically when a new PR is opened

Specifically, CLI commands can be issued by invoking a pre-built [docker image](../installation/locally.md#using-docker-image), or by invoking a [locally cloned repo](../installation/locally.md#run-from-source).

For online usage, set up the [Gitee webhook](../installation/gitee.md). It can run the tools automatically when a pull request is opened, and it also accepts slash commands in pull-request comments.
