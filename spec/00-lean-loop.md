# Lean Loop

PR-Agent 的本地交付控制台。流程按 Intake → Slice → Plan → Implement → Verify → Document → Review → Decide 推进，每次只做一个 ready 切片。

## 停止规则

- 工作树有无关改动时先停下，不覆盖。
- 预计超过 2 天的任务先拆，不在同一轮里做。
- 对真实 Git 平台的写入、发布、推送和提交，都要单独获得确认。
- 同类失败连续两次后停止，先找替代方案。
- 不给 `pr_agent/servers/` 和前端界面补单元测试；界面用浏览器或端到端验证。

## Ready / Done

Ready 必须写清 Outcome、Scope、Acceptance、Evidence、Risk、Rollback。

Done 必须满足：diff 落在 Scope 内，验收命令已跑或写明没跑的原因，契约或用户文档已同步，backlog 状态已更新，回滚路径明确。

## 验证矩阵

| 改动 | 最小验证 |
|---|---|
| Git provider | `PYTHONPATH=. uv run pytest tests/unittest/test_<provider>_provider.py -q`，再跑全量 `tests/unittest` |
| 配置与文档站 | `uv run ruff check` 覆盖改动文件；文档改动再跑 `npm run build`（在 `docs/`） |
| 真实平台 | 先只读冒烟。写入单独批准，并记录目标仓库与 PR |
| 提交前 | `uv run pre-commit run --files <paths>` |

Python 用 `uv`，测试从仓库根目录带 `PYTHONPATH=.` 运行。
