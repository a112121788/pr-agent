# Roadmap

## 北极星

让 PR-Agent 的 `/describe`、`/review`、`/ask`、`/improve` 能在 Gitee 拉取请求上闭环运行，并且发布行为可验证、可回退。

## Now

- Gitee provider 核心读写路径已在本地 `main` 的 `3b3dc06e`。真实写入、行内评论定位、Webhook 和文档站还没做。

## Next

1. 在一个指定的 Gitee PR 上验证描述、评论和标签写入。
2. 用真实 diff 核对行内评论的 `position`。
3. 用一次真实 Gitee Webhook 投递核对事件字段。
4. 用真实 Gitee Webhook 投递核对事件字段，再决定是否补 logo 和发布流水线。

## Later

- 持久评论、反应和代码建议的真实回归。
- 私有化 Gitee 部署的 API base 与证书配置样例。

## 质量门槛

- 新增 provider 必须通过共享契约测试：方法契约、行链接、请求策略、语言缓存。
- 不新增运行时依赖。Gitee 继续用 urllib3。
- token 只从 `GITEE.PERSONAL_ACCESS_TOKEN` 或 `GITEE_ACCESS_TOKEN` 读取，不写入仓库。

## 风险

- Gitee OpenAPI 与 GitHub 形状不一致：语言列表、diff `patch` 对象、评论时间线都已在 provider 内归一，后续改动要回归这些形状。
- 行内评论的 `position` 还没有真实 diff 证据。
- Webhook 载荷与鉴权方式尚未对照官方事件文档核实。
