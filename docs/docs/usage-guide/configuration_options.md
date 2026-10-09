---
title: "Configuration File"
sidebar_position: 3
---

Tools used by Gitee PR-Agent read a TOML configuration. Three persistent layers exist:

1. [Local](./configuration_options.md#local-configuration-file) configuration file
2. [Global](./configuration_options.md#global-configuration-file) configuration file
3. [External configuration URL](./configuration_options.md#external-configuration-url) (CLI)

Local configuration overrides global configuration, and global configuration overrides an external URL. Environment variables of the form `SECTION__KEY` override those files.

For every key, see the [configuration reference](./configuration_reference.md), which is rendered from [`configuration.toml`](https://github.com/the-pr-agent/pr-agent/blob/main/pr_agent/settings/configuration.toml). Each tool also has its own section. `/review` reads `[pr_reviewer]`.

:::tip[Edit only what you need]
Keep the file small. Copying the whole default file makes later default changes look like local overrides.
:::

:::tip[Show the settings a run used]
When `config.output_relevant_configurations` is true, each tool adds a collapsible block with the settings that applied. Comment arguments cannot turn this on, because the block can include host-controlled values. Set it in `.pr_agent.toml` or the host configuration.
:::

## Local configuration file {#local-configuration-file}

Upload `.pr_agent.toml` to the repository. Gitee reads it from the pull request **target** branch, not from the head branch, so the pull request cannot point the review at a file it just added. The file must already be on the target branch before the command runs.

The path defaults to `.pr_agent.toml` (`gitee.repo_setting`).

These Gitee keys are host-only. A repository file cannot set them:

- `gitee.api_base`
- `gitee.webhook_secret`
- `gitee.skip_ssl_verification`
- `gitee.ssl_ca_cert`

Model endpoints and credentials are also host-only. That includes `openai.api_base` and `openai.key`. Set them with `OPENAI__API_BASE` and `OPENAI__KEY` on the host, as described in [Changing a model](./changing_a_model.md).

Example `.pr_agent.toml`:

```toml
[pr_reviewer]
extra_instructions = """\
- instruction a
- instruction b
"""
```

The Gitee provider does not use `--config-branch` or `PR_AGENT_CONFIG_BRANCH`. Those options do not move the file off the target branch.

## Global configuration file {#global-configuration-file}

Set `config.global_settings_repo` on the **host** to the name of a repository in the same Gitee owner (namespace). PR-Agent reads `.pr_agent.toml` from that repository's default branch and applies it to every repository under the owner. The setting is empty by default, which disables the feature. A repository file or a comment cannot set `global_settings_repo`.

With `global_settings_repo = "pr-agent-settings"` and a pull request in `my-org/my-repo`, the file that is read is `my-org/pr-agent-settings` on its default branch. Keys in `my-org/my-repo`'s own `.pr_agent.toml` override it.

The token in `GITEE__PERSONAL_ACCESS_TOKEN` must be able to read both repositories. If the settings repository or file is missing, PR-Agent skips the global file and continues with the repository-local file.

:::note[Caching]
The Gitee webhook process caches the global file in memory for up to 15 minutes. A change in the settings repository can take that long to appear. CLI runs are short-lived and read the file once per invocation.
:::

`use_global_settings_file` defaults to true but reads nothing until `global_settings_repo` is set. To ignore the global file:

```toml
[config]
use_global_settings_file = false
```

## External configuration URL {#external-configuration-url}

On the CLI, merge an extra `.pr_agent.toml` before the global and repository-local files. Use this when the shared file is not in the Gitee owner namespace, or when CI should choose the defaults without committing them to the target repository.

### Usage {#usage}

Pass `--extra_config_url`, or set `PR_AGENT_EXTRA_CONFIG_URL`:

```bash
uv run python -m pr_agent.cli \
  --pr_url=<Gitee pull request URL> \
  --extra_config_url=https://config.example.com/pr-agent/shared.toml \
  review
```

Accepted values:

- `https://…` or `http://…`, fetched at runtime
- `file:///path/to/shared.toml`
- a bare filesystem path, treated like `file://`

### Authentication for private endpoints {#authentication-for-private-endpoints}

For a private URL, set one header in `PR_AGENT_EXTRA_CONFIG_AUTH_HEADER` as `<HeaderName>: <value>`:

```bash
export PR_AGENT_EXTRA_CONFIG_AUTH_HEADER="Authorization: Bearer <your-token>"
```

### Precedence {#precedence}

The external file is applied first. Later layers override it:

```text
built-in defaults
  < --extra_config_url
    < global pr-agent-settings
      < local .pr_agent.toml (pull request target branch)
        < environment variables (SECTION__KEY)
```

### Security and limits {#security-and-limits}

The file goes through the same loader as a repository `.pr_agent.toml`. Includes, preloads, custom loaders, and other directives that could run code or read arbitrary files are rejected. The fetch also:

- stops at **1 MB**
- times out after **10 seconds**
- accepts only `http`, `https`, `file`, or a bare local path

A failed fetch is logged. PR-Agent continues with the remaining layers. Host-only keys in the external file are still dropped.
