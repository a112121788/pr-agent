---
title: "GitHub 集成"
sidebar_position: 4
---

本页介绍如何把 PR-Agent 安装并运行为 GitHub Action 或 GitHub App，以及如何按你的需要配置它。

## 作为 GitHub Action 运行 {#run-as-a-github-action}

你可以使用我们预构建的 GitHub Action Docker 镜像，把 PR-Agent 作为 GitHub Action 运行。

1) 在仓库中添加以下文件，路径为 `.github/workflows/pr_agent.yml`：

```yaml
on:
  pull_request:
    types: [opened, reopened, ready_for_review, synchronize]
  issue_comment:
jobs:
  pr_agent_job:
    if: ${{ github.event.sender.type != 'Bot' }}
    runs-on: ubuntu-latest
    permissions:
      contents: read
      issues: write
      pull-requests: write
    name: Run pr agent on every pull request, respond to user comments
    steps:
      - name: PR Agent action step
        id: pragent
        uses: the-pr-agent/pr-agent@main
        env:
          OPENAI_KEY: ${{ secrets.OPENAI_KEY }}
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

2) 在仓库的 `Settings > Secrets and variables > Actions > New repository secret > Add secret` 下添加以下密钥：

```
Name = OPENAI_KEY
Secret = <your key>
```

GITHUB_TOKEN 密钥由 GitHub 自动创建。

3) 把此变更合并到你的主分支。
当你打开下一个拉取请求时，应该会看到来自 `github-actions` 机器人的评论，其中包含对该拉取请求的审查，以及如何使用其余工具的说明。

4) 你可以通过在 env 小节下添加环境变量来配置 PR-Agent，这些变量对应[配置](https://github.com/the-pr-agent/pr-agent/blob/main/pr_agent/settings/configuration.toml)文件中的任何可配置属性。一些示例：

```yaml
      env:
        # ... previous environment values
        OPENAI.ORG: "<Your organization name under your OpenAI account>"
        PR_REVIEWER.REQUIRE_TESTS_REVIEW: "false" # Disable tests review
        PR_CODE_SUGGESTIONS.NUM_CODE_SUGGESTIONS_PER_CHUNK: 6 # Increase number of code suggestions
```

详细用法见[使用指南](../usage-guide/automations_and_usage.md#github-action)

#### 配合 pull_request_target 使用（支持 fork / 外部贡献） {#using-with-pull_request_target-forkcontribution-support}

默认情况下，当拉取请求来自 fork 仓库时，`pull_request` 事件无法访问仓库或组织密钥，这意味着 PR-Agent 将无法访问 `OPENAI_KEY` 等密钥。工作流仍会收到 `GITHUB_TOKEN`，但默认情况下它对来自 fork 的拉取请求只有只读权限。对于私有仓库，管理员可以启用 **Send secrets to workflows from pull requests**，使密钥可用，但这样做会把这些密钥暴露给由 fork 拉取请求触发的工作流。

要支持来自外部贡献者（fork）的拉取请求，请改用 `pull_request_target` 事件。该事件在基础仓库的上下文中运行，可以访问其密钥和 `GITHUB_TOKEN` 权限。PR-Agent 使用 GitHub API 获取拉取请求数据，不需要在本地检出拉取请求代码。

```yaml
name: PR Agent
on:
  pull_request_target:
    types: [opened, reopened, synchronize, ready_for_review, review_requested]
  issue_comment:
jobs:
  pr_agent_job:
    if: ${{ github.event.sender.type != 'Bot' && (github.event_name == 'pull_request_target' || github.event.issue.pull_request) }}
    runs-on: ubuntu-latest
    permissions:
      contents: read
      issues: write
      pull-requests: write
    steps:
      - name: PR Agent action step
        uses: the-pr-agent/pr-agent@main
        env:
          OPENAI_KEY: ${{ secrets.OPENAI_KEY }}
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          github_action_config.pr_actions: '["opened", "reopened", "synchronize", "ready_for_review", "review_requested"]'
```

:::tip[无需本地检出]
PR-Agent 使用 GitHub API，直接从事件载荷获取拉取请求数据——它不需要在本地检出拉取请求代码。因此你可以安全地完全省略 `actions/checkout` 步骤，避免 `pull_request_target` 的常见陷阱，例如 `issue_comment` 事件没有 `pull_request.head.sha` 引用。
:::

:::warning[安全注意事项]
使用 `pull_request_target` 会使工作流能够访问仓库密钥。两种事件本身都不会检出代码，但在 `pull_request_target` 下，普通的 `actions/checkout` 获取的是默认分支而不是该拉取请求，这是一项安全特性。仅检出拉取请求头本身并不会执行不受信任的代码，但不要在同一作业中、在持有密钥或提升后的令牌权限时构建、测试、安装或以其他方式执行这些内容。如果需要本地文件，请在检出拉取请求头之前阅读 [关于 pull_request_target 的 GitHub 安全指南](https://docs.github.com/en/actions/reference/security/securely-using-pull_request_target)。
:::

### 配置示例 {#configuration-examples}

本节提供详细的分步示例，说明如何在 GitHub Actions 中用不同模型和高级选项配置 PR-Agent。

#### 快速开始示例

##### 基本设置（默认 OpenAI）

复制此最小工作流，即可使用默认的 OpenAI 模型开始：

```yaml
name: PR Agent
on:
  pull_request:
    types: [opened, reopened, ready_for_review]
  issue_comment:
jobs:
  pr_agent_job:
    if: ${{ github.event.sender.type != 'Bot' }}
    runs-on: ubuntu-latest
    permissions:
      contents: read
      issues: write
      pull-requests: write
    steps:
      - name: PR Agent action step
        uses: the-pr-agent/pr-agent@main
        env:
          OPENAI_KEY: ${{ secrets.OPENAI_KEY }}
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

##### Gemini 设置

可直接使用的 Gemini 模型工作流：

```yaml
name: PR Agent (Gemini)
on:
  pull_request:
    types: [opened, reopened, ready_for_review]
  issue_comment:
jobs:
  pr_agent_job:
    if: ${{ github.event.sender.type != 'Bot' }}
    runs-on: ubuntu-latest
    permissions:
      contents: read
      issues: write
      pull-requests: write
    steps:
      - name: PR Agent action step
        uses: the-pr-agent/pr-agent@main
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          config.model: "gemini/gemini-3.8-flash"
          config.fallback_models: '["gemini/gemini-3.8-flash"]'
          GOOGLE_AI_STUDIO.GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
          github_action_config.auto_review: "true"
          github_action_config.auto_describe: "true"
          github_action_config.auto_improve: "true"
```

#### Claude 设置

可直接使用的 Claude 模型工作流：

```yaml
name: PR Agent (Claude)
on:
  pull_request:
    types: [opened, reopened, ready_for_review]
  issue_comment:
jobs:
  pr_agent_job:
    if: ${{ github.event.sender.type != 'Bot' }}
    runs-on: ubuntu-latest
    permissions:
      contents: read
      issues: write
      pull-requests: write
    steps:
      - name: PR Agent action step
        uses: the-pr-agent/pr-agent@main
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          config.model: "anthropic/claude-opus-5"
          config.fallback_models: '["anthropic/claude-haiku-4-5-20251001"]'
          ANTHROPIC.KEY: ${{ secrets.ANTHROPIC_KEY }}
          github_action_config.auto_review: "true"
          github_action_config.auto_describe: "true"
          github_action_config.auto_improve: "true"
```

#### 带工具控制的基本配置

从这个包含工具配置的增强工作流开始：

```yaml
on:
  pull_request:
    types: [opened, reopened, ready_for_review]
  issue_comment:
jobs:
  pr_agent_job:
    if: ${{ github.event.sender.type != 'Bot' }}
    runs-on: ubuntu-latest
    permissions:
      contents: read
      issues: write
      pull-requests: write
    name: Run pr agent on every pull request, respond to user comments
    steps:
      - name: PR Agent action step
        id: pragent
        uses: the-pr-agent/pr-agent@main
        env:
          OPENAI_KEY: ${{ secrets.OPENAI_KEY }}
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          # Enable/disable automatic tools
          github_action_config.auto_review: "true"
          github_action_config.auto_describe: "true"
          github_action_config.auto_improve: "true"
          # Configure which PR events trigger the action
          github_action_config.pr_actions: '["opened", "reopened", "ready_for_review", "review_requested"]'
```

#### 切换模型

##### 使用 Gemini（Google AI Studio）

要使用 Gemini 模型代替默认的 OpenAI 模型：

```yaml
      env:
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        # Set the model to Gemini
        config.model: "gemini/gemini-3.8-flash"
        config.fallback_models: '["gemini/gemini-3.8-flash"]'
        # Add your Gemini API key
        GOOGLE_AI_STUDIO.GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
        # Tool configuration
        github_action_config.auto_review: "true"
        github_action_config.auto_describe: "true"
        github_action_config.auto_improve: "true"
```

**必需的密钥：**

- 把 `GEMINI_API_KEY` 添加到仓库密钥（从 [Google AI Studio](https://aistudio.google.com/) 获取）

**注意：** 使用 Gemini 这类非 OpenAI 模型时，不需要设置 `OPENAI_KEY`——只需要该模型专用的 API 密钥。

##### 使用 Claude（Anthropic）

要使用 Claude 模型：

```yaml
      env:
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        # Set the model to Claude
        config.model: "anthropic/claude-opus-5"
        config.fallback_models: '["anthropic/claude-haiku-4-5-20251001"]'
        # Add your Anthropic API key
        ANTHROPIC.KEY: ${{ secrets.ANTHROPIC_KEY }}
        # Tool configuration
        github_action_config.auto_review: "true"
        github_action_config.auto_describe: "true"
        github_action_config.auto_improve: "true"
```

**必需的密钥：**

- 把 `ANTHROPIC_KEY` 添加到仓库密钥（从 [Anthropic Console](https://console.anthropic.com/) 获取）

**注意：** 使用 Claude 这类非 OpenAI 模型时，不需要设置 `OPENAI_KEY`——只需要该模型专用的 API 密钥。

##### 使用 Azure OpenAI

要使用 Azure OpenAI 服务：

```yaml
      env:
        OPENAI_KEY: ${{ secrets.AZURE_OPENAI_KEY }}
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        # Azure OpenAI configuration
        OPENAI.API_TYPE: "azure"
        OPENAI.API_VERSION: "2023-05-15"
        OPENAI.API_BASE: ${{ secrets.AZURE_OPENAI_ENDPOINT }}
        OPENAI.DEPLOYMENT_ID: ${{ secrets.AZURE_OPENAI_DEPLOYMENT }}
        # Set the model to match your Azure deployment
        config.model: "gpt-4o"
        config.fallback_models: '["gpt-4o"]'
        # Tool configuration
        github_action_config.auto_review: "true"
        github_action_config.auto_describe: "true"
        github_action_config.auto_improve: "true"
```

**必需的密钥：**

- `AZURE_OPENAI_KEY`：你的 Azure OpenAI API 密钥
- `AZURE_OPENAI_ENDPOINT`：你的 Azure OpenAI 端点 URL
- `AZURE_OPENAI_DEPLOYMENT`：你的部署名称

##### 使用本地模型（Ollama）

要通过 Ollama 使用本地模型：

```yaml
      env:
        OPENAI_KEY: ${{ secrets.OPENAI_KEY }}
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        # Set the model to a local Ollama model
        config.model: "ollama/qwen2.5-coder:32b"
        config.fallback_models: '["ollama/qwen2.5-coder:32b"]'
        config.custom_model_max_tokens: "128000"
        # Ollama configuration
        OLLAMA.API_BASE: "http://localhost:11434"
        # Tool configuration
        github_action_config.auto_review: "true"
        github_action_config.auto_describe: "true"
        github_action_config.auto_improve: "true"
```

**注意：** 对于本地模型，你需要使用已安装 Ollama 的自托管运行器，因为 GitHub Actions 托管运行器无法访问 localhost 服务。

##### 使用 Amazon Bedrock

要使用带静态 IAM 凭据的 Amazon Bedrock 模型：

```yaml
      env:
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        config.model: "bedrock/anthropic.claude-3-5-sonnet-20240620-v1:0"
        config.fallback_models: '["bedrock/anthropic.claude-3-5-sonnet-20240620-v1:0"]'
        aws.AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
        aws.AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        aws.AWS_REGION_NAME: "us-east-1"
```

**推荐：在 AWS 计算资源上使用 IAM 角色凭据**

当 GitHub Actions 运行器位于 AWS 基础设施（EC2、ECS、EKS）上时，直接使用实例/任务 IAM 角色——无需密钥：

```yaml
      env:
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        config.model: "bedrock/anthropic.claude-3-5-sonnet-20240620-v1:0"
        config.fallback_models: '["bedrock/anthropic.claude-3-5-sonnet-20240620-v1:0"]'
        AWS_USE_IMDS: "true"
        # AWS_REGION_NAME: us-east-1  # optional if instance metadata provides the region
```

IAM 角色必须对目标模型 ARN 拥有 `bedrock:InvokeModel`。完整的 IAM 策略示例和支持的模型见 [Bedrock 模型配置](../usage-guide/changing_a_model.md#amazon-bedrock)。

要通过 VPC 接口端点路由调用，请在上述凭据旁添加 `AWS_BEDROCK_RUNTIME_ENDPOINT`：

```yaml
      env:
        AWS_BEDROCK_RUNTIME_ENDPOINT: "https://bedrock-runtime.us-east-1.amazonaws.com"
```

#### 高级配置选项

##### 自定义审查说明

为审查过程添加具体说明：

```yaml
      env:
        OPENAI_KEY: ${{ secrets.OPENAI_KEY }}
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        # Custom review instructions
        pr_reviewer.extra_instructions: "Focus on security vulnerabilities and performance issues. Check for proper error handling."
        # Tool configuration
        github_action_config.auto_review: "true"
        github_action_config.auto_describe: "true"
        github_action_config.auto_improve: "true"
```

##### 针对特定语言的配置

为特定编程语言进行配置：

```yaml
      env:
        OPENAI_KEY: ${{ secrets.OPENAI_KEY }}
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        # Language-specific settings
        pr_reviewer.extra_instructions: "Focus on Python best practices, type hints, and docstrings."
        pr_code_suggestions.num_code_suggestions_per_chunk: "8"
        pr_code_suggestions.suggestions_score_threshold: "7"
        # Tool configuration
        github_action_config.auto_review: "true"
        github_action_config.auto_describe: "true"
        github_action_config.auto_improve: "true"
```

##### 选择性执行工具

只自动运行特定工具：

```yaml
      env:
        OPENAI_KEY: ${{ secrets.OPENAI_KEY }}
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        # Only run review and describe, skip improve
        github_action_config.auto_review: "true"
        github_action_config.auto_describe: "true"
        github_action_config.auto_improve: "false"
        # Only trigger on PR open and reopen
        github_action_config.pr_actions: '["opened", "reopened"]'
```

##### CI 产物上下文 {#ci-artifact-context}

先前 CI 步骤产生的文件——测试报告、覆盖率摘要、linter 或 SAST 输出——可以注入到 `/review`、`/describe` 和 `/improve` 的提示中，这样模型在审查拉取请求时就能带上你流水线自己的发现。

用 `artifact_path` 输入指向该文件。路径相对于 `GITHUB_WORKSPACE` 解析（绝对路径也可以），因此 PR-Agent 运行时该文件必须已经存在于工作区——在前一个步骤中生成它，或用 `actions/download-artifact` 下载：

```yaml
    steps:
      - uses: actions/checkout@v4
      - name: Run tests
        run: pytest --junitxml=reports/pytest.xml || true
      - name: PR Agent action step
        uses: the-pr-agent/pr-agent@main
        env:
          OPENAI_KEY: ${{ secrets.OPENAI_KEY }}
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        with:
          artifact_path: reports/pytest.xml
          artifact_instructions: "These are the failing tests from this PR's CI run. Call out any suggestion that would not fix them."
```

设置 `artifact_path` 本身就会开启该功能；工作流中没有单独的启用开关需要拨动。受支持的目标工具会在其提示中收到一个专用的产物小节。标签和文件内容被明确标记为不受信任的数据，而 `artifact_instructions` 则单独作为从属的分析指导出现。受支持的目标是 `pr_reviewer`、`pr_description` 和 `pr_code_suggestions`；不受支持的名称会被跳过并给出警告。

覆盖某个受支持工具的提示时，请把 `artifact_context.instructions` 留在系统提示中，并在
用户提示里一个明确标记、不受信任的小节中渲染
`artifact_context.label`、`artifact_context.content`、`artifact_context.start_marker` 和 `artifact_context.end_marker`。这取代了 CI
产物原先通过 `extra_instructions` 实现的行为。

其余旋钮位于配置的 `[artifacts]` 小节：

```toml
[artifacts]
enable = false                                              # auto-enabled when artifact_path is set
artifact_path = ""                                          # relative to GITHUB_WORKSPACE, or absolute
artifact_instructions = ""                                  # empty = a generic "treat this as CI context" instruction
artifact_label = ""                                         # empty = the file's name
target_tools = ["pr_reviewer", "pr_description", "pr_code_suggestions"]
max_artifact_size = 50000                                   # characters; longer files are truncated with a marker
```

:::note
解析到 `GITHUB_WORKSPACE` 之外的路径会被拒绝，缺失或不可读的文件会被跳过并给出警告——这两种情况下工具仍会运行，只是没有产物上下文。
:::

当 PR-Agent 作为 CLI 从另一套 CI 系统运行、并在作业环境中设置了 `ARTIFACT_PATH` 时，同样的设置也适用；见 [GitLab 流水线示例](./gitlab.md#ci-artifact-context)。

#### 使用配置文件

除了通过环境变量设置全部选项，你也可以在仓库根目录使用 `.pr_agent.toml` 文件：

1. 在仓库根目录创建 `.pr_agent.toml` 文件：

```toml
[config]
model = "gemini/gemini-3.8-flash"
fallback_models = ["anthropic/claude-opus-5"]

[pr_reviewer]
extra_instructions = "Focus on security issues and code quality."

[pr_code_suggestions]
num_code_suggestions_per_chunk = 6
suggestions_score_threshold = 7
```

2. 使用更简单的工作流文件：

```yaml
on:
  pull_request:
    types: [opened, reopened, ready_for_review]
  issue_comment:
jobs:
  pr_agent_job:
    if: ${{ github.event.sender.type != 'Bot' }}
    runs-on: ubuntu-latest
    permissions:
      contents: read
      issues: write
      pull-requests: write
    name: Run pr agent on every pull request, respond to user comments
    steps:
      - name: PR Agent action step
        id: pragent
        uses: the-pr-agent/pr-agent@main
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          GOOGLE_AI_STUDIO.GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
          ANTHROPIC.KEY: ${{ secrets.ANTHROPIC_KEY }}
          github_action_config.auto_review: "true"
          github_action_config.auto_describe: "true"
          github_action_config.auto_improve: "true"
```

#### 排查常见问题

##### 找不到模型的错误

如果出现找不到模型的错误：

1. **检查模型名称格式**：确保使用正确的模型标识格式（例如 `gemini/gemini-3.8-flash`，而不是仅仅 `gemini-3.8-flash`）

2. **核对 API 密钥**：确保 API 密钥已正确设置为仓库密钥

3. **检查模型可用性**：有些模型可能并非在所有区域都可用，或可能需要特定访问权限

##### 环境变量格式

请记住关于环境变量的这些要点：

- 用点（`.`）或双下划线（`__`）分隔小节和键
- 布尔值应为字符串：`"true"` 或 `"false"`
- 数组应为 JSON 字符串：`'["item1", "item2"]'`
- 模型名称区分大小写

##### 速率限制

如果遇到速率限制：

```yaml
      env:
        OPENAI_KEY: ${{ secrets.OPENAI_KEY }}
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        # Add a fallback model for better reliability
        config.fallback_models: '["your-fallback-model"]'
        # Increase timeout for slower models
        config.ai_timeout: "300"
        github_action_config.auto_review: "true"
        github_action_config.auto_describe: "true"
        github_action_config.auto_improve: "true"
```

##### 常见错误消息与解决办法

**错误："Model not found"**
- **解决办法**：检查模型名称格式，确保它与精确标识一致。支持的模型及其正确标识见[在 PR-Agent 中更换模型](../usage-guide/changing_a_model.md)指南。

**错误："API key not found"**
- **解决办法**：确认 API 密钥已正确设置为仓库密钥，且环境变量名完全匹配
- **注意**：对于非 OpenAI 模型（Gemini、Claude 等），你只需要该模型专用的 API 密钥，而不需要 `OPENAI_KEY`

**错误："Rate limit exceeded"**
- **解决办法**：添加回退模型，或增大 `config.ai_timeout` 的值

**错误："Permission denied"**
- **解决办法**：确保工作流设置了正确的权限：
  ```yaml
  permissions:
    contents: read
    issues: write
    pull-requests: write
  ```
  默认工具不需要额外范围。仅当
  启用 `github.publish_as_check_run` 时才添加 `checks: write`。会推送仓库内容的功能，例如
  `pr_update_changelog.push_changelog_changes`，需要 `contents: write`；
  `pr_questions.resolve_threads` 也需要，因为 GitHub 把讨论串解决限制在该范围之后。如果省略
  `contents: write`，请启用 `config.restricted_mode`，这样需要该权限的操作会被跳过或安全
  回退，并保持 `pr_questions.resolve_threads` 关闭，因为受限模式并不覆盖它。
  详情见[受限模式指南](../usage-guide/additional_configurations.md#restricted-mode)。

**错误：不完整的 GitHub 文件导致 "PR-Agent command was not run"**
- **原因**：GitHub 把拉取请求变更文件响应限制为 3,000 个文件。当 GitHub
  返回不一致的文件计数元数据时，也可能出现不匹配。
- **解决办法**：如果拉取请求更改了超过 3,000 个文件，请把它拆成更小的拉取请求并再次运行
  该命令。否则，请重试该命令。

**错误："Invalid JSON format"**

- **解决办法**：检查数组是否正确格式化为 JSON 字符串：

```yaml

Correct:
config.fallback_models: '["model1", "model2"]'
Incorrect (interpreted as a YAML list, not a string):
config.fallback_models: ["model1", "model2"]
```

##### 调试提示

1. **启用详细日志**：添加 `config.verbosity_level: "2"` 以查看详细日志
2. **查看 GitHub Actions 日志**：查看步骤输出中的具体错误消息
3. **用最小配置测试**：从基本设置开始，再逐个添加选项
4. **核对密钥**：再次确认仓库设置中已设置所有必需密钥

##### 性能优化

对于大型仓库，为了获得更好的性能：

```yaml
      env:
        OPENAI_KEY: ${{ secrets.OPENAI_KEY }}
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        # Optimize for large PRs
        config.large_patch_policy: "clip"
        config.max_model_tokens: "32000"
        config.patch_extra_lines_before: "3"
        config.patch_extra_lines_after: "1"
        github_action_config.auto_review: "true"
        github_action_config.auto_describe: "true"
        github_action_config.auto_improve: "true"
```

#### 参考

更多详细配置选项见：

- [在 PR-Agent 中更换模型](../usage-guide/changing_a_model.md)
- [配置选项](../usage-guide/configuration_options.md)
- [自动化与用法](../usage-guide/automations_and_usage.md#github-action)

### 使用特定版本

:::tip
如果出于稳定性考虑，你想把 action 固定到某个特定版本（例如 v0.41.0），请使用：
```yaml
...
    steps:
      - name: PR Agent action step
        id: pragent
        uses: docker://pragent/pr-agent:0.41.0-github_action
...
```

为了增强安全性，你也可以按[摘要](https://hub.docker.com/r/pragent/pr-agent/tags)指定 Docker 镜像。用 `docker buildx imagetools inspect pragent/pr-agent:0.41.0-github_action --format '{{.Manifest.Digest}}'` 解析你所固定版本的摘要，然后用它代替标签：
```yaml
...
    steps:
      - name: PR Agent action step
        id: pragent
        uses: docker://pragent/pr-agent@sha256:<digest>
...
```

官方 Docker Hub 发布镜像也会发布 GitHub Artifact Attestations，因此在使用之前，你可以验证某个固定摘要确实由此仓库构建：
```sh
gh attestation verify \
  "oci://index.docker.io/pragent/pr-agent@sha256:<digest>" \
  --repo The-PR-Agent/pr-agent
```
:::

### 用于 GitHub Enterprise Server 的 Action

:::tip
要在 GitHub Enterprise Server 上使用该 action，请添加环境变量 `GITHUB__BASE_URL`，其值为你的 GitHub 服务器的 API URL。

例如，如果你的 GitHub 服务器位于 `https://github.mycompany.com`，请在工作流文件中加入：
```yaml
      env:
        # ... previous environment values
        GITHUB__BASE_URL: "https://github.mycompany.com/api/v3"
```
:::

---

## 作为 GitHub App 运行 {#run-as-a-github-app}

让你可以在私有或公开仓库上自动化审查流程。

1) 从 [GitHub 开发者门户](https://docs.github.com/en/developers/apps/creating-a-github-app)创建一个 GitHub App。

   - 设置以下权限：
     - Pull requests：Read & write
     - Issue comment：Read & write
     - Metadata：Read-only
     - Contents：Read-only（如果使用 `resolve_threads`，则为 Read & write——见下方说明）
   - 设置以下事件：
     - Issue comment
     - Pull request
     - Pull request review
     - Push（如果需要在拉取请求更新时触发）
     - Pull request review comment（在审查讨论串上使用 `/ask` 时必需）

   > **注意：** 如果启用 `pr_questions.resolve_threads`，GitHub App 需要 **Contents: Read & write** 权限。GitHub 的 `resolveReviewThread` GraphQL 变更受 Contents 权限限制，即使它只修改拉取请求讨论串的元数据。详情见 [GitHub 社区讨论](https://github.com/orgs/community/discussions/204269)。
   >
   > **重要：** 启用后，LLM 可能会解决由
   > 人工审查者发起的讨论串——而不仅是机器人生成的讨论串。仅当你的团队
   > 接受由 AI 解决讨论串时，才使用此设置。
   > 该功能为选择启用，默认关闭。

2) 为你的应用生成一个随机密钥，并保存备用。webhook 密钥是必需的：如果未配置 `GITHUB.WEBHOOK_SECRET`，服务器会以 HTTP 403 拒绝每一个传入的 webhook。例如可以使用：

```bash
WEBHOOK_SECRET=$(python -c "import secrets; print(secrets.token_hex(10))")
```

3) 从应用的设置页面获取以下信息：

   - 应用私钥（点击 "Generate a private key" 并保存文件）
   - 应用 ID

4) 克隆此仓库：

```bash
git clone https://github.com/the-pr-agent/pr-agent.git
```

5) 复制密钥模板文件并填入以下内容：

```bash
cp pr_agent/settings/.secrets_template.toml pr_agent/settings/.secrets.toml
# Edit .secrets.toml file
```

- 你的 OpenAI 密钥。
- 把应用的私钥复制到 private_key 字段。
- 把应用的 ID 复制到 app_id 字段。
- 把应用的 webhook 密钥复制到 webhook_secret 字段（必需）。
- 在 [configuration.toml](https://github.com/the-pr-agent/pr-agent/blob/main/pr_agent/settings/configuration.toml) 中把 deployment_type 设为 'app'

    > 本地 `.secrets.toml` 文件被排除在 Docker 构建上下文之外。切勿把密钥烤进容器镜像。
    > 对于容器部署，请在运行时通过环境变量或挂载的密钥卷提供密钥。
    > 例如，要在 Kubernetes 环境中把密钥文件作为卷注入，可以更新 pod spec，加入以下内容，
    > 假设你有一个名为 `pr-agent-settings` 的 Secret，其中有一个名为 `.secrets.toml` 的键：

    ```
           volumes:
            - name: settings-volume
              secret:
                secretName: pr-agent-settings
    // ...
           containers:
    // ...
              volumeMounts:
                - mountPath: /app/pr_agent/settings_prod
                  name: settings-volume
    ```

    > 服务镜像以 UID/GID `10001` 运行：挂载的密钥必须对该用户可读，挂载的数据路径必须对该用户可写。
    > 相对于主目录的挂载应放在 `/home/pragent` 下。

    > 另一种做法是在部署环境中把密钥设为环境变量，例如 `OPENAI.KEY` 和 `GITHUB.USER_TOKEN`。

6) 为应用构建 Docker 镜像，并可选地推送到 Docker 仓库。下面以 Dockerhub 为例：

    ```bash
    docker build . -t pr-agent:github_app --target github_app -f docker/Dockerfile

    # Optional, to push it to your own Docker repository:
    docker tag pr-agent:github_app <your-registry>/pr-agent:github_app
    docker push <your-registry>/pr-agent:github_app
    ```

7. 使用服务器、无服务器函数或容器环境托管该应用。或者，为了开发和
   调试，你可以使用 smee.io 等工具把 webhook 转发到本地机器。
    你可以查看[部署为 Lambda 函数](#deploy-as-a-lambda-function)

8. 回到应用的设置，并设置以下内容：

   - Webhook URL：应用服务器的 URL，或 smee.io 频道的 URL。
   - Webhook secret：你先前生成的密钥。

9. 通过「Install App」标签页安装该应用，并选择你需要的仓库。

10. 该应用在 gunicorn 下以多个工作进程运行。关于 `GUNICORN_WORKERS` / `GUNICORN_MAX_WORKERS` 旋钮和内存建议，请参见[为自托管 webhook 服务器估算规格](./index.md#sizing-a-self-hosted-webhook-server)——在设置内存限制之前值得一读。

> **注意：** 从 GitHub App 运行 PR-Agent 时，会加载默认配置文件（configuration.toml）。
> 不过，你可以通过上传本地配置文件 `.pr_agent.toml` 来覆盖默认工具参数
> 要使用组织级全局配置，请设置 `config.global_settings_repo = "pr-agent-settings"`，创建带有 `.pr_agent.toml` 文件的 `<organization>/pr-agent-settings`，并把 GitHub App 也安装到该仓库。
> 该应用需要读取设置仓库以及拉取请求所在仓库。这同时适用于 GitHub.com 和 GitHub Enterprise Server。
> 更多信息请查看[使用指南](../usage-guide/automations_and_usage.md#github-app)
---

## 其他部署方式

### 部署为 Lambda 函数 {#deploy-as-a-lambda-function}

请注意，由于 AWS Lambda 环境变量名中不能包含 "."，你可以把环境变量中的每个 "." 替换为 "__"。<br>
例如：`GITHUB.WEBHOOK_SECRET` --> `GITHUB__WEBHOOK_SECRET`

1. 按照[此处](#run-as-a-github-app)的第 1–5 步操作。
2. 构建一个可用作 Lambda 函数的 Docker 镜像

    ```shell
    docker buildx build --platform=linux/amd64 . -t pr-agent:github_lambda --target github_lambda -f docker/Dockerfile.lambda
   ```
   （注意：--target github_lambda 是可选的，因为它是默认目标）


3. 将镜像推送到 ECR

    ```shell
    docker tag pr-agent:github_lambda <AWS_ACCOUNT>.dkr.ecr.<AWS_REGION>.amazonaws.com/pr-agent:github_lambda
    docker push <AWS_ACCOUNT>.dkr.ecr.<AWS_REGION>.amazonaws.com/pr-agent:github_lambda
    ```

4. 创建一个使用该已上传镜像的 Lambda 函数。将 Lambda 超时至少设为 3 分钟。
5. 为该 Lambda 函数配置函数 URL。
6. 在 Lambda 函数的环境变量中，将 `AZURE_DEVOPS_CACHE_DIR` 指定为可写位置，例如 /tmp。（见[链接](https://github.com/the-pr-agent/pr-agent/pull/450#issuecomment-1840242269)）
7. 回到[方法 5](#run-as-a-github-app)的第 8–9 步，把函数 URL 作为你的 Webhook URL。
    Webhook URL 形如 `https://<LAMBDA_FUNCTION_URL>/api/v1/github_webhooks`

#### 使用 AWS Secrets Manager

对于生产环境的 Lambda 部署，请使用 AWS Secrets Manager，而不是环境变量：

1. 在 AWS Secrets Manager 中创建一个 JSON 格式如下的密钥：

```json
{
  "openai.key": "sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
  "github.webhook_secret": "your-webhook-secret-from-step-2",
  "github.private_key": "-----BEGIN RSA PRIVATE KEY-----\nMIIEpAIBAAKCAQEA...\n-----END RSA PRIVATE KEY-----"
}
```

2. 为你的 Lambda 执行角色添加 IAM 权限 `secretsmanager:GetSecretValue`
3. 在 Lambda 中设置这些环境变量：

```bash
AWS_SECRETS_MANAGER__SECRET_ARN=arn:aws:secretsmanager:us-east-1:123456789012:secret:pr-agent-secrets-AbCdEf
CONFIG__SECRET_PROVIDER=aws_secrets_manager
```

---

### AWS CodeCommit 设置

并非所有功能都已加入 CodeCommit。就目前而言，CodeCommit 的实现是在命令行上运行 PR-Agent CLI，并使用存储在环境变量中的 AWS 凭据。具有多个目标的 CodeCommit 拉取请求会针对每一个目标仓库和提交比较进行审查；单目标拉取请求保持相同行为。以下是一组说明，用于让 PR-Agent 从命令行审查你的 CodeCommit 拉取请求：

1. 创建一个 IAM 用户，用于读取 CodeCommit 拉取请求并发表评论
    - 注意：该用户应只有 CLI 访问权限，而没有控制台访问权限
2. 为该用户添加 IAM 权限，以允许访问 CodeCommit（见下方 IAM 角色示例）
3. 为你的 IAM 用户生成访问密钥
4. 使用环境变量设置访问密钥和秘密密钥（见下方访问密钥示例）
5. 在 `pr_agent/settings/configuration.toml` 设置文件中把 `git_provider` 的值设为 `codecommit`
6. 设置 `PYTHONPATH`，使其包含你的 `pr-agent` 项目目录
    - 方案 A：把 `PYTHONPATH="/PATH/TO/PROJECTS/pr-agent` 加入你的 `.env` 文件
    - 方案 B：在一条命令中设置 `PYTHONPATH` 并运行 CLI，例如：
        - `PYTHONPATH="/PATH/TO/PROJECTS/pr-agent python pr_agent/cli.py [--ARGS]`

---

##### AWS CodeCommit IAM 角色示例

允许该用户访问 CodeCommit 的 IAM 权限示例：

- 注意：以下是一套可用的 IAM 权限示例，具有仓库读取权限，以及允许发表评论的写入权限
- 注意：如果你只希望 pr-agent 审查拉取请求，可以进一步收紧 IAM 权限；不过此 IAM 示例可以工作，并允许 pr-agent 在拉取请求上发表评论
- 注意：你可能希望把 `"Resource": "*"` 替换为你的仓库列表，以便把访问限制在这些仓库

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "codecommit:BatchDescribe*",
                "codecommit:BatchGet*",
                "codecommit:Describe*",
                "codecommit:EvaluatePullRequestApprovalRules",
                "codecommit:Get*",
                "codecommit:List*",
                "codecommit:PostComment*",
                "codecommit:PutCommentReaction",
                "codecommit:UpdateComment",
                "codecommit:UpdatePullRequestDescription",
                "codecommit:UpdatePullRequestTitle"
            ],
            "Resource": "*"
        }
    ]
}
```

##### AWS CodeCommit 访问密钥与秘密密钥

使用环境变量设置访问密钥和秘密密钥的示例

```sh
export AWS_ACCESS_KEY_ID="XXXXXXXXXXXXXXXX"
export AWS_SECRET_ACCESS_KEY="XXXXXXXXXXXXXXXX"
export AWS_DEFAULT_REGION="us-east-1"
```

##### AWS CodeCommit CLI 示例

按照上面的说明设置好 AWS CodeCommit 之后，下面是一个 CLI 运行示例，它让 pr-agent **审查**给定的拉取请求。
（在示例中替换你自己的 PYTHONPATH 和拉取请求 URL）

```sh
PYTHONPATH="/PATH/TO/PROJECTS/pr-agent" python pr_agent/cli.py \
  --pr_url https://us-east-1.console.aws.amazon.com/codesuite/codecommit/repositories/MY_REPO_NAME/pull-requests/321 \
  review
```
