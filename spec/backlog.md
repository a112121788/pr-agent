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
| 状态 | done |
| 优先级 | P1 |
| Outcome | 负责人用 `/verdict 放行\|退回\|等待` 留下判定，模型的“批准”不能代替 |
| Scope | 解析三个词并发布判定评论。先记录评论人，不做权限名单 |
| Evidence | `parse_verdict` 拒绝「批准」；流水线「退回」只写判定记录，测试确认未调用合并 |
| Acceptance | 三个词能绑定当前 SHA；其他词拒绝；审查正文里的“批准”不会生成判定 |
| Risk | 任意评论者都能写判定 |
| Rollback | 不注册 `/verdict` |

依赖 `FACTORY-1` 和 `FACTORY-2`。

### `FACTORY-4` - 汇入前检查

| 字段 | 内容 |
|---|---|
| 状态 | done |
| 优先级 | P1 |
| Outcome | 没有当前提交的“放行”时，机器明确说不能汇入 |
| Scope | `/merge-check` 只发布检查结果。不调用 Gitee 合并接口 |
| Evidence | `render_merge_check` 与 `PRMergeCheck` 只发布检查；默认 `allow_auto_merge=false` |
| Acceptance | 缺判定、SHA 不一致、判定为退回或等待时结果都是不能汇入；放行且 SHA 一致时结果是可以由人合并 |
| Risk | 用户以为命令会自动合并 |
| Rollback | 不注册 `/merge-check` |

依赖 `FACTORY-3`。

### `FACTORY-5` - 双线先拆

| 字段 | 内容 |
|---|---|
| 状态 | done |
| 优先级 | P2 |
| Outcome | 明确声明为双线的改动不能被一次审查放行 |
| Scope | 受理意图为“双线”时添加阻塞规则。不做语义猜测 |
| Evidence | `review_policy.py` 对显式双线返回「先拆成两张拉取请求」；普通描述不触发 |
| Acceptance | `/intake 双线` 后，审查评论包含“先拆成两张拉取请求” |
| Risk | 把普通大改动误判为双线 |
| Rollback | 删除该规则 |

## Ready

### `COCKPIT-1` - 移除已登记仓库

| 字段 | 内容 |
|---|---|
| 状态 | done |
| 优先级 | P1 |
| Outcome | 驾驶舱只保留当前需要管理的仓库 |
| Scope | `watched_repos` 增加删除。删除后不再列出 PR，不删除 Gitee 仓库和历史审核记录 |
| Evidence | 页面有「移除」；`FactoryStore.remove_repo` 只删登记，SQLite 测试覆盖 |
| Acceptance | 页面每个仓库有“移除”；移除后刷新不再出现；SQLite 测试覆盖 |
| Risk | 误删正在审查的仓库记录 |
| Rollback | 隐藏移除按钮 |

### `COCKPIT-2` - 审查任务异步化

| 字段 | 内容 |
|---|---|
| 状态 | done |
| 优先级 | P1 |
| Outcome | 点审查后页面立即返回，长时间模型调用不再占住浏览器 |
| Scope | `/dashboard/run` 创建任务并后台执行 `/review`、`/improve`、`/status`。同一 PR 同一命令重复点击不新建任务 |
| Evidence | `/dashboard/run` 立即返回并带 `X-Job-Id`；重复点击不新建；失败摘要含错误 |
| Acceptance | 请求立即返回任务号；任务状态依次为排队、运行、完成或失败；失败保存错误摘要 |
| Risk | 服务进程退出会丢失内存中的后台任务 |
| Rollback | 恢复同步调用 |

### `COCKPIT-3a` - 流水线可操作

| 字段 | 内容 |
|---|---|
| 状态 | done |
| 优先级 | P1 |
| Outcome | 打开一张拉取请求就能看出是谁的哪张 PR、Gitee 上已有什么评论，并在原地发起审查 |
| Scope | 流水线页展示身份和全部评论；动作栏固定；提交只替换 `#pipeline`。不含判定按钮 |
| Evidence | 用户指出 `/dashboard/pr` 交互差；#2896 当时只剩一条 `Failed to review PR`，页面却显示没有记录 |
| Acceptance | 页面出现编号、标题和分支；失败评论可见；审查按钮不整页跳转 |
| Risk | 五秒检查仍会在内容变化时重绘展开状态 |
| Rollback | 恢复整页表单提交，并只渲染工厂记录 |

### `CODEX-1` - 并行取证不再抢同一个 Codex 状态目录

| 字段 | 内容 |
|---|---|
| 状态 | done |
| 优先级 | P0 |
| Outcome | 大 PR 的分块审查不会因为 Codex 进程互相挤掉而留下 `Failed to review PR` |
| Scope | `CodexAIHandler` 每次调用使用独立 `CODEX_HOME`。不改审查提示词，不换回 LiteLLM |
| Evidence | 发布镜像上 3 路并行调用有 2 路 `TransportClosedError`：`failed to initialize sqlite state runtime under /root/.codex` |
| Acceptance | 单测锁定每次调用的临时目录不同且会删除；同一网关的 3 路并行短调用都返回 |
| Risk | 空的 `CODEX_HOME` 不再读取镜像里的 `~/.codex` 登录；密钥和地址仍由 `OPENAI__KEY` / `OPENAI__API_BASE` 传入 |
| Rollback | 去掉 `CODEX_HOME`，恢复所有调用共享默认状态目录 |

### `DOCS-1` - 补上驾驶舱说明

| 字段 | 内容 |
|---|---|
| 状态 | done |
| 优先级 | P2 |
| Outcome | 读者能从文档知道如何登记仓库、批量审查，以及审查中的拉取请求不能再开一次 |
| Scope | 新增 `docs/docs/usage-guide/dashboard.md`，并在侧栏、README 和审核工厂页加上入口。不改驾驶舱行为 |
| Evidence | 批量审查已在首页，文档仍只写单张点审查 |
| Acceptance | 文档含「批量审查」「审查中」和 `/dashboard`；侧栏登记了 `usage-guide/dashboard` |
| Risk | 文档与以后的按钮文案再次分叉 |
| Rollback | 删除该页，并去掉侧栏和 README 中的链接 |

### `REVIEW-2` - 首页登记后可批量审查

| 字段 | 内容 |
|---|---|
| 状态 | done |
| 优先级 | P1 |
| Outcome | 登记仓库之后，可以手动一次审查已登记仓库里打开的拉取请求 |
| Scope | 驾驶舱首页「登记」后面增加「批量审查」，提交到已有的 `/dashboard/drive`。打开页面不自动审查。正在审查的同一张不再开一次 |
| Evidence | 用户要求首页登记后面添加批量审查 |
| Acceptance | 页面上「批量审查」出现在「登记」之后；GET `/dashboard` 不启动审查；POST `/dashboard/drive` 才启动 |
| Risk | 一次会为多张未在审的拉取请求排队 |
| Rollback | 去掉该按钮，保留单张「审查」 |

### `REVIEW-1` - 审查只保留自动驾驶

| 字段 | 内容 |
|---|---|
| 状态 | done |
| 优先级 | P0 |
| Outcome | 代码审查不再靠人逐行点头。Agent 自己验证，人抽查，抽查问题用来改规则和环境 |
| Scope | 去掉驾驶舱的人工加速、辅助驾驶和确认按钮。打开页面即批量审查，不先规划意图。保留已记录的双线、批准不成放行、以及放行且提交号一致才汇入。不新增规则编辑器 |
| Evidence | 三种模式把审查又变成人点确认；代码多到看不过来 |
| Acceptance | 页面没有模式名和确认按钮；`/dashboard/mode` 不存在；当前提交放行会汇入，退回和双线不会 |
| Risk | 意图没写明的拉取请求会停在留给人工 |
| Rollback | 恢复模式表、模式路由和确认按钮 |

## Ready

### `V08-1` - 内测数据重启后还在

| 字段 | 内容 |
|---|---|
| 状态 | done |
| 优先级 | P0 |
| Outcome | 内测机器重启后，已登记仓库和审查任务还在，失败任务不再一直显示审查中 |
| Scope | 驾驶舱数据目录挂卷；任务失败写成「失败」并放开按钮；页面显示构建标识。不改审查规则，不打开自动合并 |
| Evidence | 重建容器后登记记录消失；审查失败时按钮可能停在审查中 |
| Acceptance | 重启同一数据卷后仓库仍在；一条失败任务的状态是失败，并且可以再次点审查；页面能读到构建标识 |
| Risk | 挂错卷会看到空库，或把测试库当成内测库 |
| Rollback | 去掉挂卷，继续使用容器内 `/data` |

### `V09-1` - 批量审查写回一条真实评论

| 字段 | 内容 |
|---|---|
| 状态 | done |
| 优先级 | P0 |
| Outcome | 内测仓库点一次批量审查，就能在 Gitee 上看到中文审查评论 |
| Scope | 用已登记仓库跑通批量审查和流水线 Markdown。同一张审查中不再入队。不新增意图规划 |
| Evidence | `https://gitee.com/eclouddev/hlzs_web/pulls/2885` 评论 `51506075`，提交号 `19501d5c264ffe43d38719477fae86a3029a25e5`；运行中再次触发仍只有一条活动任务 |
| Acceptance | 记录一张拉取请求地址、评论编号和提交号；审查未结束时再次点击不产生第二条运行中任务 |
| Risk | 真实审查会向 Gitee 写评论，并消耗模型额度 |
| Rollback | 停用批量审查按钮，只保留单张审查 |

依赖 `V08-1`。

### `V10-1` - 0.1.0 内测包

| 字段 | 内容 |
|---|---|
| 状态 | done |
| 优先级 | P0 |
| Outcome | 没有读过源码的人能按说明完成一次审查，且这次试用不会自动合并 |
| Scope | 内测说明、已知问题、默认关闭自动合并的开关。不加入权限名单，不做意图规划 |
| Evidence | `config.allow_auto_merge=false`；内测步骤写在 `docs/docs/usage-guide/dashboard.md` |
| Acceptance | 按说明从启动到看到 Gitee 评论；默认配置下批量审查不会调用合并接口；说明里写明抽查问题改哪份规则 |
| Risk | 开关默认值弄反会在内测仓库上合并 |
| Rollback | 去掉开关，恢复「仅放行且非双线才合并」 |

依赖 `V09-1`。

## Draft

### `COCKPIT-3` - 审核对话页

| 字段 | 内容 |
|---|---|
| 状态 | done |
| 优先级 | P1 |
| Outcome | 一张 PR 的审核过程按时间显示成对话 |
| Scope | 新增 `/dashboard/pr?url=...`。展示受理、进度、审查、建议、状态和判定。页面定时刷新 |
| Evidence | `/dashboard/pr` 渲染运行中与完成后的任务状态不同 |
| Acceptance | 点击 PR 进入对话；运行中的任务显示“正在审查”；完成后出现结果 |
| Risk | 自动刷新打断阅读 |
| Rollback | 从 PR 行移除对话入口 |

依赖 `COCKPIT-2`。

### `COCKPIT-4` - 在对话里继续审核

| 字段 | 内容 |
|---|---|
| 状态 | done |
| 优先级 | P2 |
| Outcome | 审核人不用返回列表，也能继续发起审查、建议和判定 |
| Scope | 对话页底部提供审查、建议、状态、放行、退回、等待。判定仍写判定记录，不合并 |
| Evidence | 流水线有审查、建议、状态、放行、退回、等待；判定路由不调用合并 |
| Acceptance | 五条动作都创建异步任务或判定记录；页面能看到新的对话条目 |
| Risk | 连续点击产生重复审查 |
| Rollback | 保留只读对话页 |

### `COCKPIT-5` - 首页审查原地更新

| 字段 | 内容 |
|---|---|
| 状态 | done |
| 优先级 | P1 |
| Outcome | 点首页某一行的审查后，只更新这一行，浏览器不整页刷新 |
| Scope | 首页改为 JSON 接口加静态客户端。流水线页仍由服务端渲染。不引入前端框架 |
| Evidence | `/dashboard/api/run` 返回任务 JSON；`home.js` 在行末画执行图标并轮询 `/dashboard/api/jobs` |
| Acceptance | 点击审查不导航；行末有执行图标；状态随后变为完成或失败；重复点击不新建任务 |
| Risk | 客户端脚本失败时列表为空，登记表单仍会整页提交 |
| Rollback | 让 `/dashboard` 重新由服务端拼出拉取请求列表 |

### `COCKPIT-6` - 流水线原地更新

| 字段 | 内容 |
|---|---|
| 状态 | done |
| 优先级 | P1 |
| Outcome | 流水线页点审查或判定后，只更新这条流水线，浏览器不整页刷新 |
| Scope | `/dashboard/pr` 改为壳，数据来自 `/dashboard/api/pr`。判定走 `/dashboard/api/verdict`，不合并。不引入前端框架 |
| Evidence | `pipeline.js` 轮询 JSON，并在底栏画执行图标 |
| Acceptance | 页面壳不含评论正文；接口返回运行状态和评论 HTML；脚本不调用整页刷新 |
| Risk | 评论 HTML 由服务端渲染后交给客户端插入 |
| Rollback | 恢复把 `render_conversation_body` 直接写进页面 |

## Icebox

- 判定人权限名单。
- 旧版契约和新版契约的自动对照。
- 真实 Gitee Webhook 投递核对。
