---
title: "Additional Configurations"
sidebar_position: 10
---

These settings apply to Gitee PR-Agent. The webhook and CLI are described in [Usage and Automation](./automations_and_usage.md). Install steps are in the [Gitee integration guide](../installation/gitee.md).

## Show possible configurations

The defaults live in [`configuration.toml`](https://github.com/the-pr-agent/pr-agent/blob/main/pr_agent/settings/configuration.toml). The [tools](../tools/index.md) pages explain how each tool uses them. The rendered list is the [configuration reference](./configuration_reference.md).

Comment on a pull request:

```text
/config
```

To include the settings a tool actually used, an operator sets `config.output_relevant_configurations=true` in `.pr_agent.toml` or the host configuration. A comment cannot enable it, because the block may show host-controlled values.

### Showing the agent run details {#showing-the-agent-run-details}

To record which model answered, the token counts, and how long the model phase took, enable `config.output_run_details`:

```text
/review --config.output_run_details=true
```

API-cost collection is a separate option, off by default. Enable both flags to add the estimate inside the run-details section:

```text
/review --config.output_run_details=true --config.output_run_cost=true
```

`config.output_run_details` is the public-output gate. `config.output_run_cost=true` alone collects cost data and does not add it to the comment.

On Gitee the section is appended as a collapsible block when the comment uses GitHub-flavored Markdown, and as plain text otherwise:

```text
⚙️ Agent run details
- Model: provider/fallback-model (fallback)
- Tokens: 12,340 in / 1,205 out / 13,545 total
- Time cost: 8.2s
- AI calls: 1
- Estimated API cost: $0.08 USD
```

`Model` is the model that produced the answer, marked `(fallback)` when `gpt-6.1-sol` failed and `glm-5.3` (or another fallback) took over. `Tokens` appears only when the provider reports usage. The amount is an estimate from LiteLLM's pricing data, not an invoice. The public section contains aggregate costs and model names, not prompts, responses, or API keys.

`/improve` appends the section only when it publishes a summary comment. Inline-only suggestions do not carry it. With `pr_description.use_description_markers=true`, repeated `/describe` runs accumulate one block per run.

## Ignoring files from analysis {#ignoring-files-from-analysis}

Skip generated or vendor files with:

- `IGNORE.GLOB`
- `IGNORE.REGEX`

To ignore Python files for one command:

```text
/review --ignore.glob="['*.py']"
```

To ignore them for every pull request:

```toml
[ignore]
glob = ['*.py']
```

Or with a regex:

```toml
[ignore]
regex = ['.*\.py$']
```

A `**/` segment matches zero or more directories, so `src/**/generated_*.py` also ignores `src/generated_pb.py`. `*` still matches across `/`, which is why `['*.py']` ignores every Python file.

Each glob list keeps at most 256 extra zero-directory regexes. Patterns with more than six standalone `**/` segments, or more than 256 characters, are not expanded. Configured patterns and the root-level form of a leading `**/` are always kept. Files that only a skipped variant would match are still analyzed.

## Extra instructions {#extra-instructions}

Every tool accepts `extra_instructions`. Example:

```text
/update_changelog --pr_update_changelog.extra_instructions="Make sure to update also the version ..."
```

On Gitee, `/update_changelog` still only posts a comment. The provider does not support `push_code`, so the extra instructions cannot cause a commit.

## Language settings

The shipped default for `response_language` is `zh-CN`. Set a locale from [ISO 3166](https://en.wikipedia.org/wiki/ISO_3166) and [ISO 639](https://en.wikipedia.org/wiki/ISO_639) to change the language of model-written text. A [list of locale codes](https://simplelocalize.io/data/locales/) is a useful reference.

```toml
[config]
response_language = "zh-CN"
```

Only text the model generates is translated. Static labels and table headers stay as shipped. The model must support the locale.

## Log level

```toml
[config]
log_level = "DEBUG" # "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"
```

The default is `DEBUG`. Use `INFO` or `WARNING` for a quieter webhook process.

## Attributing requests to a pull request

When `add_user_to_requests` is enabled, PR-Agent sends the command and pull-request URL in the OpenAI-compatible `user` field:

```text
{"command":"improve","pr_url":"https://gitee.com/owner/repo/pulls/171"}
```

Providers that store this field can attribute cost to a pull request without matching timestamps. The setting is off by default because it shares the URL with the model provider.

```toml
[config]
add_user_to_requests = true
```

## Integrating with logging observability platforms

LiteLLM callbacks work when the default LiteLLM handler is in use. Configure them in `configuration.toml` and set the environment variables from the LiteLLM [documentation](https://docs.litellm.ai/docs/).

LangSmith example:

```toml
[litellm]
enable_callbacks = true
success_callback = ["langsmith"]
failure_callback = ["langsmith"]
service_callback = []
```

```bash
LANGSMITH_API_KEY=<api_key>
LANGSMITH_PROJECT=<project>
LANGSMITH_BASE_URL=<url>
```

Langfuse example (use `langfuse_otel`, not the legacy `langfuse` callback):

```toml
[litellm]
enable_callbacks = true
success_callback = ["langfuse_otel"]
failure_callback = ["langfuse_otel"]
```

```bash
LANGFUSE_HOST=https://cloud.langfuse.com
LANGFUSE_PUBLIC_KEY=<public_key>
LANGFUSE_SECRET_KEY=<secret_key>
```

Traces are tagged with the command, git provider (`gitee`), pull-request URL, model, token counts, and version.

### LLM telemetry via LiteLLM's OpenTelemetry integration {#llm-telemetry-via-litellms-opentelemetry-integration}

To emit OpenTelemetry traces and metrics for the model calls themselves, enable LiteLLM's `otel` callback:

```toml
[litellm]
success_callback = ["otel"]
failure_callback = ["otel"]
turn_off_message_logging = true
```

Set `turn_off_message_logging = true`. Otherwise LiteLLM can attach the prompt and the response, which here include the pull-request diff.

```bash
OTEL_EXPORTER=otlp_http
OTEL_EXPORTER_OTLP_ENDPOINT=https://collector:4318
OTEL_EXPORTER_OTLP_HEADERS=...
OTEL_SERVICE_NAME=pr-agent
LITELLM_OTEL_INTEGRATION_ENABLE_METRICS=true
```

Pending callbacks are flushed before the CLI exits, bounded by `callback_timeout_seconds` (see [Custom callbacks](#custom-callbacks)).

### Custom callbacks {#custom-callbacks}

If you embed PR-Agent, you can register a `litellm.CustomLogger`:

```python
import litellm
from pr_agent import cli

class UsageLogger(litellm.integrations.custom_logger.CustomLogger):
    async def async_log_success_event(self, kwargs, response_obj, start_time, end_time):
        record_usage(kwargs.get("model"), response_obj)

litellm.callbacks = [UsageLogger()]
cli.run_command("<pr_url>", "/review")
```

LiteLLM runs callbacks after the completion returns. PR-Agent flushes them before the CLI exits. Bound that wait with:

```toml
[litellm]
callback_timeout_seconds = 30 # default
```

## Built-in OpenTelemetry command telemetry

PR-Agent can emit its own command-level signals. These cover runs that fail before any model call:

- **Traces**: one span per request, named `pr_agent <command>`, with `pr_agent.command`, `pr_agent.args_count`, `vcs.provider.name`, a span status, and a bounded `error.type` on failure. Prompt and response bodies are not attached.
- **Metrics**: `pr_agent.commands`, `pr_agent.tokens`, and `pr_agent.ai_calls`, labeled by command and git provider. Token series also use `gen_ai.token.type`. Zero values are skipped.

Command telemetry and [LLM telemetry](#llm-telemetry-via-litellms-opentelemetry-integration) are separate switches. When both are on, model spans are children of the command span.

```toml
[otel]
is_enabled = true
exporter_type = "console" # "console", "otlp", "prometheus", or "none"
service_name = "pr-agent"
environment = "production"
```

For a collector, set `exporter_type = "otlp"` and put the endpoint in `.secrets.toml`:

```toml
[otel]
otlp_endpoint = "http://my-collector:4318"
otlp_headers = "x-honeycomb-team=YOUR_API_KEY"
```

HTTP is the default. `/v1/traces` and `/v1/metrics` are appended to `otlp_endpoint`. For gRPC, install `pr-agent[otel-grpc]` and set `otlp_protocol = "grpc"`.

If `exporter_type = "otlp"` and no endpoint is set, telemetry is disabled. It does not fall back to another exporter.

### Exposing Prometheus metrics

Set `exporter_type = "prometheus"` to serve `GET /metrics` on the `gitee_app` gunicorn process. Worker values are merged at scrape time:

```toml
[otel]
exporter_type = "prometheus"
prometheus_multiproc_dir = "/tmp/pr-agent-prometheus"
```

`/metrics` is mounted only when this exporter is selected. `prometheus_multiproc_dir` must be writable by every worker. In a single-process run the exporter serves that process's own registry without the directory.

```yaml
scrape_configs:
  - job_name: pr-agent
    static_configs:
      - targets: ["pr-agent:3000"]
```

Privacy controls, both off by default:

- `include_pr_url = true` puts pull-request URLs on spans.
- `include_error_details = true` puts exception messages on error spans. The exception class name is always attached.

Telemetry is process-level. It is read once at startup and cannot be enabled from a repository `.pr_agent.toml`. Each OTLP export is bounded by `otlp_timeout` (default 3 seconds).

## Repository context files {#bringing-per-repo-context-files-to-pr-agent}

PR-Agent can add repository instruction files, such as [AGENTS.md](https://agents.md/), to the prompts for `/review`, `/describe`, and `/improve`.

```toml
[config]
repo_context_files = ["AGENTS.md"]
```

Paths are repository-relative. By default they are read from the repository **default branch** (`repo_context_from_default_branch = true`), so a pull request cannot supply the instructions used to review it. A missing file is skipped. Set the list to `[]` to disable the feature.

Set `repo_context_from_default_branch = false` to read from the pull request's target branch instead. Files are still never read from the head branch.

`repo_context_max_lines` (default `500`) caps the rendered lines, including wrapper tags.

### Context from sibling repositories {#context-from-sibling-repositories}

The host must approve repositories before a consuming repository can select their files:

```toml
[config]
repo_context_sibling_repos = ["my-org/library"]
repo_context_max_sibling_files = 5
```

The allowlist and the fetch limit are host-only. An empty allowlist disables sibling reads. A consuming `.pr_agent.toml` may then use a structured entry:

```toml
[config]
repo_context_files = [
    "AGENTS.md",
    {repo_id = "my-org/library", file_path = "src/api.py"},
]
```

Use `owner/repository`. The sibling must share the current repository's owner. Sibling files come from their default branch and share `repo_context_max_lines`. Comment arguments cannot override `repo_context_files`.

## Ignoring automatic commands in pull requests {#ignoring-automatic-commands-in-prs}

PR-Agent can skip pull requests by:

- title (regex)
- source or target branch (regex)
- repository (regex)
- folders that did not change
- labels
- author

The title, author, label, repository, source-branch, and target-branch rules also apply to comment commands such as `/review` and `/ask`, and to CLI `--pr_url` runs. `ignore_pr_authors` matches the **pull request author**, not the person who posted the comment. An ignored CLI request exits successfully without running the tool.

### Titles

```toml
[config]
ignore_pr_title = ["\\[Bump\\]"]
```

The default is `["^\\[Auto\\]", "^Auto"]`. `^Auto` also matches ordinary titles such as "Autoscaling fix", and those pull requests are skipped for manual commands too. Narrow the pattern, or set `ignore_pr_title = []`, when that is not what you want.

### Branches

```toml
[config]
ignore_pr_source_branches = ['develop', 'main', 'master', 'stage']
ignore_pr_target_branches = ["qa"]
```

The two lists are independent. Each entry is a regex.

### Repositories

```toml
[config]
ignore_repositories = ["my-org/my-repo1", "my-org/my-repo2"]
```

### Folders

```toml
[config]
allow_only_specific_folders = ['folder1', 'folder2']
```

Automatic feedback then runs only when a changed path contains one of those folders.

### Labels

```toml
[config]
ignore_pr_labels = ["do-not-merge"]
```

### Authors

```toml
[config]
ignore_pr_authors = ["my-special-bot-user"]
```

Each entry is a regex matched against the author's username.

### Generated files by language or framework

```toml
[config]
ignore_language_framework = ['protobuf']
```

Patterns are listed in [`generated_code_ignore.toml`](https://github.com/the-pr-agent/pr-agent/blob/main/pr_agent/settings/generated_code_ignore.toml).

## Changelog output

Gitee cannot `push_code`. `/update_changelog` generates the changelog and publishes it as a pull-request comment even when `pr_update_changelog.push_changelog_changes` is true. No commit is created, and no Git host workflow file is required.
