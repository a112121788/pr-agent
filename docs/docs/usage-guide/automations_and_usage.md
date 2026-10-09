---
title: "Usage and Automation"
sidebar_position: 5
---

This build supports Gitee only. Install the webhook with the [Gitee integration guide](../installation/gitee.md). The service image is `ecloud-tcr.tencentcloudcr.com/ecloud_project/pr-agent:latest`, built from the `gitee_app` target.

## Local repo (CLI) {#local-repo-cli}

A local run uses the configuration on the machine that launches the CLI. Set `config.git_provider` to `gitee` and pass a Gitee pull-request URL (`https://gitee.com/<owner>/<repo>/pulls/<number>`).

```bash
CONFIG__GIT_PROVIDER=gitee \
GITEE__PERSONAL_ACCESS_TOKEN=<personal_access_token> \
OPENAI__KEY=<your_openai_api_key> \
OPENAI__API_BASE=<your_openai_api_base> \
uv run python -m pr_agent.cli --pr_url=<pr_url> review
```

The same environment works with the other tools:

- **Review**: `uv run python -m pr_agent.cli --pr_url=<pr_url> review`
- **Describe**: `uv run python -m pr_agent.cli --pr_url=<pr_url> describe`
- **Improve**: `uv run python -m pr_agent.cli --pr_url=<pr_url> improve`
- **Ask**: `uv run python -m pr_agent.cli --pr_url=<pr_url> ask "Write me a poem about this PR"`
- **Update changelog**: `uv run python -m pr_agent.cli --pr_url=<pr_url> update_changelog`

Use the virtualenv from `uv sync`, or an environment where the `pr_agent` package imports. `<pr_url>` must be a Gitee pull request. Other git hosts are not accepted.

`/update_changelog` only publishes a comment. Gitee has no `push_code` capability, so PR-Agent does not commit `CHANGELOG.md`.

**Notes:**

1. Repository-configurable values can also be set on the command line:

```bash
uv run python -m pr_agent.cli --pr_url=<pr_url> review --pr_reviewer.extra_instructions="focus on the file: ..."
```

Host-controlled values are rejected. That includes `GITEE__PERSONAL_ACCESS_TOKEN`, `GITEE__WEBHOOK_SECRET`, `gitee.api_base`, `gitee.skip_ssl_verification`, `gitee.ssl_ca_cert`, and model endpoint settings such as `openai.api_base`. See [Local configuration file](./configuration_options.md#local-configuration-file).

2. To print results locally instead of commenting on the pull request, set:

```toml
[config]
publish_output = false
verbosity_level = 2
```

3. `git_provider` must be `gitee` (`CONFIG__GIT_PROVIDER=gitee`). This build does not select another provider.

4. For scripts that should fail when a tool fails, enable error propagation:

```bash
uv run python -m pr_agent.cli --pr_url=<pr_url> review --config.propagate_tool_errors=true
```

With `config.propagate_tool_errors=true`, `pr-agent` and `python -m pr_agent.cli` exit with status 1 when a propagated tool error fails the request, or when a tool records a failure and still returns successfully. In the latter case the CLI logs a warning. The flag is off by default, so those failures still exit 0. Argparse usage errors still exit 2.

## Online usage {#online-usage}

Online usage means a comment on the Gitee pull request. The comment is handled only when it starts with `/`.

- **Review**: `/review`
- **Describe**: `/describe`
- **Improve**: `/improve`
- **Ask**: `/ask "..."`
- **Update changelog**: `/update_changelog`

`/update_changelog` posts the generated changelog as a comment. It does not push a commit.

Append `--<section>.<key>=<value>` to override a repository-configurable setting for that run:

```text
/review --pr_reviewer.extra_instructions="..." --pr_reviewer.require_score_review=false
```

Host-controlled settings, including the Gitee token, webhook secret, TLS settings, and model endpoint, cannot be changed from a comment. Comment `/config` to list the settings that can. The full list is the [configuration reference](./configuration_reference.md).

## Gitee webhook {#gitee-webhook}

The webhook server is the `gitee_app` target. It listens for:

```text
POST /api/v1/gitee_webhooks
```

Run the published image with the host environment:

```bash
CONFIG__GIT_PROVIDER=gitee
GITEE__PERSONAL_ACCESS_TOKEN=<personal_access_token>
GITEE__WEBHOOK_SECRET=<webhook_secret>
OPENAI__KEY=<your_openai_api_key>
OPENAI__API_BASE=<your_openai_api_base>
```

`GITEE__WEBHOOK_SECRET` is required. An empty secret rejects every webhook with HTTP 403. In the Gitee repository, set the webhook URL to `https://<PR_AGENT_HOSTNAME>/api/v1/gitee_webhooks`, use that same secret, and subscribe to pull-request and comment events. Push events do not run commands.

PR-Agent checks the signature before it parses the JSON body.

| Header | Role |
| --- | --- |
| `X-Gitee-Timestamp` | Unix timestamp, in milliseconds, from Gitee. |
| `X-Gitee-Token` | Base64 HMAC-SHA256 of `<timestamp>\n<secret>`. |

The signed content is the timestamp, a newline, and the webhook secret. Timestamps more than one hour from the server clock are rejected. A bad signature returns HTTP 401.

### Default mode {#github-app}

On a newly opened pull request the webhook runs `/describe`, `/review`, and `/improve`. That is the default mode for this build. A comment runs only when it starts with `/`, and then runs only that command.

### Commands when a pull request is opened {#github-app-automatic-tools-when-a-new-pr-is-opened}

`gitee.pr_commands` is the list that runs when a pull request is opened. Unset, it is:

```toml
[gitee]
pr_commands = [
    "/describe",
    "/review",
    "/improve",
]
```

Set the list in the host configuration, or in the repository [`.pr_agent.toml`](./configuration_options.md#local-configuration-file), to change which tools run. An empty list runs nothing on open. Arguments on a command apply to that automatic run:

```toml
[gitee]
pr_commands = [
    "/describe",
    "/review --pr_reviewer.extra_instructions='focus on the file: ...'",
    "/improve",
]
```

Tool defaults such as `[pr_description]` still apply to both automatic runs and comments. For example, `generate_ai_title = true` makes every `/describe` run generate a title.

Gitee reads `.pr_agent.toml` from the pull request's target branch. Push events are ignored, so new commits on an open pull request do not start another automatic run. Comment on the pull request to run a tool again.

## Automatic feedback {#pr-agent-automatic-feedback}

Automatic feedback in this build is the open-pull-request list above. There is no GitHub App, GitHub Action, GitLab pipeline, Bitbucket app, or Azure DevOps webhook to configure.

To stop automatic commands, set `gitee.pr_commands` to `[]`. Comment commands that start with `/` still run. Ignore rules in [Additional configurations](./additional_configurations.md#ignoring-automatic-commands-in-prs) skip both automatic runs and comment commands that match a title, author, label, branch, or repository.
