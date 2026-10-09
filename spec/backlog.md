# Backlog

## Done

### `GITEE-S1` - Gitee provider 核心路径

| 字段 | 内容 |
|---|---|
| 状态 | done |
| 优先级 | P0 |
| Outcome | `/describe`、`/review`、`/ask` 能读取 Gitee PR 并走到发布步骤 |
| Scope | `pr_agent/git_providers/gitee_provider.py`、provider 注册、`[gitee]` 配置、离线测试。不含 Webhook 与文档站 |
| Evidence | 提交 `3b3dc06e`；四个真实 PR 的只读冒烟；工具干跑全程只有 GET |
| Acceptance | `tests/unittest` 12770 passed；pre-commit 通过 |
| Risk | 发布代码未对真实仓库执行 |
| Rollback | 回退 `3b3dc06e` |

## Done

### `GITEE-S2` - 真实写入冒烟

| 字段 | 内容 |
|---|---|
| 状态 | done |
| 优先级 | P1 |
| Outcome | 描述、普通评论和标签能写到指定 Gitee PR，并可以撤回 |
| Scope | 只写 `eclouddev/hlzs_web#2896`。评论已删除，描述已恢复，临时标签已从 PR 和仓库删除 |
| Evidence | 评论 `51489944` 发布后删除；描述 PATCH 后读回一致；`pr-agent-smoke` 标签添加后删除 |
| Acceptance | 三项写入均读回成功，结束后标题、描述、评论和标签恢复原状 |
| Risk | 已发生并完成回滚 |
| Rollback | 已执行。若再次出现测试标记，用原描述重新 PATCH，并删除名为 `pr-agent-smoke` 的评论和标签 |

## Ready

### `GITEE-S3` - 行内评论定位

| 字段 | 内容 |
|---|---|
| 状态 | done |
| 优先级 | P1 |
| Outcome | `/improve` 的行内评论按 Gitee 的 diff 行号定位 |
| Scope | `GiteeProvider._inline_position`。没有向真实 PR 写行内评论 |
| Evidence | `hlzs_web#2896` 的 145 个 diff 和 `bi_service#1` 的 41 个 diff 全部与“第一个 `@@` 下一行是 position 1”一致；重建 diff 的 `---`/`+++` 文件头已扣除 |
| Acceptance | `TestInlineComments` 与 provider 契约测试 351 passed；两个真实 PR 只读复核无 mismatch |
| Risk | 还没有用 Gitee 的写入响应确认 position。多行评论和旧文件侧定位未覆盖 |
| Rollback | 回退 `_inline_position` 的文件头换算 |

## Draft

### `GITEE-S4` - Webhook 路由

| 字段 | 内容 |
|---|---|
| 状态 | done |
| 优先级 | P2 |
| Outcome | 签名通过的 Gitee PR 打开事件和评论命令能转成 `PRAgent.handle_request` |
| Scope | `pr_agent/servers/gitee_app.py`、`GITEE.WEBHOOK_SECRET`、默认命令和 `gitee_app` Docker target。不含真实事件投递和推送触发 |
| Evidence | Gitee 官方签名为 `timestamp + "\\n" + secret` 的 HMAC-SHA256；`tests/unittest/test_gitee_webhook.py` |
| Acceptance | 缺密钥返回 403，错误签名返回 401；打开 PR 依次运行 `/describe`、`/review`、`/improve`；`/review` 评论被转发，普通评论不运行 |
| Risk | 尚未用 Gitee 实际投递验证字段名。仓库配置不能覆盖 `webhook_secret` |
| Rollback | 不启动 `pr_agent.servers.gitee_app:app`，或清空 `GITEE.WEBHOOK_SECRET` 使入口拒绝全部请求 |

### `GITEE-S5` - 文档站

| 字段 | 内容 |
|---|---|
| 状态 | done |
| 优先级 | P2 |
| Outcome | 用户能按文档配置 Gitee token、Webhook 和 Docker 服务 |
| Scope | `docs/docs/installation/gitee.md`、安装索引、侧边栏和平台矩阵。未新增 logo，也未改 provider |
| Evidence | `docs/` 下 `npm run build` 成功；矩阵只标记已验证能力 |
| Acceptance | 新页面被侧边栏和安装索引引用，文档生产构建通过 |
| Risk | 真实 Gitee Webhook 字段仍未由一次实际投递核对 |
| Rollback | 删除 `gitee.md`，并还原安装索引、侧边栏和平台矩阵 |

## Ready

### `DOCS-ZH-1` - 文档站中文入口

| 字段 | 内容 |
|---|---|
| 状态 | done |
| 优先级 | P2 |
| Outcome | 中文用户可以从 `/zh-CN/` 进入文档站，并看到中文首页和导航 |
| Scope | Docusaurus i18n、中文首页、导航和首页组件文案。其余 43 页继续回退为英文 |
| Evidence | `docs/` 下 `npm run build -- --locale zh-CN` 与默认 `npm run build` 均成功 |
| Acceptance | `/zh-CN/` 输出中文首页；未翻译页面仍可访问；英文根路径保持可用 |
| Risk | 中文页不能使用指向未翻译文件的相对 Markdown 链接 |
| Rollback | 删除 `docs/i18n/zh-CN/`，并移除 `docusaurus.config.js` 的 `i18n` 配置 |

## Ready

### `FACTORY-1` - 受理记录

| 字段 | 内容 |
|---|---|
| 状态 | done |
| 优先级 | P1 |
| Outcome | 提出人用一条评论留下意图，机器只保存，不改写 |
| Scope | 新增 `/intake 新业务\|旧版迭代\|新版升级\|双线`。写入结构化评论。不判定，不合并 |
| Evidence | 审核工厂四段；当前评论没有独立受理记录 |
| Acceptance | 四种意图之一能发布受理评论，并包含原话、目标分支和 head SHA；非法意图被拒绝且不发布 |
| Risk | 模型或命令别名改写作者原话 |
| Rollback | 不注册 `/intake` |

### `FACTORY-2` - 证据绑定提交号

| 字段 | 内容 |
|---|---|
| 状态 | done |
| 优先级 | P1 |
| Outcome | 审查证据失效点清楚：提交一变，旧证据不再代表当前改动 |
| Scope | `/review` 与 `/improve` 评论头部增加 head SHA。不新增判定 |
| Evidence | `eclouddev/hlzs_web#2896` 的评论没有提交号 |
| Acceptance | 新评论第一段含完整 SHA；离线渲染测试锁定该行 |
| Risk | 长 SHA 影响现有评论识别 |
| Rollback | 去掉 SHA 行 |

## Draft

### `FACTORY-3` - 人工判定

| 字段 | 内容 |
|---|---|
| 状态 | draft |
| 优先级 | P1 |
| Outcome | 负责人用 `/verdict 放行\|退回\|等待` 留下判定，模型的“批准”不能代替 |
| Scope | 解析三个词并发布判定评论。先记录评论人，不做权限名单 |
| Evidence | 审查结论目前只是模型草稿 |
| Acceptance | 三个词能绑定当前 SHA；其他词拒绝；审查正文里的“批准”不会生成判定 |
| Risk | 任意评论者都能写判定 |
| Rollback | 不注册 `/verdict` |

依赖 `FACTORY-1` 和 `FACTORY-2`。

### `FACTORY-4` - 汇入前检查

| 字段 | 内容 |
|---|---|
| 状态 | draft |
| 优先级 | P1 |
| Outcome | 没有当前提交的“放行”时，机器明确说不能汇入 |
| Scope | `/merge-check` 只发布检查结果。不调用 Gitee 合并接口 |
| Evidence | 当前没有汇入闸门 |
| Acceptance | 缺判定、SHA 不一致、判定为退回或等待时结果都是不能汇入；放行且 SHA 一致时结果是可以由人合并 |
| Risk | 用户以为命令会自动合并 |
| Rollback | 不注册 `/merge-check` |

依赖 `FACTORY-3`。

### `FACTORY-5` - 双线先拆

| 字段 | 内容 |
|---|---|
| 状态 | draft |
| 优先级 | P2 |
| Outcome | 明确声明为双线的改动不能被一次审查放行 |
| Scope | 受理意图为“双线”时添加阻塞规则。不做语义猜测 |
| Evidence | 课程要求双线变更先拆；`review_policy.py` 还没有该规则 |
| Acceptance | `/intake 双线` 后，审查评论包含“先拆成两张拉取请求” |
| Risk | 把普通大改动误判为双线 |
| Rollback | 删除该规则 |

## Icebox

- 判定人权限名单。
- 旧版契约和新版契约的自动对照。
- 真实 Gitee Webhook 投递核对。
