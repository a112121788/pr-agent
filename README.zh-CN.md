[English](README.md) | **中文**

<br />

<div align="center">

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/The-PR-Agent/pr-agent/main/docs/static/img/logo-dark.png" width="330">
  <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/The-PR-Agent/pr-agent/main/docs/static/img/logo-light.png" width="330">
  <img src="https://raw.githubusercontent.com/The-PR-Agent/pr-agent/main/docs/static/img/logo-light.png" alt="logo" width="330">

</picture>
<br>
开源 PR 审查工具的开创者
<br><br>
<a href="https://github.com/the-pr-agent/pr-agent/commits/main">
<img alt="GitHub" src="https://img.shields.io/github/last-commit/the-pr-agent/pr-agent/main?style=for-the-badge" height="20">
</a>
</div>

---

本仓库包含开源的 PR Agent 项目。
它不是 Qodo 面向开源项目的产品。

PR-Agent 是一个开源的、由 AI 驱动的代码审查 agent，也是 Qodo 社区维护的遗留项目。它不同于 Qodo 的主要 AI 代码审查产品，后者提供功能丰富、具备上下文感知能力的体验。Qodo 为开源项目提供免费版本，并与 GitHub、GitLab、Bitbucket 和 Azure DevOps 无缝集成，实现高质量的自动审查。

## 赞助商

PR-Agent 是一个由社区维护的开源项目，其持续开发由赞助商支持。如果你想支持本项目，可以考虑[成为赞助商](https://github.com/sponsors/naorpeled)。

<p align="center">
  <h3 align="center">🥇 金牌赞助商</h3>
</p>

<p align="center">
  <a target="_blank" href="https://www.qodo.ai/">
    <img alt="Qodo — Gold sponsor" src="https://www.qodo.ai/wp-content/uploads/2025/03/qodo-logo.svg" width="150">
  </a>
</p>

<p align="center">
  <a target="_blank" href="https://www.qodo.ai/solutions/open-source/">面向开源项目的 Qodo 免费版本</a>
</p>


## 目录

- [快速开始](#快速开始)
- [为什么选择 PR-Agent](#为什么选择-pr-agent)
- [功能特性](#功能特性)
- [实际效果](#实际效果)
- [工作原理](#工作原理)
- [数据隐私](#数据隐私)
- [贡献](#贡献)

## 快速开始

> [!NOTE]
> **Docker Hub 命名空间迁移。** `0.34.2` 及之后的版本发布在 [`pragent/pr-agent`](https://hub.docker.com/r/pragent/pr-agent)。更早的版本（到 `v0.31` 为止）仍保留在旧的 [`codiumai/pr-agent`](https://hub.docker.com/r/codiumai/pr-agent) 命名空间，作为冻结的存档 —— 不会再向那里推送新镜像。升级到 `0.34.2+` 时，请一并更新所有固定版本的 `image:` / `docker pull` / `uses: docker://` 引用。

### 🚀 PR-Agent 快速上手

#### 1. GitHub Action（推荐）

用一个简单的 workflow 文件为你的仓库添加自动化 PR 审查：

```yaml
# .github/workflows/pr-agent.yml
name: PR Agent
on:
  pull_request:
    types: [opened, synchronize]
jobs:
  pr_agent_job:
    runs-on: ubuntu-latest
    steps:
    - name: PR Agent action step
      uses: the-pr-agent/pr-agent@main
      env:
        OPENAI_KEY: ${{ secrets.OPENAI_KEY }}
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```
[完整的 GitHub Action 配置指南](https://docs.pr-agent.ai/installation/github/#run-as-a-github-action)

#### 2. CLI 用法（本地开发）

在你自己的仓库上本地运行 PR-Agent：

```bash
pip install "pr-agent[github]"
export OPENAI_KEY=your_key_here
pr-agent --pr_url https://github.com/owner/repo/pull/123 review
```
各 Git 平台的 SDK 是可选的 extra：安装你所使用平台对应的那个（[列表](https://docs.pr-agent.ai/installation/locally/#using-pip-package)），或用 `pr-agent[all]` 安装全部集成。
[完整的 CLI 配置指南](https://docs.pr-agent.ai/usage-guide/automations_and_usage/#local-repo-cli)

#### 3. 其他平台

- [GitLab webhook 配置](https://docs.pr-agent.ai/installation/gitlab/)
- [BitBucket 应用安装](https://docs.pr-agent.ai/installation/bitbucket/)
- [Azure DevOps 配置](https://docs.pr-agent.ai/installation/azure/)

## 新闻与更新

每个版本的完整说明见 [Releases 页面](https://github.com/the-pr-agent/pr-agent/releases)。


## 为什么选择 PR-Agent

### 🎯 为真实开发团队打造

**快速且低成本**：每个工具（`/review`、`/improve`、`/ask`）只调用一次 LLM（约 30 秒，成本低）

**能处理任意大小的 PR**：我们的 [PR 压缩策略](https://docs.pr-agent.ai/core-abilities/compression_strategy/) 能有效处理小 PR 和大 PR

**高度可定制**：基于 JSON 的提示词让你可以通过[配置文件](pr_agent/settings/configuration.toml)轻松定制审查类别和行为

**平台无关**：
- **Git 平台**：GitHub、GitLab、BitBucket、Azure DevOps、Gitea
- **部署方式**：CLI、GitHub Actions、Docker、自托管、webhook
- **AI 模型**：OpenAI GPT、Anthropic Claude、Google Gemini、DeepSeek、Mistral，以及任何可通过 LiteLLM 访问的模型（Azure OpenAI、AWS Bedrock、Vertex AI、Databricks、OpenRouter、Ollama 等）—— 见[更换模型](https://docs.pr-agent.ai/usage-guide/changing_a_model/)

**开源带来的好处**：
- 完全掌控你的数据和基础设施
- 为团队需求定制提示词和行为
- 不被厂商锁定
- 由社区驱动开发

## 功能特性

<div style="text-align:left;">

在 PR-Agent 文档中查看当前的[功能与 Git 平台支持矩阵](https://docs.pr-agent.ai/overview/supported_platforms/)。

⚠️ 自 `v0.36.1` 起，`/help_docs` 因凭据泄露问题（[#2445](https://github.com/the-pr-agent/pr-agent/issues/2445)）等待修复，暂时禁用。

[//]: # (- Support for additional git providers is described in [here]&#40;./docs/Full_environments.md&#41;)
___

## 实际效果

</div>
<h4><a href="https://github.com/the-pr-agent/pr-agent/pull/530">/describe</a></h4>
<div align="center">
<p float="center">
<img src="https://raw.githubusercontent.com/The-PR-Agent/pr-agent/main/docs/static/img/describe_new_short_main.png" width="512">
</p>
</div>
<hr>

<h4><a href="https://github.com/the-pr-agent/pr-agent/pull/732#issuecomment-1975099151">/review</a></h4>
<div align="center">
<p float="center">
<kbd>
<img src="https://raw.githubusercontent.com/The-PR-Agent/pr-agent/main/docs/static/img/review_new_short_main.png" width="512">
</kbd>
</p>
</div>
<hr>

<h4><a href="https://github.com/the-pr-agent/pr-agent/pull/732#issuecomment-1975099159">/improve</a></h4>
<div align="center">
<p float="center">
<kbd>
<img src="https://raw.githubusercontent.com/The-PR-Agent/pr-agent/main/docs/static/img/improve_new_short_main.png" width="512">
</kbd>
</p>
</div>

<hr>

### 用法示例

PR-Agent 的工具以 PR 评论或 CLI 的形式运行。以下是一些常见用法：

```bash
# 在 PR 上评论（GitHub/GitLab/Bitbucket/…）：
/describe
/review
/improve
/ask "What does this PR change?" # 针对 PR 的自由文本问答

# issue 级命令在 issue 上运行，而不是 PR：
/similar_issue # 在仓库中查找相似 issue

# 或者通过 CLI 在本地运行：
pr-agent --pr_url <PR_URL> review
pr-agent --issue_url <ISSUE_URL> similar_issue
```

完整工具列表和示例命令见[工具文档](https://docs.pr-agent.ai/tools/#usage-examples)，每个工具的页面里还有截图和选项说明。

<hr>

## 工作原理

下图展示了 PR-Agent 的工具及其流程：

![PR-Agent Tools](https://raw.githubusercontent.com/The-PR-Agent/pr-agent/main/docs/static/img/diagram-v0.9.png)

## 数据隐私

### 自托管 PR-Agent

- 如果你用自己的 OpenAI API key 托管 PR-Agent，数据只在你和 OpenAI 之间。你可以在下面阅读他们的 API 数据隐私政策：
https://openai.com/enterprise-privacy

## 贡献

想为本项目做贡献，请先阅读我们的[贡献指南](https://github.com/the-pr-agent/pr-agent/blob/main/CONTRIBUTING.md)。

本地验证时，在仓库根目录运行 `PYTHONPATH=. uv run pytest`；它默认会发现 `tests/unittest` 下的单元测试。`tests/e2e_tests` 下的端到端测试需要各平台的凭据，应显式调用，例如 `PYTHONPATH=. uv run pytest tests/e2e_tests/test_github_app.py`。


## PR-Agent 的重磅消息

PR-Agent 有了新家！

在与社区一起打造这个工具多年之后，Qodo 已将 PR-Agent 捐赠给开源社区 —— 我们对接下来会发生的事情无比期待。

项目现在位于 GitHub 上的 PR-Agent 组织下，完全由社区所有，并欢迎更多贡献和维护者。

其他变化：
- 文档已迁移至 - [docs.pr-agent.ai](https://docs.pr-agent.ai/)
- Qodo Merge（Qodo 1.0），也就是 PR-Agent 企业版的托管站点，已更名为 Qodo（Qodo 2.0），并演进为一个完整的 AI 代码审查平台。

## ❤️ 社区

这个开源版本作为 Qodo 的社区贡献留在这里 —— 它是现代 AI 驱动代码协作的起点。我们很自豪能分享它，并启发全球的开发者。

项目现在有了第一位外部维护者 Naor（[@naorpeled](https://github.com/naorpeled)），目前正在被捐赠给一个开源基金会。
