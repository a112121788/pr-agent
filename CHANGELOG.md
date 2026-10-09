# 变更日志

**发布说明现已放在 GitHub。** 每个版本的权威变更记录是
[Releases 页面](https://github.com/The-PR-Agent/pr-agent/releases)，由该版本合并的拉取请求生成。本文件不再按版本更新。

查看两个版本之间的差异时，使用 compare 视图，例如
[`v0.40.0...v0.41.0`](https://github.com/The-PR-Agent/pr-agent/compare/v0.40.0...v0.41.0)。

---

## 历史存档

以下条目是 2023 年 7 月至 8 月保存在本文件中的部分日志，记录止于 `2023-08-03`。它们只保留历史，不描述此后的任何版本。

### 2023-08-03

#### 优化

- 为 diff 文件增加缓存，减少 API 调用。
- 重构 `load_large_diff`，只在必要时生成 patch。
- 修复 GitLab provider 未能正确获取新文件的问题。

### 2023-08-02

#### 增强

- 多个工具开始使用提交说明。
- 提交说明保存到每个工具的 `vars`。
- 在多个工具提示词中展示提交说明。

### 2023-08-01

#### 增强

- 增加从拉取请求读取提交说明的能力。
- 为 GitHub 和 GitLab provider 实现提交说明读取。
- PR 描述模板在存在提交说明时展示该部分。
- 增加仓库级 `.pr_agent.yaml` 配置。
- 增加 `use_repo_settings_file`，用于启用或禁用仓库级配置。

### 2023-07-30

#### 增强

- 允许在运行时修改 `configuration.toml` 中的配置参数。
- 命令行和机器人命令接受配置参数。
- PR Agent 可以处理每个动作的附加参数。

### 2023-07-28

#### 改进

- 改善 GitLab provider 的错误处理和日志。
- 改善 GitLab 行内评论和代码建议处理。
- 修复 GitLab 代码建议多出一行的问题。

### 2023-07-26

#### 新增

- 根据 PR 内容更新 `CHANGELOG.md`。
- 为 GitHub provider 增加该功能。
- 为变更日志更新增加配置和提示词。
