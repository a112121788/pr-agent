# 参与贡献

感谢你为 Gitee PR-Agent 做出贡献。

## 开始

1. Fork 仓库并克隆你的副本。
2. 安装 [uv](https://docs.astral.sh/uv/) 和 Python 3.12 或更高版本。
3. 执行 `uv sync`，按 `uv.lock` 创建 `.venv`。
4. 创建分支：
   - 新功能：`git checkout -b feature/功能名称`
   - 缺陷修复：`git checkout -b fix/问题描述`
5. 做出修改。
6. 添加或更新测试。
7. 在本地运行单元测试：

   ```bash
   PYTHONPATH=. uv run pytest tests/unittest
   ```

8. 检查改动文件：

   ```bash
   uv run ruff check --fix <改动的 Python 文件>
   uv run pre-commit run --files <改动文件>
   ```

9. 使用 Conventional Commits 编写提交说明。
10. 推送到你的 Fork，并提交拉取请求。

## 开发约定

- 一个拉取请求只处理一个功能或修复。
- 遵循现有代码风格。
- 为新行为添加 Pytest 单元测试。
- 用户可见行为变化时更新文档。

## 拉取请求流程

1. 写清改动内容。
2. 关联相关议题。
3. 必要时更新 `README.md`。
4. 等待维护者审查。

## 需要帮助

- 在 [GitHub Discussions](https://github.com/the-pr-agent/pr-agent/discussions) 提问。
- 查看[中文文档](https://docs.pr-agent.ai/)。
- 通过 [GitHub Issues](https://github.com/the-pr-agent/pr-agent/issues) 报告缺陷或提出功能请求。
