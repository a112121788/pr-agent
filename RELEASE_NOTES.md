# 发布说明

**发布说明现已放在 GitHub。** `v0.12` 及之后每个版本的说明发布在
[Releases 页面](https://github.com/The-PR-Agent/pr-agent/releases)，由该版本合并的拉取请求生成。本文件不再按版本更新。

`0.34.2` 及之后的旧 Docker Hub 镜像位于 [`pragent/pr-agent`](https://hub.docker.com/r/pragent/pr-agent)。下方存档中的 `codiumai/pr-agent` 标签属于冻结命名空间，不再推送新镜像。

当前 Gitee PR-Agent 镜像发布在：

```text
ecloud-tcr.tencentcloudcr.com/ecloud_project/pr-agent
```

---

## 历史存档

以下条目覆盖 `v0.7` 至 `v0.11`（2023 年 9 月至 12 月），当时项目位于 `Codium-ai/pr-agent`。链接指向旧仓库，Docker 标签指向已冻结的 `codiumai/` 命名空间，只保留历史。

### [版本 0.11] - 2023-12-07

- codiumai/pr-agent:0.11
- codiumai/pr-agent:0.11-github_app
- codiumai/pr-agent:0.11-bitbucket-app
- codiumai/pr-agent:0.11-gitlab_webhook
- codiumai/pr-agent:0.11-github_polling
- codiumai/pr-agent:0.11-github_action

#### 新增：算法

- `/describe` 增加 [PR 变更导览](https://github.com/Codium-ai/pr-agent/pull/509)。
- 改进 PR Agent [提示词](https://github.com/Codium-ai/pr-agent/pull/501)。
- 持久工具完成后发送[更新消息](https://github.com/Codium-ai/pr-agent/pull/499)。
- 增加 Amazon Bedrock [支持](https://github.com/Codium-ai/pr-agent/pull/483)。

#### 修复

- 更新 Python 3.12 的 [依赖](https://github.com/Codium-ai/pr-agent/pull/503)。

### [版本 0.10] - 2023-11-15

- codiumai/pr-agent:0.10
- codiumai/pr-agent:0.10-github_app
- codiumai/pr-agent:0.10-bitbucket-app
- codiumai/pr-agent:0.10-gitlab_webhook
- codiumai/pr-agent:0.10-github_polling
- codiumai/pr-agent:0.10-github_action

#### 新增：算法

- 审查工具默认使用[持久评论](https://github.com/Codium-ai/pr-agent/pull/451)。
- Bitbucket 的审查建议带有[代码链接](https://github.com/Codium-ai/pr-agent/pull/428)。
- 允许限制[最大 token 数](https://github.com/Codium-ai/pr-agent/pull/437/files)。
- 支持 `gpt-4-1106-preview`。
- 支持 Google [Vertex AI](https://github.com/Codium-ai/pr-agent/pull/436)。
- 为增量审查实现[阈值](https://github.com/Codium-ai/pr-agent/pull/423)。
- 自定义标签与 PR 类型[解耦](https://github.com/Codium-ai/pr-agent/pull/431)。

#### 修复

- 修复 CLI 中的[引号解析](https://github.com/Codium-ai/pr-agent/pull/446)。
- 保留用户添加的[标签](https://github.com/Codium-ai/pr-agent/pull/433)。
- 修复 GitLab 和 Bitbucket 的缺陷。

### [版本 0.9] - 2023-10-29

- codiumai/pr-agent:0.9
- codiumai/pr-agent:0.9-github_app
- codiumai/pr-agent:0.9-bitbucket-app
- codiumai/pr-agent:0.9-gitlab_webhook
- codiumai/pr-agent:0.9-github_polling
- codiumai/pr-agent:0.9-github_action

#### 新增：算法

- 新增 `generate_labels` 工具。
- `review` 和 `describe` 支持自定义标签。
- 新增 `add_docs` 工具。
- GitHub Action 可通过 `.pr_agent.toml` 控制配置。
- GitHub App 可在推送事件上触发工具。
- Azure DevOps 支持自定义域名。
- PR 描述默认使用要点格式。

#### 新增：文档

安装、用法和工具文档有较大更新。

#### 修复

- 修复 Bitbucket pipeline 支持。
- 修复 `review -i` 的缺陷。
- `add_docs` 增加特定扩展名黑名单。

### [版本 0.8] - 2023-09-27

- codiumai/pr-agent:0.8
- codiumai/pr-agent:0.8-github_app
- codiumai/pr-agent:0.8-bitbucket-app
- codiumai/pr-agent:0.8-gitlab_webhook
- codiumai/pr-agent:0.8-github_polling
- codiumai/pr-agent:0.8-github_action

#### 新增：算法

- GitHub Action 可控制新建 PR 时自动运行的工具。
- 代码建议工具尽量避免只建议添加注释。

#### 修复

- 修复 GitLab 对 `pr_id` 的错误使用。

### [版本 0.7] - 2023-09-20

#### Docker 标签

- codiumai/pr-agent:0.7
- codiumai/pr-agent:0.7-github_app
- codiumai/pr-agent:0.7-bitbucket-app
- codiumai/pr-agent:0.7-gitlab_webhook
- codiumai/pr-agent:0.7-github_polling
- codiumai/pr-agent:0.7-github_action

#### 新增：算法

- 新增 `/similar_issue`，当时用于 GitHub App 和 CLI。
- `/describe` 增加标记模板能力。
- `/review` 增加预计审查工作量。

#### 新增：基础设施

- 实现 GitLab Webhook。
- 实现 Bitbucket App。

#### 修复

- 防止没有生成代码建议时出错。
- 提高无法自动检测语言的仓库的稳定性。
