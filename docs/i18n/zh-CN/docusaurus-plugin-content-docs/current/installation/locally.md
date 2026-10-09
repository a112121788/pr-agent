---
title: "本地运行"
sidebar_position: 3
---

要在本地运行 PR-Agent，你首先需要获取两把密钥：

本地执行使用下面的 Gitee 拉取请求示例。

1. 你所配置的[语言模型提供商](../usage-guide/changing_a_model.md)的 API 密钥。对于 OpenAI，可在<a href="https://platform.openai.com/api-keys" target="_blank" rel="noopener noreferrer">此处</a>创建。
2. 来自你的 Git 平台（GitHub、GitLab、BitBucket、Gitea）且具有 repo 范围的个人访问令牌。例如 GitHub 令牌可在<a href="https://github.com/settings/tokens" target="_blank" rel="noopener noreferrer">此处</a>签发

## 使用 Docker 镜像 {#using-docker-image}

相关工具列表见[工具指南](../tools/index.md)。

要调用某个工具（例如 `review`），可以直接从 Docker 镜像运行 PR-Agent。方法如下：

- 对于 GitHub：

    ```bash
    docker run --rm -it -e OPENAI__KEY=<your_openai_key> -e GITHUB__USER_TOKEN=<your_github_token> pragent/pr-agent:latest --pr_url <pr_url> review
    ```

    如果你使用 GitHub Enterprise Server，需要把自定义 URL 指定为变量。
    例如，如果你的 GitHub 服务器位于 `https://github.mycompany.com`，请在命令中加入：

    ```bash
    -e GITHUB__BASE_URL=https://github.mycompany.com/api/v3
    ```

- 对于 GitLab：

    ```bash
    docker run --rm -it -e OPENAI__KEY=<your key> -e CONFIG__GIT_PROVIDER=gitlab -e GITLAB__PERSONAL_ACCESS_TOKEN=<your token> pragent/pr-agent:latest --pr_url <pr_url> review
    ```

    如果你有专用的 GitLab 实例，需要把自定义 URL 指定为变量：

    ```bash
    -e GITLAB__URL=<your gitlab instance url>
    ```

- 对于 BitBucket：

    ```bash
    docker run --rm -it -e CONFIG__GIT_PROVIDER=bitbucket -e OPENAI__KEY=$OPENAI_API_KEY -e BITBUCKET__BEARER_TOKEN=$BITBUCKET_BEARER_TOKEN pragent/pr-agent:latest --pr_url=<pr_url> review
    ```

- 对于 Gitea：

    ```bash
    docker run --rm -it -e OPENAI__KEY=<your key> -e CONFIG__GIT_PROVIDER=gitea -e GITEA__PERSONAL_ACCESS_TOKEN=<your token> pragent/pr-agent:latest --pr_url <pr_url> review
    ```

    如果你有专用的 Gitea 实例，需要把自定义 URL 指定为变量：

    ```bash
    -e GITEA__URL=<your gitea instance url>
    ```


对于其他 Git 提供商，请相应更新 `CONFIG__GIT_PROVIDER`，并查看 [`pr_agent/settings/.secrets_template.toml`](https://github.com/the-pr-agent/pr-agent/blob/main/pr_agent/settings/.secrets_template.toml) 文件，了解环境变量的预期名称和取值。

### 使用环境变量

也可以通过设置对应的环境变量来提供或覆盖配置。
你可以按以下约定定义对应的环境变量：`<TABLE>__<KEY>=<VALUE>` 或 `<TABLE>.<KEY>=<VALUE>`。
`<TABLE>` 指配置文件中的表/小节，`<KEY>=<VALUE>` 指配置文件中某项设置的键/值对。

例如，假设你要运行连接到自托管 GitLab 实例的 `pr_agent`，类似上面的示例。
你可以在名为 `.env` 的纯文本文件中定义环境变量，内容如下：

```bash
CONFIG__GIT_PROVIDER="gitlab"
GITLAB__URL="<your url>"
GITLAB__PERSONAL_ACCESS_TOKEN="<your token>"
OPENAI__KEY="<your key>"
```

然后可以用以下命令通过 Docker 运行 `pr_agent`：

```shell
docker run --rm -it --env-file .env pragent/pr-agent:latest <tool> <tool parameter>
```

---

### 运行 Docker 镜像时出错。我该怎么办？

如果运行 Docker 镜像时遇到错误，几乎总是因为 API 密钥或令牌配置有误。

请注意，pr-agent 所使用的 litellm 有时会返回信息量不足的错误消息，例如 `APIError: OpenAIException - Connection error.`
请仔细检查你提供的 API 密钥和令牌，确保它们正确。
根据你的 LLM 提供商，可能需要做一些调整。

例如，对于 Azure OpenAI，还[需要](../usage-guide/changing_a_model.md#azure)额外的密钥。
其他提供商也是如此，请查看[文档](../usage-guide/changing_a_model.md#changing-a-model-in-pr-agent)

## 使用 pip 包

安装该包：

```bash
pip install "pr-agent[github]"
```

Git 提供商 SDK 是可选的 extra，因此请安装你所用提供商对应的那个：`github`、`gitlab`、`bitbucket`（Bitbucket Cloud、Bitbucket Server 和 Jira）、`azure`、`codecommit` 或 `gitea`。
`google` 会加入 Vertex AI，`pr-agent[all]` 会安装全部集成。

然后用下面的脚本运行相应工具。
<br>
请务必填入所需参数（`user_token`、`openai_key`、`pr_url`、`command`）：

```python
from pr_agent import cli
from pr_agent.config_loader import get_settings

def main():
    # Fill in the following values
    provider = "github" # github/gitlab/bitbucket/azure_devops
    user_token = "..."  #  user token
    openai_key = "..."  # OpenAI key
    pr_url = "..."      # PR URL, for example 'https://github.com/the-pr-agent/pr-agent/pull/809'
    command = "/review" # Command to run (e.g. '/review', '/describe', '/ask="What is the purpose of this PR?"', ...)

    # Setting the configurations
    get_settings().set("CONFIG.git_provider", provider)
    get_settings().set("openai.key", openai_key)
    get_settings().set("github.user_token", user_token)

    # Run the command. Feedback will appear in GitHub PR comments
    return cli.run_command(pr_url, command)


if __name__ == '__main__':
    raise SystemExit(main())
```

启用 `config.propagate_tool_errors` 后，通过 `SystemExit` 转发返回值会使此脚本在工具错误被传播后以状态码 1 退出。默认仍为状态码 0。

这个 Python 辅助函数接受带引号的参数，例如
`cli.run_command(pr_url, "/review --pr_reviewer.extra_instructions='be concise please'")`。
它使用与已配置的自动化命令相同的引号规则：显式
加引号的设置值保持为字符串，未加引号的值保留其正常
类型。对于包含撇号的问题，请用双引号包住
问题，例如 `command = '/ask "What\'s changed?"'`。
这不会改变交互式拉取请求评论的解析方式。

## 从源码运行 {#run-from-source}

1. 克隆此仓库：

```bash
git clone https://github.com/the-pr-agent/pr-agent.git
```

2. 进入 `/pr-agent` 文件夹，并用 [uv](https://docs.astral.sh/uv/) 安装依赖（根据 `uv.lock` 创建 `.venv`）：

```bash
uv sync
```

*注意：如果在安装依赖时出现与 Rust 相关的错误，请确保已安装 Rust 且它在你的 `PATH` 中，说明见：https://rustup.rs*

3. 复制密钥模板文件，并填入你的 OpenAI 密钥和 GitHub 用户令牌：

```bash
cp pr_agent/settings/.secrets_template.toml pr_agent/settings/.secrets.toml
chmod 600 pr_agent/settings/.secrets.toml
# Edit .secrets.toml file
```

4. 运行 cli.py 脚本：

```bash
uv run pr-agent --pr_url <pr_url> review
uv run pr-agent --pr_url <pr_url> ask "<your question>"
uv run pr-agent --pr_url <pr_url> describe
uv run pr-agent --pr_url <pr_url> improve
uv run pr-agent --pr_url <pr_url> add_docs
uv run pr-agent --pr_url <pr_url> generate_labels
uv run pr-agent --issue_url <issue_url> similar_issue
...
```

*注意：`similar_issue` 工具需要额外依赖，单纯的 `uv sync` 不会安装它们。运行前请用 `uv sync --group similar-issue` 安装。*

[可选] 把 pr_agent 文件夹加入你的 PYTHONPATH

```bash
export PYTHONPATH=$PYTHONPATH:<PATH to pr_agent folder>
```
