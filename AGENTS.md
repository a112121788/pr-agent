# 仓库指南

本文件是编码代理的共享仓库指南。工具专用说明应引用本文件，不要重复仓库级规则。

## 要做与不要做

- **要**使用 `pyproject.toml` 声明的 Python ≥ 3.12，并用 `uv sync` 按 `uv.lock` 安装运行时与开发依赖。
- **要**在运行测试时设置 `PYTHONPATH=.`，例如 `PYTHONPATH=. uv run pytest tests/unittest/test_gitee_provider.py -q`。
- **要**通过 `.pr_agent.toml` 或 `pr_agent/settings/` 下的文件调整配置，不要把值硬编码进代码。
- **不要**提交密钥或访问令牌；按健康检查和端到端测试的方式使用环境变量。
- **不要**全局重排或重排版文件；保持 120 字符行宽、现有导入顺序和文档字符串风格。
- **不要**在未获维护者同意时删除或重命名配置、提示词或工作流文件。

## 项目结构

Gitee PR-Agent 只为 Gitee 拉取请求生成中文审查证据。

- `pr_agent/agent/` 通过 `pr_agent/agent/pr_agent.py` 调度 `review`、`describe`、`improve` 等命令。
- `pr_agent/tools/` 实现审查、代码建议、文档更新和标签生成。
- `pr_agent/algo/` 包含模型处理、提示词、token、类型和共享算法。
- `pr_agent/git_providers/` 只注册 `GiteeProvider`；身份和密钥仍分别位于 `pr_agent/identity_providers/` 与 `pr_agent/secret_providers/`。
- `pr_agent/settings/` 保存 Dynaconf 默认值；仓库级覆盖来自 `.pr_agent.toml`。
- `pr_agent/servers/` 只保留 Gitee Webhook 入口 `gitee_app.py`。
- `tests/unittest/`、`tests/e2e_tests/` 和 `tests/health_test/` 分别放单元、端到端和冒烟测试。
- `docs/` 是默认中文的 Docusaurus 站点。
- `.github/workflows/` 运行单元测试、覆盖率、文档、pre-commit 和发布。
- `docker/Dockerfile` 提供 `cli`、`gitee_app` 和 `test` 三个目标。

## 请求流程

命令行或 Webhook 调用 `PRAgent.handle_request(...)`，再由 `command2class` 找到 `pr_agent/tools/` 中的工具。工具读取 Gitee 拉取请求，准备提示词，调用模型，并把中文结果发布为评论。

### 提示词

工具构造 `self.vars`，连同系统和用户提示词交给 `TokenHandler`。渲染使用 `StrictUndefined`，模板引用的变量必须存在。提示词位于 `pr_agent/settings/`，新文件必须加入 `pr_agent/config_loader.py` 的 `settings_files`。

### 配置

使用 `pr_agent/config_loader.py` 的 `get_settings()`。默认值在 `configuration.toml`，仓库覆盖由 `apply_repo_settings` 在命令执行前应用。密钥放在环境变量或被忽略的 `.secrets.toml` 中。

### Gitee Provider

平台差异通过 `provider.is_supported("feature")` 判断。Gitee 不支持 `push_code`，因此代码建议和变更日志只发布评论，不推送文件。

## 构建、测试与开发

- 安装依赖：`uv sync`。
- 单个测试：`PYTHONPATH=. uv run pytest tests/unittest/test_gitee_provider.py -q`。
- 全部单元测试：`PYTHONPATH=. uv run pytest tests/unittest -v`。
- 本地命令：`uv run gitee-pr-agent --pr_url <Gitee PR 地址> review`。`pr-agent` 仍指向同一入口。
- 测试镜像：`docker build -f docker/Dockerfile --target test .`。
- 文档：在 `docs/` 中执行 `npm ci` 和 `npm run build`。

## 代码风格

Ruff 是唯一的 Python 检查器，规则为 `E`、`F`、`B`、`I`。提交前对改动文件运行：

```bash
uv run ruff check --fix <改动的 Python 文件>
uv run pre-commit run --files <改动文件>
```

不要启用全仓 `ruff format`。Python 字符串与周围代码一致时使用双引号。`pr_agent/settings/` 中的 TOML 保持原有顺序和注释。文档页使用 front matter，新页面注册到 `docs/sidebars.js`。

## 测试约定

- 新测试放在最接近的目录。Pytest 默认只收集 `tests/unittest`。
- 优先测试 `pr_agent/algo/`、`pr_agent/tools/` 和 Gitee provider 的辅助函数。
- 端到端测试需要 Gitee 与模型凭据，只在凭据和环境准备好时运行。
- 健康检查覆盖 `/describe`、`/review` 和 `/improve`。提示词发生实质变化时更新预期结果。

## 提交与拉取请求

- 遵循 `CONTRIBUTING.md`，使用 Conventional Commits。
- 分支使用 `feature/<name>` 或 `fix/<issue>`。
- 用户可见行为变化时同步 README 或 `docs/`。
- 审查前运行相关本地检查，并确认 `build-and-test` 与 `pre-commit` 可通过。

## 安全与权限

- 添加依赖、重命名文件或修改工作流前先确认。
- 可以读取文件并运行有针对性的检查；完整 Docker 构建和依赖外部凭据的端到端测试需先确认。
- 不提交密钥、缓存凭据或覆盖率产物。
- 提示词和配置是单一事实来源，相关 TOML 要一起更新。
- 披露漏洞前先阅读 `SECURITY.md`。
