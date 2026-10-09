---
title: "为拉取请求获取工单上下文"
sidebar_position: 5
---

`支持的 Git 平台：GitHub、GitLab、Bitbucket、Azure DevOps、Gitea`

:::note[分支名链接：Jira 键适用于所有提供方；数字 GitHub 议题仅适用于 GitHub]
**Jira** 工单键（例如 `ABC-123`）会在**每个 Git 提供方**上从分支名中提取。
从分支名提取**数字 GitHub 议题**链接（以及可选的 `branch_issue_regex` 设置）目前**仅在 GitHub 上**实现；对其他提供方的支持计划在后续版本中提供。
:::

## 概述

PR-Agent 通过与多个工单管理系统无缝连接，简化代码审查工作流。
这种集成会在代码变更旁边自动呈现相关工单信息和上下文，从而丰富审查过程。

**支持的工单系统**：

- [GitHub/GitLab 议题](#githubgitlab-issues-integration)
- [Jira](#jira-integration)
- [Asana](#asana-integration)

**获取的工单数据：**

1. 工单标题
2. 工单描述
3. 自定义字段（验收标准）
4. 子任务（已链接任务）
5. 标签
6. 附加图片/截图

## 受影响的工具

工单识别要求：

- GitHub/GitLab 议题引用可以出现在 PR/MR 标题或描述中。GitHub 也会识别分支名中的数字议题引用。
- 对于 Jira 工单，应按 [Jira 集成](#jira-integration)中的说明向 Jira 认证。
- 对于 Asana 工单，见 [Asana 集成](#asana-integration)。

### 描述工具

PR-Agent 会识别工单，并使用工单内容（标题、描述、标签）为代码变更提供额外上下文。
通过理解修改背后的理由和意图，LLM 可以提供更有洞察、更相关的代码分析。

### 审查工具

与 `describe` 工具类似，`review` 工具会使用工单内容为代码变更提供额外上下文。

此外，此功能会评估拉取请求（PR）在多大程度上遵循关联工单或议题所定义的原始目的/意图。
每个工单会被分配一个标签（符合性/对齐程度），表示拉取请求完成其原始目的的程度：

- Fully Compliant（完全符合）
- Partially Compliant（部分符合）
- Not Compliant（不符合）
- PR Code Verified（PR 代码已验证）

<img src="/img/ticket_compliance_review.png" alt="工单符合性" width="768" />

`PR Code Verified` 标签表示拉取请求代码满足工单要求，但需要代码范围之外的额外人工测试。例如——在不同环境（Mac、Windows、移动端等）中验证 UI 显示。


#### 配置选项

-

    默认情况下，`review` 工具会自动验证拉取请求是否符合所引用的工单。
    如果要禁用此反馈，把以下行加入配置文件：

    ```toml
    [pr_reviewer]
    require_ticket_analysis_review=false
    ```

-

    如果设置：
    ```toml
    [pr_reviewer]
    check_pr_additional_content=true
    ```
    （默认值：`false`）

    `review` 工具还会验证拉取请求代码不包含与工单无关的额外内容。如果包含，该拉取请求最多会被标为 `PR Code Verified`，并且 `review` 工具会提供一条评论，说明在拉取请求代码中发现的额外无关内容。

## GitHub/GitLab 议题集成 {#githubgitlab-issues-integration}

PR-Agent 会自动识别 PR/MR 标题或描述中提到的 GitHub/GitLab 议题，并获取议题内容。
有效的 GitHub/GitLab 议题引用示例：

- `https://github.com/<ORG_NAME>/<REPO_NAME>/issues/<ISSUE_NUMBER>` 或 `https://gitlab.com/<ORG_NAME>/<REPO_NAME>/-/issues/<ISSUE_NUMBER>`
- `#<ISSUE_NUMBER>`
- `<ORG_NAME>/<REPO_NAME>#<ISSUE_NUMBER>`

完整的 GitHub 议题 URL 会在已配置实例的 HTTPS Web 源上被识别，包括 GitHub Enterprise URL，例如 `https://github.example.com/<ORG_NAME>/<REPO_NAME>/issues/<ISSUE_NUMBER>`。
其他源上的完整 GitHub 议题 URL 会被忽略。

GitHub 先处理描述中的引用，然后是分支名，然后是标题。GitLab 先处理
描述引用，再处理标题引用。重复的相同引用不会增加查找，标题引用使用
现有的工单查找和结果限制，而不会挤掉更早的来源。

可选的 `config.description_issue_regex` 设置只应用于 GitHub 拉取请求描述。GitHub 标题使用
上面的内置引用格式，包括最多六位数字的本地 `#<ISSUE_NUMBER>` 引用。

分支名也可以用来链接议题，例如：
- `123-fix-bug`（其中 `123` 是议题编号）

这种分支名检测**仅在 Git 提供方为 GitHub 时**适用。对其他平台的支持计划稍后提供。

默认情况下，GitHub 工单上下文限于拉取请求自身的仓库。另一个
仓库中的议题和子议题需要通过 `config.repo_context_sibling_repos` 获得明确的主机批准：

```toml
[config]
repo_context_sibling_repos = ["myorg/shared-tickets"]
```

只接受拉取请求仓库已解析所有者之下的规范仓库。对于私有或内部
仓库，命令请求者还必须具有读取权限；没有命令执行者时，CLI 运行使用拉取请求作者。
仓库设置和评论参数不能更改此允许列表。空列表会禁用
跨仓库工单读取，包括公开仓库。只批准可以包含在
使用方拉取请求的审查或描述中的内容。工单查找限制与同级文件限制是分开的。
PyGithub 可能会跟随议题转移，但来自不同仓库的结果会在用于提示词之前被丢弃。
请按转移后议题的当前仓库和编号引用它。

## Asana 集成 {#asana-integration}

PR-Agent 可以检测拉取请求描述中的 Asana 任务引用，通过
[Asana API](https://developers.asana.com/reference/gettask) 获取所引用的任务，并把它们的标题、描述和标签纳入
工单符合性检查。

**支持的引用格式：**

- 旧链接：`https://app.asana.com/0/{project_gid}/{task_gid}`
- 当前永久链接：`https://app.asana.com/1/{workspace_gid}/task/{task_gid}`
- 当前项目链接：`https://app.asana.com/1/{workspace_gid}/project/{project_gid}/task/{task_gid}`
- 当前 Home 链接：`https://app.asana.com/1/{workspace_gid}/home/task/{task_gid}`
- 以 `/comment/{comment_gid}` 结尾的任务评论链接（获取的是父任务）

**如何把拉取请求链接到 Asana 任务：**

在拉取请求描述中包含 Asana 任务 URL。PR-Agent 会自动检测它，并把它列入相关
工单列表。

### 认证

创建一个[Asana 个人访问令牌](https://developers.asana.com/docs/personal-access-token)，使其能够访问
PR-Agent 应当读取的任务。在 `.secrets.toml` 中配置：

```toml
[asana]
api_token = "YOUR_PERSONAL_ACCESS_TOKEN"
```

对于基于环境变量的部署，设置等效的 Dynaconf 环境变量：

```bash
ASANA__API_TOKEN="YOUR_PERSONAL_ACCESS_TOKEN"
```

该令牌只作为 Bearer 令牌发送到 Asana 固定的任务 API 端点。未配置令牌，或任务
对该令牌不可访问时，PR-Agent 会跳过该 Asana 任务，而不是对照占位
内容评估符合性。API 请求超时可以用 `asana.request_timeout` 调整（默认 10 秒，上限 60 秒）。

### 工单数量限制

PR-Agent 最多获取最先检测到的三个 Asana 任务，并保持它们在描述中的顺序。这是
附加的、特定于提供方的限制，原生工单列在 Asana 任务之前：

- 在 GitHub 上，保留现有的三个 GitHub 议题上限，外加最多三个 Asana 任务。
- 在 Azure DevOps 上，保留所有已链接工作项，外加最多三个 Asana 任务。
- 在其他提供方上，最多三个检测到的 Asana 任务可以提供工单上下文。

把这些限制分开，可以防止 Asana 引用悄悄挤掉原生工单，也避免改变
现有提供方既定的工单提取行为。

## Jira 集成 {#jira-integration}

Jira 查找需要 `bitbucket` extra：`pip install "pr-agent[bitbucket]"`。没有它时，查找会被跳过并记录警告。

只支持 **Jira Cloud**。基础 URL 由经过验证的站点名派生
（`jira_site` → `https://<site>.atlassian.net`），而不是作为自由格式 URL 接受，因此
配置的目标始终是 Atlassian Cloud 主机。Jira Server / Data Center
（自托管）使用自由格式主机，目前尚不支持；一旦
自托管情形的基础 URL 处理确定下来，就可以添加。

### Jira Cloud

#### 邮箱/令牌认证

可以从 Atlassian 账户创建 API 令牌：

1. 登录 https://id.atlassian.com/manage-profile/security/api-tokens。

2. 点击 Create API token。

3. 在出现的对话框中，为新令牌输入名称并点击 Create。

4. 点击 Copy to clipboard。

<img src="https://images.ctfassets.net/zsv3d0ugroxu/1RYvh9lqgeZjjNe5S3Hbfb/155e846a1cb38f30bf17512b6dfd2229/screenshot_NewAPIToken" alt="Jira Cloud API 令牌" width="384" />

5. 在 PR-Agent 主机配置（密钥文件或 `JIRA__JIRA_SITE` 等环境变量）中添加以下行。仓库的 `.pr_agent.toml` 不能设置它们：

```toml
[jira]
jira_site = "<JIRA_SITE>"   # the "<site>" in https://<site>.atlassian.net (e.g. "mycompany")
jira_api_email = "YOUR_EMAIL"
jira_api_token = "YOUR_API_TOKEN"
```

`jira_site` 是你的 Jira Cloud 站点名——`.atlassian.net` 之前的部分（对于
`https://mycompany.atlassian.net`，站点是 `mycompany`）。PR-Agent 把基础 URL 构建为
`https://<jira_site>.atlassian.net`；它不接受完整 URL，因此配置
不能把已认证请求重定向到另一个主机。把 `jira_api_email` 和
`jira_api_token` 存为密钥（环境变量或密钥文件），不要放在
提交到仓库的配置中。

#### 验收标准 / 需求（可选）

要把工单的验收标准纳入分析，把 `jira_requirements_field`
设为存放它的自定义字段 ID。字段 ID 特定于你的 Jira
实例（例如 `customfield_10127`）；留空则跳过需求。

```toml
[jira]
jira_requirements_field = "customfield_10127"
```

#### 项目键允许列表（可选）

工单检测会匹配任何形如 `PROJECT-123` 的文本，因此标题或描述中的 `SHA-256`、
`UTF-8` 或 `ISO-8601` 这类字符串每次都会花费一次返回 404 的已认证查找。如果部署使用一组已知的 Jira 项目，在主机的 `project_keys` 中列出它们的键；任何其他前缀的键都会在查找之前被丢弃（它们会
在调试级别的日志中各记录一次）。把列表留空则会查找找到的每个键。
`project_keys`、`jira_site` 和 `jira_api_email` 仅限主机：仓库的 `.pr_agent.toml`
或评论命令不能更改它们。

```toml
[jira]
project_keys = ["PROJ", "OPS"]
```

条目是纯大写项目键（仅字母，与 Jira 的写法一致）；其他任何内容
（小写标签、完整工单键、URL、空白条目）都会被忽略并记录
警告。如果设置了列表但没有任何条目有效，在修复之前根本不会进行 Jira 查找，
以免拼写错误悄悄再次放宽查找。只有选项缺失、
空列表，以及设为空字符串的环境变量覆盖，才表示“查找每个
键”。

### 如何把拉取请求链接到 Jira 工单

要与 Jira 集成，可以用以下任一方法把拉取请求链接到工单：

**方法 1：描述引用：**

在拉取请求描述中包含工单引用，使用完整 URL 格式 `https://<JIRA_SITE>.atlassian.net/browse/ISSUE-123`，或缩短的工单 ID `ISSUE-123`（缩短 ID 不要带前缀或后缀）。

**方法 2：分支名检测：**

用工单 ID 作为前缀命名分支（例如 `ISSUE-123-feature-description` 或 `ISSUE-123/feature-description`）。
