---
title: "本地运行"
sidebar_position: 3
---

本地运行 Gitee PR-Agent 需要三项信息：

1. [语言模型](../usage-guide/changing_a_model.md)的 API 密钥。
2. OpenAI 兼容接口地址，通常以 `/v1` 结尾。
3. Gitee 个人访问令牌，可在 <a href="https://gitee.com/personal_access_tokens" target="_blank" rel="noopener noreferrer">Gitee 个人访问令牌</a>页面创建。

## 使用 Docker 镜像 {#using-docker-image}

相关工具见[工具指南](../tools/index.md)。审查一张 Gitee 拉取请求：

```bash
docker run --rm -it \
  -e OPENAI__KEY=<模型密钥> \
  -e OPENAI__API_BASE=<模型地址> \
  -e CONFIG__GIT_PROVIDER=gitee \
  -e GITEE__PERSONAL_ACCESS_TOKEN=<Gitee 令牌> \
  ecloud-tcr.tencentcloudcr.com/ecloud_project/pr-agent:latest \
  --pr_url https://gitee.com/owner/repo/pulls/7 review
```

企业版地址使用 `https://e.gitee.com/<企业名>/repos/owner/repo/pulls/7`。把最后的 `review` 换成 `describe`、`improve`、`ask`、`add_docs` 或 `generate_labels`，即可运行对应工具。

### 使用环境变量

也可以通过设置对应的环境变量来提供或覆盖配置。
你可以按以下约定定义对应的环境变量：`<TABLE>__<KEY>=<VALUE>` 或 `<TABLE>.<KEY>=<VALUE>`。
`<TABLE>` 指配置文件中的表/小节，`<KEY>=<VALUE>` 指配置文件中某项设置的键/值对。

例如，把 Gitee 审查所需的变量写入 `.env`：

```bash
CONFIG__GIT_PROVIDER=gitee
GITEE__PERSONAL_ACCESS_TOKEN=<Gitee 令牌>
OPENAI__KEY=<模型密钥>
OPENAI__API_BASE=<模型地址>
```

然后运行：

```shell
docker run --rm -it --env-file .env \
  ecloud-tcr.tencentcloudcr.com/ecloud_project/pr-agent:latest \
  --pr_url https://gitee.com/owner/repo/pulls/7 review
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
pip install gitee-pr-agent
```

Gitee 使用标准库和已有依赖，不需要额外的 Git 平台 SDK。`google` 会加入 Vertex AI。

然后用下面的脚本运行相应工具。
<br>
请务必填入所需参数（`user_token`、`openai_key`、`pr_url`、`command`）：

```python
from pr_agent import cli
from pr_agent.config_loader import get_settings

def main():
    # Fill in the following values
    user_token = "..."  # Gitee personal access token
    openai_key = "..."  # model key
    api_base = "..."    # OpenAI-compatible API base
    pr_url = "..."      # for example 'https://gitee.com/owner/repo/pulls/7'
    command = "/review" # '/review', '/describe', '/improve', ...

    # Setting the configurations
    get_settings().set("CONFIG.git_provider", "gitee")
    get_settings().set("openai.key", openai_key)
    get_settings().set("openai.api_base", api_base)
    get_settings().set("gitee.personal_access_token", user_token)

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

3. 复制密钥模板，填入模型密钥、模型地址和 Gitee 令牌：

```bash
cp pr_agent/settings/.secrets_template.toml pr_agent/settings/.secrets.toml
chmod 600 pr_agent/settings/.secrets.toml
# Edit .secrets.toml file
```

4. 运行 cli.py 脚本：

```bash
uv run gitee-pr-agent --pr_url <Gitee PR 地址> review
uv run gitee-pr-agent --pr_url <Gitee PR 地址> ask "<你的问题>"
uv run gitee-pr-agent --pr_url <Gitee PR 地址> describe
uv run gitee-pr-agent --pr_url <Gitee PR 地址> improve
uv run gitee-pr-agent --pr_url <Gitee PR 地址> add_docs
uv run gitee-pr-agent --pr_url <Gitee PR 地址> generate_labels
...
```

*注意：`similar_issue` 工具需要额外依赖，单纯的 `uv sync` 不会安装它们。运行前请用 `uv sync --group similar-issue` 安装。*

[可选] 把 pr_agent 文件夹加入你的 PYTHONPATH

```bash
export PYTHONPATH=$PYTHONPATH:<PATH to pr_agent folder>
```
