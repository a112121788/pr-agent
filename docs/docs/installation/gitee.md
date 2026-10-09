---
title: "Gitee Integration"
sidebar_position: 9
---

## Run a Gitee webhook server

1. Create a Gitee user that can read the target repository and comment on its pull requests. Give it permission to edit pull-request descriptions and labels when you want `/describe` and `/generate_labels` to publish those changes.

2. Create a personal access token for that user. Gitee sends this token as the `access_token` query parameter, so keep it in the host secrets rather than in a repository settings file.

3. Generate the webhook secret:

    ```bash
    WEBHOOK_SECRET=$(python -c "import secrets; print(secrets.token_hex(32))")
    ```

    `GITEE.WEBHOOK_SECRET` is required. When it is empty, the server rejects every webhook with HTTP 403.

4. Clone this repository:

    ```bash
    git clone https://github.com/the-pr-agent/pr-agent.git
    ```

5. Configure the host secrets:

    - Set `config.git_provider` to `gitee`.
    - Set the AI model credentials in their provider section.
    - In the `[gitee]` section, set `personal_access_token` from step 2 and `webhook_secret` from step 3.

    A repository's `.pr_agent.toml` cannot override `api_base`, `webhook_secret`, `skip_ssl_verification`, or `ssl_ca_cert`.

6. Build the webhook image:

    ```bash
    docker build . -t pr-agent:gitee_app --target gitee_app -f docker/Dockerfile
    ```

7. Provide the runtime configuration:

    ```bash
    CONFIG__GIT_PROVIDER=gitee
    GITEE__PERSONAL_ACCESS_TOKEN=<personal_access_token>
    GITEE__WEBHOOK_SECRET=<webhook_secret>
    GITEE__URL=https://gitee.com
    OPENAI__KEY=<your_openai_api_key>
    ```

    Use `GITEE__API_BASE` only when a proxy exposes the same Gitee OpenAPI v5. Set `GITEE__SKIP_SSL_VERIFICATION=true` only for a trusted private endpoint.

8. In the Gitee repository, add a webhook:

    - URL: `https://<PR_AGENT_HOSTNAME>/api/v1/gitee_webhooks`
    - Secret: the value from step 3
    - Events: Pull Request and comments

    PR-Agent checks `X-Gitee-Timestamp` and `X-Gitee-Token` before parsing the JSON body. The signature is HMAC-SHA256 over `<timestamp>\n<secret>`, encoded as Base64, and timestamps older than one hour are rejected.

9. Open a pull request or comment `/review` on one. An opened pull request runs `/describe`, `/review`, and `/improve`. A comment runs only when it starts with `/`.

10. The server uses the shared gunicorn configuration. See [Sizing a self-hosted webhook server](./index.md#sizing-a-self-hosted-webhook-server) before applying a memory limit.

## Verified behavior

The Gitee provider reads pull-request metadata, commits, changed files, and comments. It publishes descriptions, comments, and existing labels. Inline comments use Gitee's diff `position`, counted from the line below the first `@@` hunk header.

The webhook routes `merge_request_hooks` for an opened pull request and `note_hooks` for a pull-request comment. Push events do not trigger commands yet.

## Incomplete pull-request files

PR-Agent stops a command when Gitee cannot return a complete changed-file list. With `CONFIG.PUBLISH_OUTPUT` enabled, it tries to post a **PR-Agent command was not run** notice. Retry the command and inspect the changed files in Gitee if the notice persists.
