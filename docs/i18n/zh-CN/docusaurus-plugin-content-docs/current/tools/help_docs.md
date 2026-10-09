---
title: "文档帮助"
sidebar_position: 10
---

:::warning[`/help_docs` 当前已禁用]
自 **v0.36.1** 起，`/help_docs` 命令暂时禁用，作为凭证泄露漏洞的缓解措施（[#2445](https://github.com/The-PR-Agent/pr-agent/issues/2445)）：
该命令接受对 git 克隆目标的不可信运行时覆盖，而克隆 URL 的主机校验只检查子串包含关系，因此一个仅仅*包含*允许主机名的主机就可能收到 Git 提供方令牌。

该命令未在 `PRAgent` 中注册，因此在任何提供方上调用它都没有效果。
下面的页面记录的是重新启用后该工具的行为。
:::

## 概述

`help_docs` 工具可以根据 git 文档目录回答自由文本问题。

可以在任意拉取请求或议题上评论来手动调用：

```
/help_docs "..."
```

也可以配置为在[新议题打开时](../installation/gitee.md)自动触发。

工具默认假定文档位于仓库根目录的 `/docs` 文件夹。
不过可以通过 `docs_path` 配置选项自定义：

```toml
[pr_help_docs]
repo_url = ""                 # The repository to use as context
docs_path = "docs"            # The documentation folder
repo_default_branch = "main"  # The branch to use in case repo_url overwritten

```

更多配置选项见[配置选项](#configuration-options)一节。

## 使用示例

[//]: # (#### 询问关于本仓库的问题：)

[//]: # (<img src="/img/help_docs_comment.png" alt="help_docs on the documentation of this repository" width="512" />)

**询问关于另一个仓库的问题**

<img src="/img/help_docs_comment_explicit_git.png" alt="针对另一个仓库文档的 help_docs" width="512" />

**回复**：

<img src="/img/help_docs_response.png" alt="help_docs 回复" width="512" />

## 新议题打开时自动运行

可以把 PR-Agent 配置为在任何新建议题上自动运行 `help_docs`。
例如，对于文档丰富的开源项目，这可以给提出问题的用户立即反馈。

做法如下：

1) 按[作为 GitHub Action 运行](../installation/gitee.md)中的步骤创建新工作流，例如：`.github/workflows/help_docs.yml`：

2) 把 yaml 文件编辑为如下内容：

```yaml
name: Run pr agent on every opened issue, respond to user comments on an issue

#When the action is triggered
on:
  issues:
    types: [opened] #New issue

# Read env. variables
env:
  GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
  GITHUB_API_URL: ${{ github.api_url }}
  GIT_REPO_URL: ${{ github.event.repository.clone_url }}
  ISSUE_URL: ${{ github.event.issue.html_url || github.event.comment.html_url }}
  ISSUE_BODY: ${{ github.event.issue.body || github.event.comment.body }}
  OPENAI_KEY: ${{ secrets.OPENAI_KEY }}

# The actual set of actions
jobs:
  issue_agent:
    runs-on: ubuntu-latest
    if: ${{ github.event.sender.type != 'Bot' }} #Do not respond to bots

    # Set required permissions
    permissions:
      contents: read    # For reading repository contents
      issues: write     # For commenting on issues

    steps:
      - name: Run PR Agent on Issues
        if: ${{ env.ISSUE_URL != '' }}
        uses: docker://pragent/pr-agent:latest
        with:
          entrypoint: /bin/bash #Replace invoking cli.py directly with a shell
          args: |
            -c "cd /app && \
            echo 'Running Issue Agent action step on ISSUE_URL=$ISSUE_URL' && \
            export config__git_provider='github' && \
                        export github__user_token=$GITHUB_TOKEN && \
            export github__base_url=$GITHUB_API_URL && \
            export openai__key=$OPENAI_KEY && \
            python -m pr_agent.cli --issue_url=$ISSUE_URL --pr_help_docs.repo_url="..." --pr_help_docs.docs_path="..." --pr_help_docs.openai_key=$OPENAI_KEY && \
            help_docs "$ISSUE_BODY"
```

3) 完成其余步骤（例如添加密钥以及 `repo_url`、`docs_path` 等相关配置）后，把此变更合并到主分支。
当新议题打开时，如果问题与仓库文档相关，你应当会看到来自 `github-actions` 机器人的自动回复评论。

---

## 配置选项 {#configuration-options}

在 `pr_help_docs` 节下，[配置文件](https://github.com/the-pr-agent/pr-agent/blob/main/pr_agent/settings/configuration.toml)包含用于自定义 “help docs” 工具的选项：

- `repo_url`：如果未被覆盖，将使用上下文来源的仓库（议题或拉取请求）；否则使用给定仓库作为上下文。
- `repo_default_branch`：当 `repo_url` 被覆盖时要使用的分支；否则没有效果。
- `docs_path`：相对于仓库根目录的路径（该拉取请求所属仓库，或上面的仓库 URL）。
- `exclude_root_readme`：查询模型时是否排除根目录 README 文件。
- `supported_doc_exts`：为查询模型而应包含的文件扩展名。

---
