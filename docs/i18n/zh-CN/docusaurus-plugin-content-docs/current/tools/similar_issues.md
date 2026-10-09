---
title: "相似议题"
sidebar_position: 8
---

## 概述

> **注意**：`/similar_issue` 是**实验性**功能。它只在 GitHub 上工作，作为单提供方工具却占了项目依赖和配置面中不成比例的很大一部分，因此不在 v1 稳定性保证范围内。没有任何后端针对其真实驱动做过测试。

相似议题工具会检索与当前议题最相似的议题。
这是一条以议题为范围的命令：在议题上评论 `/similar_issue`（由 GitHub Action 提供；GitHub App webhook 只分发拉取请求上的评论），或在 CLI 中使用 `--issue_url` 运行：

```
/similar_issue
```

## 使用示例

<img src="/img/similar_issue_original_issue.png" alt="similar_issue_original_issue" width="768" />

<img src="/img/similar_issue_comment.png" alt="similar_issue_comment" width="768" />

<img src="/img/similar_issue.png" alt="similar_issue" width="768" />

### 索引与再次运行 {#indexing-and-re-runs}

为了执行检索，`similar_issue` 工具会把仓库议题索引到已配置的向量数据库中。在每个后端上：

- **首次运行**最多索引 `max_issues_to_scan` 个议题（默认 `500`）。
- **后续运行**检查最新的 `max_issues_to_scan` 个议题，并索引其中缺失的议题，因此已索引的议题不会重新嵌入。
- `force_update_dataset = true` 会使每次运行都重新索引整个仓库：LanceDB 会先删除该仓库的行，Pinecone 和 Qdrant 则覆盖已有行。
- `skip_comments = true` 会跳过议题评论，只嵌入议题标题和正文。

这些键位于 `[pr_similar_issue]` 节。下面每个后端小节都会说明各自的配置和再次运行行为。

### 选择向量数据库

在 `configuration.toml` 的 `[pr_similar_issue]` 下设置 `vectordb` 参数，以配置首选数据库：

```
[pr_similar_issue]
vectordb = "lancedb"  # options: "pinecone", "lancedb", "qdrant"
```

#### 可用选项

可从以下向量数据库中选择：

1. LanceDB
2. Pinecone
3. Qdrant

#### LanceDB 配置

LanceDB 是默认后端（`vectordb = "lancedb"`），不需要外部凭证。索引存放在 `[lancedb] uri` 键给出的本地目录中（默认 `./lancedb`）。同一目录中索引的每个仓库共享一张表（`codium-ai-pr-agent-issues`）；行在元数据中带有仓库名标记。

如[索引与再次运行](#indexing-and-re-runs)所述，首次运行会创建表并最多索引 `max_issues_to_scan` 个议题；后续运行会索引最新 `max_issues_to_scan` 个议题中缺失的议题；`force_update_dataset = true` 会删除该仓库的行并重新索引。

#### Pinecone 配置

要将 Pinecone 用于 `similar issue` 工具，把这些凭证加入 `.secrets.toml`（或设置为环境变量）：

```
[pinecone]
api_key = "..."
cloud = "aws"
region = "us-east-1"
```

`cloud` 的值必须是 `aws`、`gcp` 或 `azure` 之一，`region` 必须是该云提供的可用区。这些参数可以通过注册 [Pinecone](https://app.pinecone.io/?sessionType=signup/) 获得。请注意，该工具使用 Pinecone 的 serverless 索引 API；来自 gcp-starter pod 层级的旧 `environment` 设置已不再支持。

`cloud` 和 `region` 只在索引尚不存在、需要创建时使用。已有索引按名称打开，绝不会重建，因此把现有部署迁移到新配置不会丢失已存储的向量。

再次运行时，首次运行会创建索引并 upsert 最多 `max_issues_to_scan` 个议题；后续运行会索引最新 `max_issues_to_scan` 个议题中缺失的议题；`force_update_dataset = true` 会重新索引整个仓库。

:::note[没有任何后端针对其真实驱动做过测试]

`similar-issue` 依赖组未在 CI 中安装，因此 pinecone 测试针对伪造模块运行，qdrant 测试从不构造客户端，lancedb 测试针对伪造表运行。
:::

:::note[默认向量数据库]

`vectordb` 默认为 `lancedb`，无需外部凭证即可工作。要使用 qdrant 或 pinecone，请在 `[pr_similar_issue]` 下设置 `vectordb = "qdrant"` 或 `vectordb = "pinecone"`。
:::

#### Qdrant 配置

要将 Qdrant 用于 `similar issue` 工具，把这些凭证加入 `.secrets.toml`（或设置为环境变量）：

```
[qdrant]
url = "https://YOUR-QDRANT-URL" # e.g., https://xxxxxxxx-xxxxxxxx.eu-central-1-0.aws.cloud.qdrant.io
api_key = "..."
```

然后在 `configuration.toml` 中选择 Qdrant：

```
[pr_similar_issue]
vectordb = "qdrant"
```

可以从 [Qdrant Cloud](https://cloud.qdrant.io/) 获取免费的托管 Qdrant 实例。

即使服务器不强制认证，`api_key` 也必须存在（接受空字符串）：工具会同时读取 `url` 和 `api_key`，任一缺失都会抛出错误。重新索引会在单次请求中上传整个仓库。

Qdrant 点存放在名为 `codium-ai-pr-agent-issues-v2` 的集合中，由共享索引名（`codium-ai-pr-agent-issues`）追加 `-v2` 后缀得到。该后缀只是 Qdrant 后端的实现细节；pinecone 和 lancedb 使用不带后缀的名称。

再次运行时，首次运行会创建集合并存储最多 `max_issues_to_scan` 个议题；后续运行会索引最新 `max_issues_to_scan` 个议题中缺失的议题；`force_update_dataset = true` 会重新索引整个仓库。

:::note[升级在点 ID 修复之前创建的索引]

较早版本仅根据议题 ID 派生点 ID，因此相同议题编号会在不同仓库之间冲突。现在 ID 以仓库名作为种子，这意味着较早版本写入的点永远不会被改写或删除——它们仍携带匹配的 `metadata.repo` 载荷，因此仍然可查询，并可能与其替代点一起出现。

`-v2` 集合后缀避开了这个问题：新索引写入 `codium-ai-pr-agent-issues-v2`，原有的 `codium-ai-pr-agent-issues` 集合保持不变。不会删除任何内容，升级后的首次运行会把仓库重新索引到新集合。对结果满意后，可以在 Qdrant 中手动删除旧的 `codium-ai-pr-agent-issues` 集合以回收存储。
:::

## 如何使用

- 安装该工具的额外依赖（向量数据库和数据集），普通的 `uv sync` 并不包含它们：
`uv sync --group similar-issue`

- 要从 **CLI** 调用 “similar issue” 工具，运行：
`uv run pr-agent --issue_url=... similar_issue`

- 要通过在线用法调用 “similar” issue 工具，在议题上[评论](https://github.com/the-pr-agent/pr-agent/issues/178#issuecomment-1716934893)：
`/similar_issue`

- 也可以把 “similar issue” 工具加入 [github_app 节的 pr_commands 列表](https://github.com/the-pr-agent/pr-agent/blob/main/pr_agent/settings/configuration.toml)，使其在新议题打开时自动运行
