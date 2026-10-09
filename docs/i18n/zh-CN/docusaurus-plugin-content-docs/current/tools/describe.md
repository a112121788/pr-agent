---
title: "描述"
sidebar_position: 2
---

## 概述

生成拉取请求标题、类型、摘要、代码导览和标签。

该工具可以在每次新拉取请求[打开](../usage-guide/automations_and_usage.md#github-app-automatic-tools-when-a-new-pr-is-opened)时自动触发，也可以在任意拉取请求上评论来手动调用：

```
/describe
```

## 使用示例

### 手动触发

在任意拉取请求上评论 `/describe` 来手动调用该工具：

<img src="/img/describe_comment.png" alt="描述评论" width="512" />

大约 30 秒后，工具会为该拉取请求生成描述：

<img src="/img/describe_new.webp" alt="新描述" width="512" />

大型拉取请求的分块运行期间，临时评论 `Preparing PR description...` 会就地改写，例如 `Preparing PR description... analyzed 2 of 3 chunks`；当每个分块都处理完毕后，若有分块放弃，会追加 `, 1 chunk failed`。这需要 `config.publish_output_progress`，以及能够编辑和删除评论的提供方；单分块运行会保留普通占位符。

如果要编辑[配置](#configuration-options)，把相关项加到命令中：

```
/describe --pr_description.some_config1=... --pr_description.some_config2=...
```

### 自动触发

要在拉取请求打开时自动运行 `describe`，在[配置文件](../usage-guide/configuration_options.md#local-configuration-file)中定义：

```
[github_app]
pr_commands = [
    "/describe",
    ...
]

[pr_description]
publish_labels = true
...
```

- `pr_commands` 列出拉取请求打开时会自动执行的命令。
- `[pr_description]` 节包含你想修改的 `describe` 工具配置（如果有）。

## 保留用户原始描述

默认情况下，PR-Agent 会把你的原始拉取请求描述放在生成内容之上，从而尽量保留它。
这要求在最初创建拉取请求时就包含你的描述。

“PR-Agent 把拉取请求中的原始描述删掉了。为什么？”

根据我们的经验，有两种可能原因：

- 如果在自动化工具*运行期间*编辑描述，可能发生竞态，导致原始描述丢失。因此，请在发起拉取请求之前写好描述。

- *更新*拉取请求描述时，`/describe` 工具会把 “PR Type” 字段之上的一切视为用户内容并予以保留。
此标记之下的一切都视为先前自动生成的内容，并会被替换。

<img src="/img/pr_description_user_description.png" alt="描述评论" width="512" />

## 时序图支持
`/describe` 工具包含一张 Mermaid 时序图，展示组件/函数之间的交互。

该选项默认通过 `pr_description.enable_pr_diagram` 参数启用。

图的方向会随形状调整。节点最长链超过 `pr_description.pr_diagram_direction_threshold` 的图会自上而下绘制，而不是从左到右，以免过宽的图被缩小到无法阅读。把 `pr_description.pr_diagram_direction` 设为 `LR` 或 `TD` 可以固定方向。


[//]: # (### 如何启用或禁用)

[//]: # ()
[//]: # (在配置中：)

[//]: # ()
[//]: # (```)

[//]: # (toml)

[//]: # ([pr_description])

[//]: # (enable_pr_diagram = true)

[//]: # (```)

## 配置选项 {#configuration-options}

下面的说明解释每个选项的行为。权威默认值见
[`configuration.toml`](https://github.com/the-pr-agent/pr-agent/blob/main/pr_agent/settings/configuration.toml)
中的相关节。

<details open>
<summary>可用配置</summary>

<table>
  <tr>
    <td><b>publish_labels</b></td>
    <td>设为 true 时，工具会把标签发布到拉取请求。</td>
  </tr>
  <tr>
    <td><b>publish_description_as_comment</b></td>
    <td>设为 true 时，工具会把描述作为评论发布到拉取请求。设为 false 时，会覆盖原始描述。</td>
  </tr>
  <tr>
    <td><b>publish_description_as_comment_persistent</b></td>
    <td>设为 true 且 `publish_description_as_comment` 为 true 时，工具会把描述作为持久评论发布到拉取请求。</td>
  </tr>
  <tr>
    <td><b>add_original_user_description</b></td>
    <td>设为 true 时，工具会把用户原始描述加入生成的描述。</td>
  </tr>
  <tr>
    <td><b>generate_ai_title</b></td>
    <td>设为 true 时，工具还会为拉取请求生成 AI 标题。</td>
  </tr>
  <tr>
    <td><b>extra_instructions</b></td>
    <td>给工具的可选附加指令。例如："focus on the changes in the file X. Ignore change in ..."</td>
  </tr>
  <tr>
    <td><b>enable_pr_type</b></td>
    <td>设为 false 时，描述内容中不会把 `PR type` 显示为文本值。</td>
  </tr>
  <tr>
    <td><b>enable_pr_description</b></td>
    <td>设为 false 时，不会向模型请求 AI 生成的摘要节，也不会在描述内容中显示。其他节（图、变更导览）不受影响。</td>
  </tr>
  <tr>
    <td><b>final_update_message</b></td>
    <td>设为 true 时，调用 `/describe` 结束后会添加一条评论消息 [`PR Description updated to latest commit...`](https://github.com/the-pr-agent/pr-agent/pull/499#issuecomment-1837412176)。</td>
  </tr>
  <tr>
    <td><b>enable_semantic_files_types</b></td>
    <td>设为 true 时，会生成 “Changes walkthrough” 节。</td>
  </tr>
  <tr>
        <td><b>file_table_collapsible_open_by_default</b></td>
        <td>控制 “Changes walkthrough” 节中的文件列表初始是展开还是折叠。</td>
  </tr>
  <tr>
    <td><b>collapsible_file_list</b></td>
    <td>设为 true 时，“Changes walkthrough” 节中的文件列表可折叠。设为 "adaptive" 时，仅当文件数超过 <code>collapsible_file_list_threshold</code> 时文件列表才可折叠。</td>
  </tr>
  <tr>
    <td><b>enable_large_pr_handling</b></td>
    <td>设为 true 时，对于大型拉取请求，工具会多次调用 AI 并合并结果，以便覆盖更多文件。</td>
  </tr>
  <tr>
    <td><b>enable_help_text</b></td>
    <td>设为 true 时，工具会在评论中显示帮助文本。</td>
  </tr>
  <tr>
    <td><b>enable_pr_diagram</b></td>
    <td>设为 true 时，工具会生成一张 Mermaid 流程图，概括拉取请求的主要变更。不适用时该字段保持为空。</td>
  </tr>
  <tr>
    <td><b>pr_diagram_direction</b></td>
    <td>生成的 Mermaid 流程图方向：<b>adaptive</b>、<b>LR</b> 或 <b>TD</b>。使用 adaptive 时，方向由图的形状决定。</td>
  </tr>
  <tr>
    <td><b>pr_diagram_direction_threshold</b></td>
    <td>使用 <b>adaptive</b> 方向时，最长链超过这么多个节点的图会自上而下绘制，而不是从左到右。</td>
  </tr>
  <tr>
    <td><b>auto_create_ticket</b></td>
    <td>设为 true 时，拉取请求打开时会在工单系统中自动创建工单。</td>
  </tr>
</table>

</details>

## 标记模板

要启用标记，设置 `pr_description.use_description_markers=true`。
标记可以用类似模板的机制，方便地把用户内容和自动生成内容整合在一起。

例如，如果拉取请求的原始描述是：

```
User content...

## PR Type:
pr_agent:type

## PR Description:
pr_agent:summary

## PR Walkthrough:
pr_agent:walkthrough

## PR Diagram:
pr_agent:diagram
```

标记 `pr_agent:type` 会被替换为拉取请求类型，`pr_agent:summary` 会被替换为拉取请求摘要，`pr_agent:walkthrough` 会被替换为拉取请求导览，`pr_agent:diagram` 会被替换为时序图（如果已启用）。

<img src="/img/describe_markers_before.png" alt="标记前的描述" width="512" />

会变成

<img src="/img/describe_markers_after.webp" alt="标记后的描述" width="512" />

**配置参数**：

- `use_description_markers`：设为 true 时，工具使用标记模板。它会把每个形如 `pr_agent:marker_name` 的标记替换为相应内容。默认值为 false。
- `include_generated_by_header`：设为 true 时，工具会为任何自动内容添加专用页眉：'Generated by PR Agent at ...'。默认值为 true。
- `diagram`：如果作为标记出现，会被替换为拉取请求时序图（如果已启用）。

## 自定义标签

describe 工具的默认标签相当通用，因为它们要用于任何仓库：[`Bug fix`、`Tests`、`Enhancement`、`Documentation`、`Other`]。

你可以定义与自己仓库和用例相关的自定义标签。
自定义标签可以在配置文件中定义，也可以直接在仓库的[标签页](#handle-custom-labels-from-the-repos-labels-page)上定义。

请为每个标签提供恰当的标题，以及详细、措辞清楚的描述，这样工具才知道何时建议它。
每条标签描述都应当是一个**条件语句**，根据拉取请求内容指示是否把该标签加到拉取请求上。

<details open>
<summary>自定义标签不再相关时自动移除</summary>

如果自定义标签不再相关，运行 `generate_labels` 工具或 `describe` 工具时会自动把它从拉取请求上移除。

</details>


### 从配置文件处理自定义标签

配置文件中的自定义标签配置示例：

```
[config]
enable_custom_labels=true


[custom_labels."sql_changes"]
description = "Use when a PR contains changes to SQL queries"

[custom_labels."test"]
description = "use when a PR primarily contains new tests"

...
```

### 从仓库标签页处理自定义标签 {#handle-custom-labels-from-the-repos-labels-page}

也可以从仓库标签页控制 `describe` 工具会建议的自定义标签：

- GitHub：前往 `https://github.com/{owner}/{repo}/labels`（或点击议题或拉取请求页面上的 “Labels” 标签）
- GitLab：前往 `https://gitlab.com/{owner}/{repo}/-/labels`（或点击左侧菜单的 “Manage” -> “Labels”）

然后添加/编辑自定义标签。格式应当如下：

- 标签名：自定义标签的名称。
- 描述：描述以前缀 `pr_agent:` 开头，例如：`pr_agent: Description of when AI should suggest this label`。<br>

自定义标签示例：

- `Main topic:performance` -  pr_agent:The main topic of this PR is performance
- `New endpoint` -  pr_agent:A new endpoint was added in this PR
- `SQL query` -  pr_agent:A new SQL query was added in this PR
- `Dockerfile changes` - pr_agent:The PR contains changes in the Dockerfile
- ...

描述应当全面、详细，说明何时添加所需标签。例如：
<img src="/img/add_native_custom_labels.webp" alt="添加原生自定义标签" width="768" />

## 使用提示

:::tip[自动化]
- 首次安装 PR-Agent 应用时，describe 工具的[默认模式](../usage-guide/automations_and_usage.md#github-app)是：
```
pr_commands = ["/describe", ...]
```
意味着 `describe` 工具会以默认配置在每个拉取请求上自动运行。
:::

- 标记是控制生成描述的另一种方式，把最大控制权交给用户。如果设置：

   ```
   pr_commands = ["/describe --pr_description.use_description_markers=true", ...]
   ```

   工具会把拉取请求描述中每个形如 `pr_agent:marker_name` 的标记替换为相应内容，其中 `marker_name` 是以下之一：
         *`type`：拉取请求类型。
         * `summary`：拉取请求摘要。
         * `walkthrough`：拉取请求导览。

- 请注意，启用标记后，如果原始拉取请求描述不包含任何标记，工具完全不会改动描述。
