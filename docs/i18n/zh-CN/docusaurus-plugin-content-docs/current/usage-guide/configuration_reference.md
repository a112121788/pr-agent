---
title: "配置参考"
sidebar_position: 4
---

> 本页为**自动生成**，不应手动编辑。
> 请用以下命令从 [TOML 源文件](https://github.com/the-pr-agent/pr-agent/blob/main/pr_agent/settings/configuration.toml) 重新生成：
>
> ```bash
> python scripts/generate_config_reference.py
> ```

PR-Agent 支持的每一个配置选项，按节分组。[configuration.toml](https://github.com/the-pr-agent/pr-agent/blob/main/pr_agent/settings/configuration.toml)
文件是默认值和行内注释的唯一事实来源；本页渲染同一份
列表，便于搜索和链接。

**说明**为空的行，是其 TOML 条目尚无解释性注释的键。
它们被有意列出而不是隐藏，因此这些空白同时也是文档的
待办清单。

## `[config]` {#config}

| Key | Default | 说明 |
| --- | --- | --- |
| `max_webhook_request_body_bytes` | 5242880 | webhook 服务器接受的最大请求体（5 MiB） |
**模型**

| Key | Default | 说明 |
| --- | --- | --- |
| `model` | "gpt-6.1-sol" |  |
| `fallback_models` | ["glm-5.3"] |  |
**CLI**

| Key | Default | 说明 |
| --- | --- | --- |
| `git_provider` | "github" |  |
| `publish_output` | true |  |
| `publish_output_progress` | true |  |
| `progress_gif_url` | "" | 可选，覆盖进度加载 gif 的 URL（示例：'https://.../spinner.gif'）。 |
| `progress_gif_width` | 48 | 可选，进度加载 gif 的宽度（单位 px）。 |
| `verbosity_level` | 0 | 0,1,2 |
| `use_extra_bad_extensions` | false |  |
**日志**

| Key | Default | 说明 |
| --- | --- | --- |
| `log_level` | "DEBUG" |  |
**配置**

| Key | Default | 说明 |
| --- | --- | --- |
| `use_repo_settings_file` | true |  |
| `use_global_settings_file` | true |  |
| `global_settings_repo` | "" | 仅主机侧的仓库名，位于所属 org/group/workspace 中，其 .pr_agent.toml 会应用到那里的每一个仓库。空值禁用命名空间范围的设置；设为 "pr-agent-settings" 可保持先前的行为 |
| `enable_per_directory_settings` | false | 为 true 时，从 PR 已更改文件向上遍历，合并找到的按目录划分的 .pr_agent.toml 文件（单体仓库支持）。会为每个 MR 增加有界的递归树发现；按目录的文件只能覆盖非关键节（见 REPO_PER_DIRECTORY_OVERRIDABLE_SECTIONS）。共享键由最近（最深）的目录胜出；深度相同的同级路径解析为字典序最后的路径；当匹配文件数超过 per_directory_settings_max_files 上限时，先应用更浅的文件，被部分截断的那一层会保留其较后路径（胜出）的同级文件；任何重叠都会作为警告记入日志。 |
| `per_directory_settings_max_files` | 20 | 每个 MR 应用的按目录 .pr_agent.toml 文件数量的硬上限（超出上限的更深层配置会被跳过并给出警告） |
| `per_directory_settings_max_tree_pages` | 10 | GitLab 递归树的最大页数（每页 100 个条目）；如果发现不完整则跳过嵌套设置。由根/主机控制，独立于设置文件上限。 |
| `extra_config_url` | "" | 可选的 URL 或路径，指向在仓库本地配置之前合并的额外 .pr_agent.toml；也可通过 --extra_config_url 或 PR_AGENT_EXTRA_CONFIG_URL 设置。见 docs/docs/usage-guide/configuration_options.md#external-configuration-url。 |
| `disable_auto_feedback` | false |  |
| `enable_auto_approval` | false | 为 true 时，/review 可以通过 auto_approve_logic() 自动批准 PR；该调用方目前被注释掉了 |
| `ai_timeout` | 120 | 2 分钟 |
| `http_request_timeout` | 60 | 仅主机侧，GitLab/Gitea 以及直接的 Bitbucket/Gerrit HTTP 尝试的连接/读取空闲秒数；上限为 600 |
| `retry_same_model_on_timeout` | true | 为 false 时，超时的调用不会在同一模型上重试，而是继续使用 fallback_models |
| `retry_same_model_on_length` | false | 为 true 时，因输出上限而被截断的空响应会在同一模型上重试，而不是直接转到 fallback_models |
| `skip_keys` | [] |  |
| `custom_reasoning_model` | false | 为 true 时，对不支持聊天式输入的模型禁用系统消息和温度控制 |
| `response_language` | "en-US" | PR 响应的语言区域代码，格式为 ISO 3166 和 ISO 639（例如 "en-US"、"it-IT"、"zh-CN" 等） |
| `repo_context_files` | ["AGENTS.md"] | 要作为 AI 提示词上下文包含的、相对仓库的文件（例如 AGENTS.md、CLAUDE.md）；设为 [] 可禁用本地上下文。结构化条目 {"repo_id" = ..., "file_path" = ...} 会从同一命名空间/所有者中选择一个同级默认分支文件；repo_id 必须位于下方由主机签发的 repo_context_sibling_repos 允许列表中。读取使用同级仓库的默认分支，并共享 repo_context_max_lines；仓库设置可以选择条目，评论参数不能覆盖此键 |
| `repo_context_from_default_branch` | true | 从仓库默认分支读取仓库上下文文件（只信任默认分支的内容）。设为 false 则改为从 PR 目标分支读取。 |
| `repo_context_max_lines` | 500 | 仓库上下文的最大渲染总行数，包括包裹标签 |
| `repo_context_sibling_repos` | [] | 仅主机侧的已批准同级仓库标识符列表（GitHub owner/repo、GitLab group/project 或数字 ID 字符串），repo_context_files 的同级条目可以从中选择。在 GitHub 上，这也会批准用于关联 issue 和子 issue 工单上下文的仓库。空值禁用同级读取。只批准那些内容可以在消费方 PR 中被披露的仓库，因为行动者检查限制的是谁触发读取，而不是谁选择了目标或输出落在哪里。仓库设置和评论参数不能更改此列表。解析之后会检查规范身份和所属命名空间 |
| `repo_context_max_sibling_files` | 5 | 每次构建仓库上下文时获取的同级仓库文件数量上限。获取次数与 repo_context_max_lines 分开限制，因此被选中的同级文件不能触发无界数量的跨仓库调用；同级文件仍然竞争 repo_context_max_lines 预算。仅主机侧（不能由仓库的 .pr_agent.toml 或评论命令提高），并钳制为每次构建最多 20 次获取的硬上限。 |
**token 上限**

| Key | Default | 说明 |
| --- | --- | --- |
| `max_description_tokens` | 500 |  |
| `max_commits_tokens` | 500 |  |
| `max_model_tokens` | 32000 | 限制任何模型可以使用的最大 token 数，无论该模型的默认能力如何。 |
| `custom_model_max_tokens` | -1 | 覆盖未知模型，或非原生自定义提供商上的 Sol 层级 GPT-6。 |
| `max_output_tokens` | 0 | 0 = 未设置（适用提供商自己的默认值） |
| `model_token_count_estimate_factor` | 0.3 | 用于提高 token 计数估算的系数，以降低因 token 过多导致模型失败的可能性——仅在请求精确估算时适用。 |
| `image_input_token_allowance` | 4096 | 当提供商计数省略或低估图像成本时，为每张图像预留的 token |
**补丁扩展逻辑**

| Key | Default | 说明 |
| --- | --- | --- |
| `patch_extension_skip_types` | [".md", ".txt"] |  |
| `allow_dynamic_context` | true |  |
| `max_extra_lines_before_dynamic_context` | 10 | 会尝试在补丁的 hunk 之前最多包含 10 行额外内容，直到到达包围它的函数或类 |
| `patch_extra_lines_before` | 5 | 在补丁的每个 hunk 之前包含的额外行数（另加默认的 3 行） |
| `patch_extra_lines_after` | 1 | 在补丁的每个 hunk 之后包含的额外行数（另加默认的 3 行） |
| `secret_provider` | "" | ""（禁用）、"google_cloud_storage" 或 "aws_secrets_manager"，用于安全的密钥管理 |
| `cli_mode` | false |  |
| `output_relevant_configurations` | false |  |
| `output_run_details` | false | 为 true 时，在生成的 PR 评论末尾追加代理运行详情部分（模型、token、时间成本、AI 调用） |
| `output_run_cost` | false | 为 true 时，采集估算的 LiteLLM API 费用，并把它包含进已启用的运行详情部分 |
| `large_patch_policy` | "clip" | "clip"、"skip" |
| `duplicate_prompt_examples` | false |  |
| `persistent_inline_comments` | false | 启用持久行内评论（issue #2037），为每条行内评论生成指纹并嵌入平台兼容的标记，然后在多次运行中跳过重新发布 PR/MR 上已经存在的建议。 |
**随机种子**

| Key | Default | 说明 |
| --- | --- | --- |
| `seed` | -1 | 设为正值以固定随机种子（并确保 temperature=0） |
| `temperature` | 0.2 |  |
**忽略逻辑**

| Key | Default | 说明 |
| --- | --- | --- |
| `ignore_pr_title` | ["^\\[Auto\\]", "^Auto"] | 用于匹配 PR 标题以忽略 PR agent 的正则表达式列表 |
| `ignore_pr_target_branches` | [] | 创建 PR 时，要从 PR agent 忽略的目标分支正则表达式列表 |
| `ignore_pr_source_branches` | [] | 创建 PR 时，要从 PR agent 忽略的源分支正则表达式列表 |
| `ignore_pr_labels` | [] | 创建 PR 时要从 PR agent 忽略的标签 |
| `ignore_pr_authors` | [] | 创建 PR 时要从 PR agent 忽略的作者 |
| `reaction_on_start` | "eyes" | 在命令运行之前添加 |
| `reaction_on_success` | "" | 命令成功时替换开始时的反应（GitHub App、GitLab webhook） |
| `reaction_on_failure` | "" | 命令失败时替换开始时的反应（GitHub App、GitLab webhook） |
| `ignore_repositories` | [] | 要从 PR agent 处理中忽略的仓库全名（例如 "org/repo"）正则表达式列表 |
| `ignore_language_framework` | [] | 代码生成语言或框架列表（例如 'protobuf'、'go_gen'），其自动生成的源文件将被排除在分析之外 |
| `bot_user_indicators` | ["codium", "bot_", "bot-", "_bot", "-bot"] | 用于在 webhook 事件上跳过机器人用户的子串指示符。目前由 GitLab webhook 使用（`is_bot_user`）；其他平台将来可能采用此列表。匹配对发送者显示名不区分大小写。覆盖此设置会替换默认列表——如果希望保留它们，请在覆盖中包含下面的条目（例如 `["codium", "bot_", "bot-", "_bot", "-bot", "renovate"]`）。 |
| `restricted_mode` | false | 为 true 时，跳过需要更高权限的操作（例如向仓库推送代码） |
| `is_auto_command` | false | 如果命令由自动化触发，会被自动设为 true |
| `propagate_tool_errors` | false | 为 true 时，工具会重新抛出而不是吞掉内部错误，以便调用方区分失败的运行和空的运行 |
| `enable_ai_metadata` | false | 将启用添加 AI 元数据 |
| `add_user_to_requests` | false | 在 OpenAI 兼容的 "user" 请求字段中发送当前命令和 PR URL，用于在提供商侧归因请求（例如 OpenRouter 的 "external_user"） |
| `reasoning_effort` | "medium" | "none"、"minimal"、"low"、"medium"、"high"、"xhigh"、"max" |
| `additional_reasoning_effort_models` | [] | 可选：额外接受 config.reasoning_effort 的模型 ID。否则，推理支持由 litellm 捆绑的模型元数据（以及维护中的 Grok 注册表）决定，因此当 litellm 不认识该模型（自定义 OpenAI 兼容端点），或另一提供商以同一 ID 托管 Sol 层级 GPT-6 模型时，在这里添加 ID。模型 ID 精确匹配，或通过任意提供商前缀匹配（例如 "deepseek-v4-flash-0731" 匹配 "openai/deepseek-v4-flash-0731"）。对于它不认识的 OpenAI 兼容模型，LiteLLM 通过 allowed_openai_params 将 reasoning_effort 列入白名单，因此该参数会到达端点。默认的 "medium" 可能被只接受不同子集（例如 "none"/"low"/"high"/"max"）的提供商拒绝；现在添加自定义模型 id 会暴露提供商侧错误，而不是像以前那样静默丢弃。 |
| `no_temperature_models` | ["deepseek/deepseek-reasoner", "o1-mini", "o1-mini-2024-09-12", "o1", "o1-2024-12-17", "o3-mini", "o3-mini-2025-01-31", "o3", "o3-2025-04-16", "o4-mini", "o4-mini-2025-04-16", "gpt-5.1-codex", "gpt-5.1-codex-mini", "gpt-5.2-codex", "gpt-5.3-codex", "gpt-5-mini"] | 可选：在 litellm 参数元数据所报告的内容之外，绝不能接收 temperature 参数的模型 ID。否则，温度支持由 litellm.get_supported_openai_params() 决定（与 reasoning_effort 的方式一致），因此当 litellm 报告支持温度但提供商拒绝它，或某个 OpenAI 兼容端点接受它但你仍希望丢弃它时，在这里添加 ID。自适应思考的 Claude 模型（Opus 4.7/4.8 以及 Opus/Sonnet/Fable 5）从不接收 temperature。精确匹配模型 ID，或通过任意提供商前缀匹配。对于 OpenRouter 的 `:nitro` 和 `:floor` 路由快捷方式，也匹配去掉后缀的基 ID（例如用 `future-model` 匹配 `openrouter/vendor/future-model:nitro`）。其他模型变体保持完整 ID。当 litellm 的元数据仍把它们标记为支持温度时，保留下面原先的静态注册表条目；探测差异见对应 issue。 |
**Claude 推理模型的扩展思考**

| Key | Default | 说明 |
| --- | --- | --- |
| `enable_claude_extended_thinking` | false | 设为 true 以启用扩展思考功能 |
| `extended_thinking_budget_tokens` | 2048 |  |
| `extended_thinking_max_output_tokens` | 4096 |  |
| `enable_claude_adaptive_thinking` | false | Claude Opus 4.7/4.8 和 Claude 5 模型的自适应思考。启用后，这些模型会收到 thinking={"type": "adaptive"} 以及 output_config effort。不要把仅支持自适应的模型加入 claude_extended_thinking_models_override；当两个功能都启用时，自适应思考优先。 |
| `claude_adaptive_thinking_models_override` | [] | 可选：额外当作仅支持自适应的 Claude 模型的模型 id 列表。在这里添加不透明的 Bedrock 应用推理配置 ARN，同时保留对具名模型的内置检测。启用自适应思考时，请使用精确的请求模型 id，以便 LiteLLM 保留自适应载荷，而不是把它转换成旧的 budget_tokens 形状。 |
| `claude_extended_thinking_models_override` | [] | 可选：覆盖接收扩展思考载荷的内置 Claude 模型列表。非空时，此列表完全替换内置默认值（见 pr_agent/algo/__init__.py 中的 CLAUDE_EXTENDED_THINKING_MODELS）。留空则使用默认值。 |
| `extract_issue_from_branch` | true | 从 PR 源分支名提取 issue 编号（例如 feature/1-auth-google -> issue #1）。为 true 时，从分支派生的 issue URL 会与 PR 描述中的工单合并，用于合规。设为 false 可恢复仅使用描述的行为。注意：分支名提取目前仅支持 GitHub；其他平台计划稍后支持。 |
| `branch_issue_regex` | "" | 可选：恰好有一个捕获组、用于 issue 编号的自定义正则（运行时校验；缺失时回退到默认）。为空时使用默认模式：分支开头或斜杠之后的前 1-6 位数字，后跟连字符或结尾（例如 feature/1-test、123-fix）。仅 GitHub；其他平台计划稍后支持。 |
| `description_issue_regex` | "" | 配置一个替换裸 #N 引用的正则，恰好有一个捕获组用于 ASCII issue 编号。留空则使用默认匹配（最多六位数字）；模式无效时给出警告并回退。在模式中设置自定义位数限制；只使用可解析为整数的捕获。保留完整 URL 和 owner/repo#N 引用。使用 TOML 字面引号以保留反斜杠，例如 description_issue_regex = '(?i)(?:fixes\|closes\|resolves)\s+#(\d+)' |


## `[pr_reviewer]` — /review {#pr_reviewer-review}

**启用/禁用功能**

| Key | Default | 说明 |
| --- | --- | --- |
| `require_score_review` | false |  |
| `require_tests_review` | true |  |
| `require_estimate_effort_to_review` | true |  |
| `require_can_be_split_review` | false |  |
| `require_security_review` | true |  |
| `require_estimate_contribution_time_cost` | false |  |
| `require_todo_scan` | false |  |
| `require_ticket_analysis_review` | true |  |
| `require_risk_assessment` | false | 要求模型给出总体风险级别（low/medium/high） |
| `require_merge_recommendation` | false | 要求模型给出合并建议（safe_to_merge/merge_with_caution/changes_required） |
| `require_priority_files` | false | 要求模型指出人工应该首先检查哪些文件 |
**通用选项**

| Key | Default | 说明 |
| --- | --- | --- |
| `publish_output_no_suggestions` | true | 如果只需要审查者的评语（不要标签、不要 "security audit" 等），并希望避免嘈杂的 "No major issues detected" 评论，请设为 "false"。 |
| `publish_review_failure_comment` | true | 设为 false 可抑制审查失败评论，而不改变命令的失败状态。 |
| `publish_error_details` | false | 在手动审查评论中发布确定的、已脱敏的失败原因。不使用 AI 调用。 |
| `persistent_comment` | true |  |
| `review_heading` | "PR Reviewer Guide" | 完整审查和增量审查评论的可见基础标题。身份另行跟踪。 |
| `persistent_finding_state` | true | 在完整的审查运行之间持久化审查发现状态。 |
| `max_previous_findings_chars` | 8000 | 先前审查所存储发现的字符预算，作为上下文提供给 /review，以便它保持原有措辞而不是换种说法重新提出，并跳过其 GitLab 行内讨论已被人工解决的发现（需要 persistent_finding_state）；0 表示禁用。 |
| `inline_key_issues` | false | 在平台能够验证行内评论发布的地方（GitHub、Bitbucket Cloud、Azure DevOps、GitLab），把每条审查发现发布为行内评论。 |
| `extra_instructions` | "" |  |
| `num_max_findings` | 3 |  |
| `final_update_message` | true |  |
**审查标签**

| Key | Default | 说明 |
| --- | --- | --- |
| `enable_review_labels_security` | true |  |
| `enable_review_labels_effort` | true |  |
**增量审查（/review -i）的专用配置**

| Key | Default | 说明 |
| --- | --- | --- |
| `require_all_thresholds_for_incremental_review` | false |  |
| `minimal_commits_for_incremental_review` | 0 |  |
| `minimal_minutes_for_incremental_review` | 0 |  |
| `enable_intro_text` | true |  |
| `enable_help_text` | false | 决定是否在 PR 审查中包含帮助文本。 |
| `enable_review_coverage_footer` | true |  |
| `enable_large_pr_chunking` | false | 大型 diff 分块（可选启用）。当 token 预算使一些文件无法进入审查时，把 diff 分成多块，分别审查每一块，再把各块结果合并成一次审查。 |
| `max_number_of_calls` | 3 | 分块审查调用的最大次数，仅在 enable_large_pr_chunking 为 true 时使用 |


## `[pr_description]` — /describe {#pr_description-describe}

| Key | Default | 说明 |
| --- | --- | --- |
| `publish_labels` | false |  |
| `add_original_user_description` | true |  |
| `generate_ai_title` | false |  |
| `extra_instructions` | "" |  |
| `enable_pr_type` | true |  |
| `enable_pr_description` | true | 添加一个包含 PR 变更的 AI 生成摘要的部分 |
| `final_update_message` | true |  |
| `enable_help_text` | false |  |
| `enable_help_comment` | false |  |
| `enable_pr_diagram` | true | 添加一个包含 PR 变更示意图的部分 |
| `pr_diagram_direction` | "adaptive" | 'adaptive'、'LR'、'TD'。'adaptive' 根据示意图的形状选择方向 |
| `pr_diagram_direction_threshold` | 5 | 使用 'adaptive' 时，长于这么多个节点的链会自上而下绘制 |
**以评论形式描述**

| Key | Default | 说明 |
| --- | --- | --- |
| `publish_description_as_comment` | false |  |
| `publish_description_as_comment_persistent` | true |  |
**变更走查部分**

| Key | Default | 说明 |
| --- | --- | --- |
| `enable_semantic_files_types` | true |  |
| `collapsible_file_list` | "adaptive" | true、false、'adaptive' |
| `collapsible_file_list_threshold` | 6 |  |
| `file_table_collapsible_open_by_default` | false |  |
**标记**

| Key | Default | 说明 |
| --- | --- | --- |
| `use_description_markers` | false |  |
| `enable_large_pr_handling` | true |  |
| `include_generated_by_header` | true |  |
| `max_ai_calls` | 4 |  |
| `async_ai_calls` | true |  |


## `[pr_questions]` — /ask {#pr_questions-ask}

| Key | Default | 说明 |
| --- | --- | --- |
| `enable_help_text` | false |  |
| `use_conversation_history` | true |  |
| `ask_heading` | "Ask" | 设置顶层 /ask 回答的纯文本标题；特定于平台的呈现会自动添加。 |
| `resolve_threads` | false | 启用后，当 LLM 判断问题已解决时，让 /ask_line 解决该审查讨论串。注意：也会解决由人工审查者发起的讨论串。 |
| `extra_instructions` | "" |  |


## `[pr_code_suggestions]` — /improve {#pr_code_suggestions-improve}

| Key | Default | 说明 |
| --- | --- | --- |
| `committable_code_suggestions` | false | 仍被接受直到 1.0 的已弃用别名：pr_code_suggestions.commitable_code_suggestions |
| `dual_publishing_score_threshold` | -1 | -1 表示禁用，[0-10] 用于设置同时在表格中和作为可提交建议发布代码建议的阈值（>=） |
| `focus_only_on_problems` | true |  |
| `extra_instructions` | "" |  |
| `suggestions_heading` | "PR Code Suggestions" | 摘要表格形式的 /improve 评论的可见基础标题。身份另行跟踪。 |
| `enable_help_text` | false |  |
| `enable_chat_text` | false |  |
| `persistent_comment` | true |  |
| `max_history_len` | 4 |  |
| `publish_output_no_suggestions` | true |  |
| `enable_suggestions_coverage_footer` | true | 显示失败的块以及因 token 或 AI 调用预算而被省略的文件 |
**建议评分**

| Key | Default | 说明 |
| --- | --- | --- |
| `suggestions_score_threshold` | 0 | [0-10]\| 建议不要把此值设到 8 以上，因为高于它可能会裁掉高度相关的建议 |
| `score_on_reflection_failure` | 7 | [0-10]\| 自我反思失败或其反馈无法解析时赋予的分数；设为低于 suggestions_score_threshold 可丢弃未经核验的建议 |
| `new_score_mechanism` | true |  |
| `new_score_mechanism_th_high` | 9 |  |
| `new_score_mechanism_th_medium` | 7 |  |
**'/improve --extended' 模式的参数**

| Key | Default | 说明 |
| --- | --- | --- |
| `num_code_suggestions_per_chunk` | 3 |  |
| `max_suggestions_per_file` | 0 | 所有块合并之后每个文件保留的建议数量上限；0 表示禁用该上限。对摘要输出应用正的上限之前，先跳过无法解析的行位置；行内选择保持不变。 |
| `max_discussion_context_chars` | 24000 | 作为上下文提供给 /improve 的先前代码建议讨论的字符预算（GitLab、Azure DevOps）；0 表示禁用。 |
| `max_number_of_calls` | 3 |  |
| `parallel_calls` | true |  |
| `decouple_hunks` | false |  |
**自查复选框**

| Key | Default | 说明 |
| --- | --- | --- |
| `demand_code_suggestions_self_review` | false | 为作者添加一个复选框，让其自行复查代码建议 |
| `code_suggestions_self_review_text` | "**Author self-review**: I have reviewed the PR code suggestions, and addressed the relevant ones." |  |
| `approve_pr_on_self_review` | false | 无效果：自查复选框只是视觉标记，PR-Agent 不会批准 PR（见 improve 文档和 FAQ） |
| `fold_suggestions_on_self_review` | true | 无效果：自查复选框只是视觉标记，勾选后建议不会被折叠 |


## `[pr_add_docs]` — /add_docs {#pr_add_docs-add_docs}

| Key | Default | 说明 |
| --- | --- | --- |
| `extra_instructions` | "" |  |
| `docs_style` | "Sphinx" | "Google Style with Args, Returns, Attributes...etc"、"Numpy Style"、"Sphinx Style"、"PEP257"、"reStructuredText" |


## `[pr_update_changelog]` — /update_changelog {#pr_update_changelog-update_changelog}

| Key | Default | 说明 |
| --- | --- | --- |
| `push_changelog_changes` | false |  |
| `extra_instructions` | "" |  |
| `add_pr_link` | true |  |
| `skip_ci_on_push` | true |  |


## `[pr_config]` — /config {#pr_config-config}

_本节只记录被注释掉的示例；详情见 [TOML 源文件](https://github.com/the-pr-agent/pr-agent/blob/main/pr_agent/settings/configuration.toml)。_

## `[pr_help_docs]` {#pr_help_docs}

| Key | Default | 说明 |
| --- | --- | --- |
| `repo_url` | "" | 如果未被覆盖，将使用上下文所来自的仓库（issue 或 PR） |
| `repo_default_branch` | "main" |  |
| `docs_path` | "docs" |  |
| `exclude_root_readme` | false |  |
| `supported_doc_exts` | [".md", ".mdx", ".rst"] |  |
| `enable_help_text` | false |  |


## `[github]` {#github}

| Key | Default | 说明 |
| --- | --- | --- |
| `deployment_type` | "user" | 要创建的部署类型。有效值为 'app' 或 'user'。 |
| `ratelimit_retries` | 5 |  |
| `seconds_between_requests` | 0 | API 请求之间的秒数；0 = 不限速（1.59 的行为） |
| `seconds_between_writes` | 0 | 写调用之间的秒数；0 = 不限速（1.59 的行为） |
| `api_retries` | 0 | 每个请求带退避的最大重试次数；0 = 不重试（1.59 的行为） |
| `polling_request_timeout` | 10 | 评论历史回退的总秒数；正值上限为 60 |
| `base_url` | "https://api.github.com" |  |
| `try_fix_invalid_inline_comments` | true |  |
| `ignore_bot_pr` | true |  |
| `publish_as_check_run` | false | 为 true 时，把 review/description/improve 输出发布为 GitHub Checks，而不是 PR 评论 |


## `[github_action_config]` {#github_action_config}

_本节只记录被注释掉的示例；详情见 [TOML 源文件](https://github.com/the-pr-agent/pr-agent/blob/main/pr_agent/settings/configuration.toml)。_

## `[github_app]` {#github_app}

| Key | Default | 说明 |
| --- | --- | --- |
| `override_deployment_type` | true | 这些开关允许从自定义部署运行 github app |
**"pull_request" 事件的设置**

| Key | Default | 说明 |
| --- | --- | --- |
| `handle_pr_actions` | ["opened", "reopened", "ready_for_review"] |  |
| `feedback_on_draft_pr` | false |  |
| `review_states` | ["changes_requested"] | 已提交的 GitHub 审查可以选择性触发这些命令。空的默认值保持当前行为。 |
| `review_author_types` | ["User"] |  |
| `review_commands` | [] |  |
| `webhook_delivery_deduplication` | false | 选择启用按每个 worker 进程内的 X-GitHub-Delivery 进行内存去重。进行中的工作保持受保护；已完成的 ID 在部署的 push_trigger_pending_tasks_ttl 之后过期（启动时读取，默认 300 秒）。失败或已取消的工作可以立即重试。重复投递不会延长 TTL。在此窗口内，手动重新投递也会被抑制。状态在重启时清除，并且不在 worker 或副本之间共享。 |
| `handle_push_trigger` | false | 针对动作为 "synchronize" 的 "pull_request" 事件的设置——用于检测并处理新提交的推送触发 |
| `push_trigger_ignore_bot_commits` | true |  |
| `push_trigger_ignore_merge_commits` | true |  |
| `push_trigger_pending_tasks_backlog` | true |  |
| `push_trigger_pending_tasks_ttl` | 300 |  |
| `push_commands` | ["/describe", "/review"] |  |


## `[gitlab]` {#gitlab}

| Key | Default | 说明 |
| --- | --- | --- |
| `url` | "https://gitlab.com" |  |
| `expand_submodule_diffs` | false | 子模块目标也必须列在 config.repo_context_sibling_repos 中。 |
| `feedback_on_draft_pr` | false |  |
| `publish_review_as_thread` | false | 把 /review 摘要发布为可解决的讨论串（discussion），而不是普通评论。 |
| `publish_improve_as_thread` | false | 把 /improve 建议评论发布为可解决的讨论串（discussion），而不是普通评论。 |
| `reply_to_trigger_comment` | false | 在 GitLab 上，当讨论 ID 可用时，把 `/review` 和 `/improve` 的输出回复到触发评论所在的讨论。 |
| `publish_code_suggestions_as_review` | false | 当 pr_code_suggestions.committable_code_suggestions 为 true 时，把每条建议排成 GitLab 草稿评论，并一次性成批发布（类似 GitLab 自己的“开始审查”流程），而不是一创建就各自发布为实时讨论——以及各自的通知。 |
| `resolve_outdated_inline_threads` | false | 解决机器人自己的、被后续推送留在过时 diff 版本上的行内讨论串。 |
| `auto_resolve_fixed_inline_threads` | false | 解决机器人自己的、其被标记的行在评论发布之后被修改的行内讨论串——即评论的 head sha 与当前 head sha 之间的 diff 删除/替换了该行。与 resolve_outdated_inline_threads 不同，这是基于内容的：没人碰过的行上的讨论串（或只是因无关插入而位移的行）保持打开。 |
| `handle_push_trigger` | false |  |
| `push_commands` | ["/describe", "/review"] |  |
| `handle_reviewer_assignment` | false | 当机器人被指定为 MR 的审查者时自动触发命令 |
| `reviewer_commands` | ["/review"] |  |


## `[gitea]` {#gitea}

| Key | Default | 说明 |
| --- | --- | --- |
| `url` | "https://gitea.com" |  |
| `handle_push_trigger` | false |  |
| `push_commands` | ["/describe", "/review"] |  |


## `[gitee]` {#gitee}

| Key | Default | 说明 |
| --- | --- | --- |
| `url` | "https://gitee.com" |  |
| `personal_access_token` | "" | Gitee 个人访问令牌。优先使用 pr_agent/settings/.secrets.toml 中的 GITEE.PERSONAL_ACCESS_TOKEN 或 GITEE__PERSONAL_ACCESS_TOKEN 环境变量，而不是把令牌存放在这里。 |
| `repo_setting` | ".pr_agent.toml" | 仓库设置文件的路径，从拉取请求的目标分支读取。 |
| `skip_ssl_verification` | false |  |


## `[bitbucket]` {#bitbucket}

| Key | Default | 说明 |
| --- | --- | --- |
| `identity_request_timeout` | 30 | 已认证账号验证请求的正数秒数 |


## `[bitbucket_app]` {#bitbucket_app}

| Key | Default | 说明 |
| --- | --- | --- |
| `avoid_full_files` | false |  |
| `request_timeout` | 30 | 连接超时和响应读取空闲超时的正数秒数 |


## `[local]` {#local}

_本节只记录被注释掉的示例；详情见 [TOML 源文件](https://github.com/the-pr-agent/pr-agent/blob/main/pr_agent/settings/configuration.toml)。_

## `[gerrit]` {#gerrit}

| Key | Default | 说明 |
| --- | --- | --- |
| `webhook_username` | "" | 两者都必填：在设置它们之前，gerrit webhook 端点会拒绝每一次调用 |
| `webhook_password` | "" |  |


## `[bitbucket_server]` {#bitbucket_server}

| Key | Default | 说明 |
| --- | --- | --- |
| `url` | "" | BitBucket Server 实例的 URL |


## `[jira]` {#jira}

| Key | Default | 说明 |
| --- | --- | --- |
| `jira_requirements_field` | "" | 存放验收标准/需求的自定义字段 id，映射到工单的 "requirements" 部分。特定于实例（例如 "customfield_10127"）；空值则禁用。 |
| `project_keys` | [] | 可选的 Jira 项目键允许列表，例如 ["PROJ", "OPS"]。非空时，带有其他前缀的、形状像键的文本（"SHA-256"、"UTF-8"、"ISO-8601"）会在任何查找之前被丢弃，因此不再每次花费一次已认证的 404。条目必须是纯大写键；提供的列表如果没有有效条目，会禁用查找而不是放宽它。空（默认）会查找找到的每一个键。与 jira_site 和 jira_api_email 一样仅主机侧：仓库设置和评论参数不能更改它们。 |


## `[litellm]` {#litellm}

| Key | Default | 说明 |
| --- | --- | --- |
| `enable_callbacks` | false |  |
| `success_callback` | [] |  |
| `failure_callback` | [] |  |
| `service_callback` | [] |  |
| `turn_off_message_logging` | false | 设为 true 可使提示词/响应内容（整个 PR diff）不进入回调载荷；强烈建议与 "otel" 回调一起使用 |
| `custom_llm_provider` | "" | 可选：向 LiteLLM 转发固定的 custom_llm_provider，以便原始的托管模型 id（例如 "claude-sonnet-4-5"）原样到达提供商，而不是被 LiteLLM 的前缀推断改写。空 = 让 LiteLLM 根据模型名推断提供商。 |
| `force_streaming_custom_llm_provider` | "" | 当请求匹配此提供商且其 api_base 包含下面的某个子串时强制流式传输。某些 OpenAI 兼容端点会返回 LiteLLM 在非流式模式下无法规范化的响应。两者都必须设置，该变通方法才会应用。 |
| `force_streaming_api_base_substrings` | [] |  |
| `callback_timeout_seconds` | 30 | 退出前等待待处理 litellm 回调刷新的最大秒数 |
| `base_models` | {} | 可选：把不透明的请求模型 id（例如 Bedrock 应用推理配置 ARN）映射到有 LiteLLM 定价的模型 id，以便报告运行费用而不是不可用。默认为空；具名模型由 LiteLLM 直接定价，这里不需要条目。 |
| `cache_control_injection_points` | [] | 可选：通过 LiteLLM 启用 Anthropic 提示词缓存，例如 [{location = "message", role = "system"}]（https://docs.litellm.ai/docs/tutorials/prompt_caching）。PR-Agent 只对名称包含 "claude" 或列在 Claude 思考覆盖中的模型转发这些点；LiteLLM 添加 cache_control 块。LiteLLM 自己的默认注入（litellm.enable_anthropic_prompt_caching，环境变量 LITELLM_ENABLE_ANTHROPIC_PROMPT_CACHING，默认关闭）只在这里没有配置这些点时应用，因此两者绝不会双重注入。当这些点无法生效时（非 Anthropic 模型、不支持提示词缓存，或前缀低于模型最小值），每个进程记录一次警告。 |


## `[openrouter]` {#openrouter}

| Key | Default | 说明 |
| --- | --- | --- |
| `provider_only` | [] | 把路由限制为仅这些上游提供商，一份硬性允许列表（例如 ["z-ai"]）；空 = OpenRouter 默认路由 |
| `provider_order` | [] | 首选提供商顺序；设置了 provider_only 时被忽略；空 = 未设置 |
| `allow_fallbacks` | true | 设置了 provider_order 时，允许路由到所列提供商之外 |
| `reasoning_effort` | "" | 无效的 reasoning_effort 值会被警告并视为未设置。空值对具备推理能力的模型继承 config.reasoning_effort（对照 litellm 捆绑的推理元数据或 Grok 注册表探测，或列在 additional_reasoning_effort_models 中）。有效值："none"、"minimal"、"low"、"medium"、"high"、"xhigh"、"max"。OpenRouter 把 "max" 规范化为 "xhigh"，以兼容 LiteLLM/OpenRouter。特定于模型的支持情况各不相同。对于 PR-Agent 的钳制未覆盖的模型，不要假定 "none" 会关闭推理；请检查所选模型和提供商的支持情况。 |
| `reasoning_max_tokens` | 0 | 使用正值可覆盖全局 effort 以及非 none 的 OpenRouter 专用 effort。对于显式的 openrouter.reasoning_effort = "none"，保持推理关闭，但 Grok 4.5/4.6、Gemini 3.7/3.8 Flash，以及其页面省略了 "none" 的 GPT-6 模型（GPT-6 Astra 和 GPT-6.1 Sol）除外。在应用预算之前，在那里把 "none" 钳制为最低受支持的 effort，因此正的预算会胜出。在提供商要求的地方，保持 max_tokens 大于推理预算。 |
| `max_tokens` | 0 | 请求的补全 token 硬上限；0 = 未设置 |


## `[model_routing]` — 将小型拉取请求发给更便宜的主模型（默认禁用） {#model_routing-send a small pull request to a cheaper primary model (disabled by default)}

| Key | Default | 说明 |
| --- | --- | --- |
| `enable` | false | 规则按顺序检查；第一个其限制能容纳该拉取请求的规则会为这次调用选择主模型，之后仍然应用 config.fallback_models。不符合任何规则的拉取请求使用 config.model。规模在 [ignore] 规则之后按 diff hunk（max_hunks）和已更改文件（max_files）衡量，每个 Git 平台都会报告这两者，并且不依赖任何模型的分词器。只有请求常规模型的调用会被路由（/review、/improve、/generate_labels、/add_docs）；使用 model_weak 的工具保持不变。使用 Azure（设置了 openai.deployment_id）时，规则还需要自己的 deployment_id，否则会被跳过。 |
| `rules` | [] | 例如 [{ max_hunks = 3, model = "gpt-5.6-luna" }, { max_hunks = 15, max_files = 6, model = "gpt-5.6-terra" }] |


## `[otel]` {#otel}

| Key | Default | 说明 |
| --- | --- | --- |
| `is_enabled` | false | 默认禁用；设为 true 以启用遥测 |
| `exporter_type` | "console" | "console"、"otlp"、"prometheus" 或 "none" |
| `service_name` | "pr-agent" |  |
| `environment` | "development" | "development"、"staging"、"production" 等。 |
| `otlp_timeout` | 3 | 秒；每次 OTLP 导出调用的硬截止时间（含重试）。当收集器不可达时，限制 CLI 退出/请求的停顿；慢于此时长的批次会被丢弃。 |
| `otlp_protocol` | "http" | "http"（默认；导出器随 pr-agent 一起提供）或 "grpc"（需要 otel-grpc extra：pip install pr-agent[otel-grpc]） |
| `prometheus_multiproc_dir` | "/tmp/pr-agent-prometheus" | prometheus 导出器按 worker 状态文件的共享目录；当 exporter_type = "prometheus" 时必需（多进程 gunicorn 部署）；以 0700 创建，并且必须保持由运行用户拥有（符号链接或属主不符的路径会被拒绝） |
| `include_pr_url` | false | 设为 true 可把 PR URL 附加到 span（可能暴露私有仓库名） |
| `include_error_details` | false | 设为 true 可把异常消息和被拒绝的命令文本附加到 span（可能暴露 PR URL、仓库名或其他请求内容） |


## `[pr_similar_issue]` {#pr_similar_issue}

| Key | Default | 说明 |
| --- | --- | --- |
| `skip_comments` | false |  |
| `force_update_dataset` | false |  |
| `max_issues_to_scan` | 500 |  |
| `vectordb` | "lancedb" | 选项："pinecone"、"lancedb"、"qdrant" |


## `[pinecone]` {#pinecone}

| Key | Default | 说明 |
| --- | --- | --- |
| `cloud` | "aws" | 现代 SDK 的无服务器索引部署。`cloud` 是 "aws"、"gcp" 或 "azure" 之一；选择该云提供的 `region`。 |
| `region` | "us-east-1" |  |


## `[lancedb]` {#lancedb}

| Key | Default | 说明 |
| --- | --- | --- |
| `uri` | "./lancedb" |  |


## `[qdrant]` {#qdrant}

_本节只记录被注释掉的示例；详情见 [TOML 源文件](https://github.com/the-pr-agent/pr-agent/blob/main/pr_agent/settings/configuration.toml)。_

## `[skills]` {#skills}

| Key | Default | 说明 |
| --- | --- | --- |
| `enabled` | false | Agent skills（SKILL.md）支持：从已配置的文件系统路径发现 SKILL.md 文件，并把它们的内容注入 review/improve/describe 以及顶层 /ask 提示词。技能目录树中的同级 *.md 文件（例如 references/guide.md）会与 SKILL.md 一起内联。PR-Agent 只支持纯文本技能：scripts/ 和 assets/ 子目录会被跳过，因为 PR-Agent 使用单次模型调用（没有工具使用循环），不能按需执行脚本或加载二进制资源。依赖脚本执行的技能在这里不会工作。见 https://github.com/The-PR-Agent/pr-agent/issues/2384 |
| `paths` | [] | 递归扫描 "*/SKILL.md" 的目录；支持 ~ 和 $VAR |
| `max_skills_tokens` | 8000 | 合并后的 skills_context 块的 token 预算 |


## `[artifacts]` {#artifacts}

| Key | Default | 说明 |
| --- | --- | --- |
| `enable` | false | 启用把产物注入工具提示词（默认关闭；设置了 artifact_path 输入时自动启用） |
| `artifact_path` | "" | 产物的文件路径（相对 GITHUB_WORKSPACE，或绝对路径） |
| `artifact_instructions` | "" | 在不受信任的产物标签和内容之前单独渲染的分析指引（留空则使用合理的默认值） |
| `artifact_label` | "" | 展示给 AI 的标签——为空时默认为文件名。 |
| `target_tools` | ["pr_reviewer", "pr_description", "pr_code_suggestions"] | 哪些受支持的工具接收产物上下文；不受支持的名称会被跳过并给出警告。 |
| `max_artifact_size` | 50000 | 产物的最大大小（字符数）（超出则截断内容） |


## `[mosaico]` {#mosaico}

| Key | Default | 说明 |
| --- | --- | --- |
| `bearer_tokens` | {} | 主体名称到互不相同的 bearer 密钥；空值允许匿名的受信任网络使用 |
| `routing_scan_max_chars` | 65536 | 用于检测 PR URL 和命令的正数字符限制；不会截断 diff |
| `health_timeout_seconds` | 10 | 协作式健康探测工作的有限正数秒数；不包括同步初始化和阻塞的 SDK 工作 |
| `context_history_max_tasks` | 100 | 上下文后续跟进所考虑的先前任务数量上限；设置范围为 1 到 1000 |


## `[asana]` {#asana}

| Key | Default | 说明 |
| --- | --- | --- |
| `request_timeout` | 10 | 每个 Asana 任务 API 请求允许的秒数 |


## `[azure_devops]` {#azure_devops}

| Key | Default | 说明 |
| --- | --- | --- |
| `default_comment_status` | "closed" |  |


## `[azure_devops_server]` {#azure_devops_server}

| Key | Default | 说明 |
| --- | --- | --- |
| `agent_identity` | "" | 空：从该 PR 上更早的代理评论中发现身份 |


## `[push_outputs]` — 将工具输出推送到外部接收端，而不调用 Git 平台 API（默认禁用） {#push_outputs-push tool outputs to external sinks without calling git-provider APIs (disabled by default)}

| Key | Default | 说明 |
| --- | --- | --- |
| `enable` | false |  |
| `channels` | [] | 以下任意项："stdout"、"file"、"webhook"、"slack"、"telegram"。在这里列出通道之前不会发出任何内容 |
| `file_path` | "pr-agent-outputs/reviews.jsonl" | 由 "file" 通道使用 |
| `webhook_url` | "" | 由 "webhook" 通道使用：通用 JSON POST 目标。必须是绝对的 https:// URL |
| `slack_webhook_url` | "" | 由 "slack" 通道使用：Slack Incoming Webhook URL。必须是绝对的 https:// URL |
| `telegram_bot_token` | "" | 由 "telegram" 通道使用；放在固定的 api.telegram.org URL 路径中 |
| `telegram_chat_id` | "" | 由 "telegram" 通道用作 sendMessage 的目标聊天 |
