---
title: "更换模型"
sidebar_position: 8
---

## 在 PR-Agent 中更换模型 {#changing-a-model-in-pr-agent}

PR-Agent 支持的模型列表见[这里](https://github.com/the-pr-agent/pr-agent/blob/main/pr_agent/algo/__init__.py)。
当前的默认模型和备用层级定义在[配置文件](https://github.com/the-pr-agent/pr-agent/blob/main/pr_agent/settings/configuration.toml)中。
要使用不同的模型，请编辑该文件中的这些字段：

```toml
[config]
model = "..."
fallback_models = ["..."]
```

要查看这些模型中实际处理了某个 PR 的是哪一个，请启用 `config.output_run_details`（参见[附加配置](./additional_configurations.md#showing-the-agent-run-details)）。
要把小型拉取请求发给更便宜的模型，参见[将小型拉取请求路由到更便宜的模型](#routing-small-pull-requests-to-a-cheaper-model)。

对于不是来自 OpenAI 的模型和环境，你可能需要提供额外的密钥和其他参数。
可以通过配置文件或环境变量提供参数。

:::note[特定于模型的环境变量]
各模型所需的环境变量见 [litellm 文档](https://litellm.vercel.app/docs/proxy/quick_start#supported-llms)，它们可能随时间变化。我们按模型编写的文档不一定始终与最新变更同步。
如果没有设置某个模型所需的密钥，通常会导致 litellm 无法识别模型类型，从而无法使用它。
:::

:::warning[凭据隔离边界]
PR-Agent 会按处理器捕获请求设置以及受支持的提供商环境值。部署方拥有的 LiteLLM 密钥管理器位于此请求隔离边界之外；它们的凭据不会被 PR-Agent 做快照。请在请求运行期间保持进程环境变量和 LiteLLM 全局变量稳定。处理器不会隔离嵌入方应用在请求期间所做的任意更改。当工作负载需要不同的、由部署方拥有的凭据来源，或可变的全局身份验证与路由状态时，请使用单独的进程。

诸如 `litellm.api_base`、`litellm.api_version`、`litellm.organization`、`litellm.vertex_project` 和 `litellm.vertex_location` 这类进程级路由回退，即使没有被修改也可能被拒绝。请使用对应的 PR-Agent 设置（`OPENAI.API_BASE`、`OPENAI.API_VERSION`、`OPENAI.ORG`、`VERTEXAI.VERTEX_PROJECT` 和 `VERTEXAI.VERTEX_LOCATION`）或受支持的提供商环境变量，并清除对应的 LiteLLM 全局变量，即使它们与预期路由一致。请使用 `LITELLM.EXTRA_HEADERS`，而不是 `litellm.headers`。
:::

### 类 OpenAI API

要使用类 OpenAI API，请在 `.secrets.toml` 文件中设置以下内容：

```toml
[openai]
api_base = "https://api.openai.com/v1"
api_key = "sk-..."
```

或使用环境变量（请务必使用双下划线 `__`）：

```bash
OPENAI__API_BASE=https://api.openai.com/v1
OPENAI__KEY=sk-...
```

### OpenAI Flex Processing

要为非紧急/后台任务降低成本，请启用 Flex Processing：

```toml
[litellm]
extra_body='{"service_tier": "flex"}'
```

详情参见 [OpenAI Flex Processing 文档](https://platform.openai.com/docs/guides/flex-processing)。

### 聊天模板选项

对于接受 `chat_template_kwargs` 的 OpenAI 兼容端点，例如
[提供 Qwen 的 vLLM 部署](https://docs.vllm.ai/en/latest/features/reasoning_outputs/)，
请通过现有的全局选项传入一个 JSON 对象：

```toml
[litellm]
extra_body='{"chat_template_kwargs": {"enable_thinking": false}}'
```

PR-Agent 会在请求体中发送该对象，并保留生成的 OpenRouter 路由、推理和请求归因字段。该设置适用于每一个已配置的模型，包括备用模型，因此仅当所有选中的端点都支持该字段时才使用它。现有的 `service_tier` 和 `processing_mode` 选项可以包含在同一个 JSON 对象中。

### Azure

要使用 Azure，请在 `.secrets.toml` 中设置（从 CLI 工作时），或在 GitHub 的 `Settings > Secrets and variables` 中设置（从 GitHub App 或 GitHub Action 工作时）：

```toml
[openai]
key = "" # your azure api key
api_type = "azure"
api_version = '2023-05-15'  # Check Azure documentation for the current API version
api_base = ""  # The base URL for your Azure OpenAI resource. e.g. "https://<your resource name>.openai.azure.com"
deployment_id = ""  # The deployment name you chose when you deployed the engine
```

并在配置文件中设置：

```toml
[config]
model="" # the OpenAI model you've deployed on Azure (e.g. gpt-4o)
fallback_models=["..."]
```

Azure AD 身份验证需要 `azure` extra（`pip install "pr-agent[azure]"`）。要使用基于 Azure AD（Entra id）的身份验证，请在 `.secrets.toml` 中设置（从 CLI 工作时），或在 GitHub 的 `Settings > Secrets and variables` 中设置（从 GitHub App 或 GitHub Action 工作时）：

```toml
[azure_ad]
client_id = ""  # Your Azure AD application client ID
client_secret = ""  # Your Azure AD application client secret
tenant_id = ""  # Your Azure AD tenant ID
api_base = ""  # Your Azure OpenAI service base URL (e.g., https://openai.xyz.com/)
```

请求局部的 Azure OIDC 桥会在处理器初始化时捕获 `AZURE_CLIENT_ID`、`AZURE_TENANT_ID`、`AZURE_AUTHORITY_HOST`、`AZURE_SCOPE`，以及与之竞争的 `AZURE_CLIENT_SECRET` / `AZURE_USERNAME` / `AZURE_PASSWORD` 设置。它在把配套凭据及其缓存身份绑定到所捕获的机构的同时，保留原生身份验证优先级；未提供机构时使用 Azure 公有云默认值，而空机构会被拒绝用于配套凭据。LiteLLM 的原生断言和密钥选择器仍然控制更新和来源选择；它们底层由部署方拥有的凭据链不是按请求隔离的。请把这些来源限定在预期的工作负载身份上，或为不同身份使用单独的进程。

对于除 Cloudflare 网关之外的原生 Azure SDK 路由，普通 AD 令牌使用相同的已捕获配套设置和 SDK 客户端缓存隔离。Azure Responses 路由也会把普通 AD 配套选择绑定到已捕获的设置。即使没有初始 AD 令牌，也可以选择完整的配套凭据，包括在原生 Azure AI 原始 HTTP 路由上。已捕获的配套提供方保留可调用的令牌刷新和原生身份验证优先级。如果 SDK 初始化或 Responses 令牌解析在 `enable_azure_ad_token_refresh=True` 时进入 LiteLLM 的隐式凭据发现，该请求会被拒绝：这一回退会重新读取进程级身份设置。请改为配置完整的客户端密钥或用户名/密码配套凭据。通过这一回退进行的托管身份、证书和默认凭据链发现被有意设为不受支持；已经缓存的、隔离的 SDK 客户端仍然可以在不进入发现的情况下被复用。

可以通过为 litellm 设置 extra_headers 参数，向底层 LLM Model API 传递自定义头。

```toml
[litellm]
extra_headers='{"projectId": "<authorized projectId >", ...}') #The value of this setting should be a JSON string representing the desired headers, a ValueError is thrown otherwise.
```

这使用户可以在通过 API 管理网关路由请求时传递授权令牌或 API 密钥。

原本会继承非空的进程级 `litellm.headers` 的请求会被拒绝，即使那些不是身份验证头；请改为通过 `LITELLM.EXTRA_HEADERS` 配置头。

### Ollama

你可以通过 [VLLM](https://docs.litellm.ai/docs/providers/vllm) 或 [Ollama](https://docs.litellm.ai/docs/providers/ollama) 在本地运行模型。

例如，要通过 Ollama 在本地使用一个新模型，请在 `.secrets.toml` 或配置文件中设置：

```toml
[config]
model = "ollama/qwen2.5-coder:32b"
fallback_models=["ollama/qwen2.5-coder:32b"]
custom_model_max_tokens=128000 # set the maximal input tokens for the model
duplicate_examples=true # will duplicate the examples in the prompt, to help the model to generate structured output

[ollama]
api_base = "http://localhost:11434" # or whatever port you're running Ollama on
```

默认情况下，Ollama 使用 2048 token 的上下文窗口。在大多数情况下，这不足以覆盖 pr-agent 的提示词和拉取请求 diff。可以用 `OLLAMA_CONTEXT_LENGTH` 环境变量覆盖上下文窗口大小。例如，要把默认上下文长度设为 8K，请使用：`OLLAMA_CONTEXT_LENGTH=8192 ollama serve`。更多信息见[官方 Ollama FAQ](https://docs.ollama.com/faq#how-can-i-specify-the-context-window-size)。

请注意，`custom_model_max_tokens` 设置应与 `OLLAMA_CONTEXT_LENGTH` 保持一致。否则可能导致意外的模型输出。

:::note[本地模型与商业模型]
PR-Agent 几乎兼容任何 AI 模型，但分析复杂的代码仓库和拉取请求需要专门为代码分析优化的模型。

GPT-5、Claude Sonnet 和 Gemini 等商业模型已经证明，它们能够针对大输入的代码分析任务稳健地生成结构化输出。相比之下，目前大多数开源模型（截至 2025 年 1 月）在这些复杂任务上面临困难。

根据我们的测试，本地开源模型适合实验和学习（主要是 `ask` 命令），但不适合生产级的代码分析任务。

因此，对于生产工作流和实际使用，我们建议使用商业模型。
:::

### Hugging Face

例如，要在 Hugging Face Inference Endpoints 上使用一个新模型，请设置：

```toml
[config] # in configuration.toml
model = "huggingface/meta-llama/Llama-2-7b-chat-hf"
fallback_models=["huggingface/meta-llama/Llama-2-7b-chat-hf"]
custom_model_max_tokens=... # set the maximal input tokens for the model

[huggingface] # in .secrets.toml
key = ... # your Hugging Face api key
api_base = ... # the base url for your Hugging Face inference endpoint
```

（你可以从[这里](https://replicate.com/replicate/llama-2-70b-chat/api)获取 Llama2 密钥）

### Replicate

例如，要在 Replicate 上使用 Llama2 模型，请设置：

```toml
[config] # in configuration.toml
model = "replicate/llama-2-70b-chat:2c1608e18606fad2812020dc541930f2d0495ce32eee50074220b87300bc16e1"
fallback_models=["replicate/llama-2-70b-chat:2c1608e18606fad2812020dc541930f2d0495ce32eee50074220b87300bc16e1"]
[replicate] # in .secrets.toml
key = ...
```

（你可以从[这里](https://replicate.com/replicate/llama-2-70b-chat/api)获取 Llama2 密钥）

另请查阅 [.secrets_template.toml](https://github.com/the-pr-agent/pr-agent/blob/main/pr_agent/settings/.secrets_template.toml) 文件，了解如何为其他模型设置密钥。

### Groq

例如，要在 Groq 上使用 Llama3 模型，请设置：

```toml
[config] # in configuration.toml
model = "llama3-70b-8192"
fallback_models = ["groq/llama3-70b-8192"]
[groq] # in .secrets.toml
key = ... # your Groq api key
```

（你可以从[这里](https://console.groq.com/keys)获取 Groq 密钥）

### SambaNova

例如，要在 SambaNova 上使用 MiniMax-M3 模型，请设置：

```toml
[config] # in configuration.toml
model = "sambanova/MiniMax-M3"
fallback_models = ["sambanova/MiniMax-M2.7"]
[sambanova] # in .secrets.toml
key = ... # your SambaNova api key
```

（你可以从[这里](https://cloud.sambanova.ai/apis)获取 SambaNova 密钥）

### xAI

要在 PR-Agent 中使用 xAI 的模型，请设置：

```toml
[config] # in configuration.toml
model = "xai/grok-4.6"
fallback_models = ["xai/grok-4.6"] # or any other model as fallback

[xai] # in .secrets.toml
key = "..." # your xAI API key
```

你可以从 [xAI 控制台](https://console.x.ai/)获取 xAI API 密钥：创建账号并进入开发者设置页面。

Grok 4.5 和 Grok 4.6 注册了 500K token 的上下文窗口（`xai/grok-4.5`、`xai/grok-4.5-latest`、`xai/grok-build-latest`、`xai/grok-4.6`、`openrouter/x-ai/grok-4.5`、`openrouter/x-ai/grok-4.6`）。xAI 为 Grok 4.5 发布了 `grok-4.5-latest` 和 `grok-build-latest` 别名；Grok 4.6 目前没有已发布的别名。

Grok 4.5 和 Grok 4.6 是始终开启的推理模型，并遵守 `config.reasoning_effort`（`low`、`medium`、`high`；Grok 4.6 及之后支持 `"xhigh"`）。PR-Agent 默认发送 `medium`；设为 `"high"` 可恢复 xAI 的原生默认值。该设置是全局的，因此更改它也会影响其他已注册的推理模型。不受支持的值会被钳制到最接近的可接受级别（`none`/`minimal` → `"low"`；Grok 4.5 上的 `"max"`/`"xhigh"` → `"high"`；Grok 4.6 上的 `"max"` → `"xhigh"`）。

OpenRouter 路由（`openrouter/x-ai/grok-4.5`、`openrouter/x-ai/grok-4.6`）会在解析 OpenRouter effort 值之后、在 none 与预算的决策之前，应用同样的钳制。显式的 `openrouter.reasoning_effort` 会覆盖全局 effort；正的 `openrouter.reasoning_max_tokens` 仍然只表示预算，并会抑制 effort，包括被钳制后的 `"none"` 值。`:nitro` 这类路由后缀需要 `custom_model_max_tokens`，因为 token 查找目前使用精确的模型 ID。

### Vertex AI

Vertex AI 需要 `google` extra（`pip install "pr-agent[google]"`）。要使用 Google 的 Vertex AI 平台及其相关模型（chat-bison/codechat-bison），请设置：

```toml
[config] # in configuration.toml
model = "vertex_ai/codechat-bison"
fallback_models="vertex_ai/codechat-bison"

[vertexai] # in .secrets.toml
vertex_project = "my-google-cloud-project"
vertex_location = ""
```

身份验证会使用你的[应用默认凭据](https://cloud.google.com/docs/authentication/application-default-credentials)，因此在大多数环境中无需设置显式凭据。

如果确实要设置显式凭据，可以使用 `GOOGLE_APPLICATION_CREDENTIALS` 环境变量，将其设为 JSON 凭据文件的路径。

每个处理器都会捕获所选的 Cloud SDK ADC 文件及其资源项目配置，包括 `CLOUDSDK_CONFIG`、当前命名配置和 `CLOUDSDK_CORE_PROJECT`。之后的更改作用于新的处理器，而不是已有的处理器。配额项目与资源项目保持分开。如果初始化时不存在 ADC 文件，处理器会保留托管运行时发现，而不会采用之后才创建的文件。

由 AWS 支持的 Vertex 工作负载身份联合会按处理器捕获环境凭据和区域。不同的已捕获身份即使共享同一 WIF 配置，也会使用分开的凭据缓存；相同的快照可以复用缓存条目。由元数据支持的凭据会继续通过所捕获的元数据来源刷新。

带有可执行来源的 Vertex 外部账号凭据被有意设为不受支持，包括当 `GOOGLE_EXTERNAL_ACCOUNT_ALLOW_EXECUTABLES=1` 时。该辅助程序及其缓存输出可能在处理器捕获配置之后改变身份，因此 Vertex 请求会在将其用于身份验证之前拒绝这一来源。请改用为预期身份配置的、非可执行的凭据来源；对于受支持的来源，正常的凭据刷新仍然启用。

### Google AI Studio

要使用 [Google AI Studio](https://aistudio.google.com/) 模型，请在配置文件的配置部分设置相关模型：

```toml
[config] # in configuration.toml
model="gemini/gemini-3.8-flash"
fallback_models=["gemini/gemini-3.8-flash"]

[google_ai_studio] # in .secrets.toml
gemini_api_key = "..."
```

如果不想在 .secrets.toml 文件中设置 API 密钥，可以设置 `GOOGLE_AI_STUDIO.GEMINI_API_KEY` 环境变量。

### Anthropic

要使用 Anthropic 模型，请在配置文件的配置部分设置相关模型：

```toml
[config]
model="anthropic/claude-opus-5"
fallback_models=["anthropic/claude-opus-5"]
```

并在 .secrets.toml 文件中设置 API 密钥：

```toml
[anthropic]
KEY = "..."
```

关于 Anthropic 所需环境变量的更多信息，见 [litellm](https://docs.litellm.ai/docs/providers/anthropic#usage) 文档。

### Amazon Bedrock

要使用 Amazon Bedrock 及其基础模型，请添加以下配置：

```toml
[config] # in configuration.toml
model="bedrock/anthropic.claude-3-5-sonnet-20240620-v1:0"
fallback_models=["bedrock/anthropic.claude-3-5-sonnet-20240620-v1:0"]

[aws]
AWS_ACCESS_KEY_ID="..."
AWS_SECRET_ACCESS_KEY="..."
AWS_REGION_NAME="..."
```

你也可以使用 Amazon Bedrock 上新的 Meta Llama 4 模型：

```toml
[config] # in configuration.toml
model="bedrock/us.meta.llama4-scout-17b-instruct-v1:0"
fallback_models=["bedrock/us.meta.llama4-maverick-17b-instruct-v1:0"]
```

Kimi K3 也可在 Amazon Bedrock 上使用：

```toml
[config] # in configuration.toml
model="bedrock/moonshotai.kimi-k3"
fallback_models=["bedrock/us.moonshotai.kimi-k3"]
```

在可以直接使用的地方使用裸的 `bedrock/moonshotai.kimi-k3` id，用 `us.` 跨区域前缀在美国各区域之间路由，或用 `global.` 前缀让 Bedrock 在所有受支持的区域之间路由。要通过 Bedrock Converse API 而不是经典运行时调用它，请给模型 id 加上 `bedrock/converse/` 前缀，例如 `bedrock/converse/us.moonshotai.kimi-k3`。

Grok 4.3 通过 Amazon Bedrock Mantle 提供，而不是经典 Bedrock 运行时：

```toml
[config] # in configuration.toml
model="bedrock_mantle/xai.grok-4.3"
fallback_models=["bedrock_mantle/xai.grok-4.3"]
```

Bedrock Mantle 使用相同的 AWS 凭据来源，但其 IAM 权限与经典运行时不同。参见 [AWS Mantle 推理权限](https://docs.aws.amazon.com/bedrock/latest/userguide/inference.html)。

#### 使用 IAM 角色凭据（在 AWS 计算环境上推荐）

在 AWS 基础设施（EC2、ECS/Fargate、带 IRSA 的 EKS、Lambda，或 AWS 上任何自托管的 GitHub Actions 运行器）上运行 PR-Agent 时，实例或任务已经附加了 IAM 角色。你可以直接使用这些环境凭据，而不必存储长期静态密钥。

在环境中设置 `AWS_USE_IMDS=true`。PR-Agent 会通过 boto3 的标准提供方链解析凭据，它会透明地处理所有 AWS 计算环境：

| 计算环境 | 机制 |
|---|---|
| 带 IAM 角色的 EC2 实例 | IMDSv2 (169.254.169.254) |
| ECS / Fargate 任务角色 | 任务元数据端点 |
| 带 IRSA 的 EKS Pod | Web 身份令牌 + STS |
| Lambda 函数 | 运行时注入的凭据 |

凭据发现在处理器初始化期间运行。在每个符合条件的 SigV4 请求之前，会在后台线程中通过同一个 boto3 凭据对象进行刷新。非 AWS 请求以及使用 bearer 身份验证的请求不会触发这次刷新。PR-Agent 把请求局部的快照传给 LiteLLM，而不会把凭据写入进程环境。构造时的发现和凭据文件指纹仍然是同步的。

使用此提供方链的 AWS 调用在一个处理器内保持串行，包括任何静态凭据重试。取消请求不会停止已经在运行的 boto3 刷新，但其结果不能覆盖处理器的凭据或静态回退决策。另一把锁会串行化 SDK 刷新，包括已取消调用方尚未完成的工作。刷新使用事件循环共享的默认执行器：被阻塞的操作，以及在反复取消之后等待 SDK 锁的 worker，可能会延迟无关的执行器工作和进程关闭。这里没有引入服务级的 worker 配额或额外的 SDK 超时。

其他 boto3 提供方链来源也需要同样的选择启用，包括 `AWS_PROFILE` 和共享凭据文件。不支持 LiteLLM 专用的 `AWS_PROFILE_NAME` 和 `AWS_ROLE_NAME` 选择器，因为它们可以覆盖请求局部的凭据；请取消设置它们，并改用 `AWS_USE_IMDS=true`。

从隐式的 LiteLLM 凭据链发现升级时，请显式设置 `AWS_USE_IMDS=true`。没有这一选择启用时，PR-Agent 只使用设置中的完整静态凭据，或处理器初始化时捕获的环境凭据；它不会让 LiteLLM 在请求时发现角色或配置文件。

对于经典 Bedrock，受支持的模型 ARN 会在环境/设置中的区域之前提供请求区域，包括在静态凭据重试期间。Converse 也会使用已捕获的 `litellm.model_id` ARN，或在 `model_id` 缺失时使用区域/模型路径；Invoke 不会从单独的 `model_id` 推导其区域。否则，在没有 `AWS_USE_IMDS=true` 时，请设置 `aws.AWS_REGION_NAME`、`AWS_REGION_NAME`、`AWS_REGION` 或 `AWS_DEFAULT_REGION`。仅有完整的环境凭据并不会启用从 boto3 配置文件或 LiteLLM 默认区域进行的区域发现。`[aws]` 中的静态凭据仍然需要 `AWS_REGION_NAME`。

对于没有 IMDS 或完整静态凭据的 Bedrock Mantle，区域来自 `BEDROCK_MANTLE_REGION`、`AWS_REGION_NAME`、`aws.AWS_REGION_NAME` 或 `AWS_REGION`，然后默认为 `us-east-1`；仅有 `AWS_DEFAULT_REGION` 不会改变该默认值。标准主机 `https://bedrock-mantle.<region>.api.aws` 上的 `BEDROCK_MANTLE_API_BASE` 会提供区域并覆盖这些来源；自定义端点主机则不会。完整的静态凭据和已选择启用的 boto3 发现仍遵循上文描述的 AWS 区域策略。

没有 `AWS_USE_IMDS=true` 时，环境身份验证遵循 LiteLLM 对 `AWS_SESSION_TOKEN` 的选择。旧的 `AWS_SECURITY_TOKEN` 别名只被已选择启用的 boto3 链识别；当两者都非空时，该链优先使用它而不是 `AWS_SESSION_TOKEN`。

Bedrock bearer 令牌必须来自处理器捕获的凭据，而不是进程级的 LiteLLM 回退，并且对于 `sagemaker_chat` 和 `sagemaker_nova` 路由，必须取消设置 `AWS_BEARER_TOKEN_BEDROCK`。

在 `AWS_USE_IMDS=true` 下通过配置文件解析凭据时，PR-Agent 不会执行所选配置文件或其 `source_profile` 链中的 `credential_process`。如果配置了这样的进程，PR-Agent 会改为使用 `[aws]` 中的完整静态凭据（`AWS_ACCESS_KEY_ID`、`AWS_SECRET_ACCESS_KEY` 和 `AWS_REGION_NAME`，需要时再加上 `AWS_SESSION_TOKEN`）；没有它们时，凭据解析会失败。使用在处理器初始化时捕获的完整环境凭据时，此限制不适用。

由 `AWS_WEB_IDENTITY_TOKEN_FILE`、配置文件的 `web_identity_token_file` 或 `AWS_CONTAINER_AUTHORIZATION_TOKEN_FILE` 选择的工作负载令牌文件必须由部署控制，而不能在租户之间切换。PR-Agent 保留从所选来源进行的原生令牌重新加载和凭据刷新；它不会冻结令牌内容，也不会检测同一路径上的内容被换成另一个身份。请为不同的工作负载身份使用分开控制的凭据来源和适当的进程/容器隔离，或提供显式的请求局部凭据。请求局部配置并不是针对同一进程中任意代码的隔离边界。

最小的 GitHub Actions 工作流（不需要 AWS 密钥）：

```yaml
- uses: the-pr-agent/pr-agent@main
  env:
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
    AWS_USE_IMDS: "true"
    # AWS_REGION_NAME: us-east-1  # optional if the instance metadata provides it
  with:
    command: review
```

IAM 角色必须对目标模型 ARN 拥有 `bedrock:InvokeModel` 权限，例如：

```json
{
  "Effect": "Allow",
  "Action": "bedrock:InvokeModel",
  "Resource": "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-5-sonnet-20240620-v1:0"
}
```

如果你还在 `[aws]` 中配置了静态密钥，当环境凭据无法解析，或使用已选择启用的提供方链的 SigV4 调用抛出速率限制错误以外的 API 错误时，它们会作为自动回退。这适用于 Bedrock、Bedrock Mantle 和 SageMaker 路由，并为 IAM 授权和连接失败保留现有的回退行为，且只使用处理器捕获的静态凭据。

#### 自定义推理配置

要使用经典 `bedrock/` 模型调用[应用推理配置](https://docs.aws.amazon.com/bedrock/latest/userguide/cost-mgmt-application-inference-profiles.html)（用于成本分配标签和其他配置设置），请在配置中把 `model_id` 设为该配置的 ARN：

```toml
[config] # in configuration.toml
model="bedrock/anthropic.claude-3-5-sonnet-20240620-v1:0"
fallback_models=["bedrock/anthropic.claude-3-5-sonnet-20240620-v1:0"]

[aws]
AWS_ACCESS_KEY_ID="..."
AWS_SECRET_ACCESS_KEY="..."
AWS_REGION_NAME="..."

[litellm]
model_id = "your-application-inference-profile-arn"
```

`litellm.model_id` 参数只适用于通过 `bedrock-runtime` API 发出的经典 `bedrock/` 调用。它不适用于 `bedrock_mantle/`；对于 Mantle Chat Completions 和 Responses API 的成本分配，请使用 [Amazon Bedrock Projects](https://docs.aws.amazon.com/bedrock/latest/userguide/cost-mgmt-projects.html)。

该配置只随 `config.model` 中设置的模型的请求发送。`config.fallback_models` 中的模型不会使用它，因此备用模型绝不会被路由到主模型的推理配置。

要给备用模型自己的应用推理配置，请把它列在 `litellm.model_ids` 中，以精确的模型名为键。`model_ids` 中的条目对该模型优先；当 `config.model` 没有条目时，`model_id` 仍然适用于它。两者都没有的模型不会获得配置。

```toml
[litellm]
model_ids = {"bedrock/anthropic.claude-3-5-sonnet-20240620-v1:0" = "your-primary-profile-arn", "bedrock/qwen.qwen3-235b-a22b-2507-v1:0" = "your-fallback-profile-arn"}
```

##### 使用 ARN 时的提示词缓存和运行费用

提示词缓存和运行费用估算按名称识别模型，因此不透明的应用推理配置 ARN 需要额外配置：

- 把该 ARN 加入 `claude_adaptive_thinking_models_override`（扩展思考则加入 `claude_extended_thinking_models_override`），以便 PR-Agent 将其视为 Claude 并转发 `cache_control_injection_points`。参见[使用应用推理配置 ARN 的 Claude 5 思考](#claude-5-thinking-with-an-application-inference-profile-arn)。
- 在 `[litellm] base_models` 中把该 ARN 映射到一个有 LiteLLM 定价的模型 id，这样运行费用会被估算，而不是报告为不可用：

```toml
[litellm.base_models]
"bedrock/converse/arn:aws:bedrock:eu-central-1:<account-id>:application-inference-profile/<profile-id>" = "bedrock/anthropic.claude-sonnet-4-5-20250929-v1:0"
```

#### 使用应用推理配置 ARN 的 Claude 5 思考 {#claude-5-thinking-with-an-application-inference-profile-arn}

Bedrock 上的 Claude Sonnet 5 通过推理配置调用，而不是直接的基础模型 id。当该配置是应用推理配置时，其 ARN 是不携带模型名的不透明值。把该 ARN 加入 `claude_adaptive_thinking_models_override`，以便 PR-Agent 和 LiteLLM 都把它当作自适应思考模型：

把该 ARN 用作模型 id，并在覆盖列表中重复这个精确值：

```toml
[config] # in configuration.toml
model = "bedrock/converse/arn:aws:bedrock:eu-central-1:<account-id>:application-inference-profile/<profile-id>"
enable_claude_adaptive_thinking = true
claude_adaptive_thinking_models_override = [
    "bedrock/converse/arn:aws:bedrock:eu-central-1:<account-id>:application-inference-profile/<profile-id>"
]
```

该覆盖是追加的，因此同一备用链中的具名 Claude 模型会继续使用内置检测。PR-Agent 还会向 LiteLLM 注册每个覆盖项，防止 LiteLLM 把自适应载荷转换成 Bedrock 会拒绝的旧式 `budget_tokens` 形状。

只有当后缀不透明时，ARN 才需要该覆盖。嵌入了模型系列的 ARN，例如 `...:inference-profile/us.anthropic.claude-sonnet-5`，会规范化成自适应正则已经匹配的字符串。

#### 使用自定义 VPC 端点（PrivateLink）

要把 Bedrock 流量路由到 VPC 接口端点，而不是公共的 `bedrock-runtime` 端点，请把 `AWS_BEDROCK_RUNTIME_ENDPOINT` 设为环境变量或写在 `[aws]` 中：

```toml
[aws]
AWS_BEDROCK_RUNTIME_ENDPOINT="https://bedrock-runtime.us-east-1.amazonaws.com"
```

关于 Amazon Bedrock 所需环境变量的更多信息，见 [litellm](https://docs.litellm.ai/docs/providers/bedrock#usage) 文档。

### DeepSeek

例如，要在 DeepSeek 上使用 deepseek-v4 模型，请设置：

```toml
[config] # in configuration.toml
model = "deepseek/deepseek-v4-pro"
fallback_models=["deepseek/deepseek-v4-flash"]
```

并填入你的密钥

```toml
[deepseek] # in .secrets.toml
key = ...
```

（你可以从[这里](https://platform.deepseek.com/api_keys)获取 deepseek-v4 密钥）

### GLM（Z.AI）

例如，要在 Z.AI（智谱）上使用 GLM 模型，请设置：

```toml
[config] # in configuration.toml
model = "zai/glm-5.2"
fallback_models=["zai/glm-5.2"]
```

并填入你的密钥

```toml
[zai] # in .secrets.toml
key = ...
```

（你可以从[这里](https://z.ai/)获取 Z.AI API 密钥）

### Kimi（Moonshot）

例如，要在 Moonshot 上使用 Kimi 模型，请设置：

```toml
[config] # in configuration.toml
model = "moonshot/kimi-k3"
fallback_models=["moonshot/kimi-k3"]
```

并填入你的密钥

```toml
[moonshot] # in .secrets.toml
key = ...
```

（你可以从[这里](https://platform.moonshot.ai/)获取 Moonshot API 密钥）

如果使用的是中国区端点，请在 `[moonshot]` 下添加 `api_base = "https://api.moonshot.cn/v1"`。

### Qwen（DashScope）

例如，要在阿里云 DashScope 上使用 Qwen 模型，请设置：

```toml
[config] # in configuration.toml
model = "dashscope/qwen3.8-max"
fallback_models=["dashscope/qwen3.8-max"]
```

并填入你的密钥

```toml
[dashscope] # in .secrets.toml
key = ...
```

（你可以从[这里](https://dashscope.console.aliyun.com/)获取 DashScope API 密钥）

### 小米 MiMo

例如，要使用小米 MiMo 模型，请设置：

```toml
[config] # in configuration.toml
model = "xiaomi_mimo/mimo-v2.5"
fallback_models=["xiaomi_mimo/mimo-v2.5"]
```

并填入你的密钥

```toml
[xiaomi_mimo] # in .secrets.toml
key = ...
```

（你可以从[这里](https://platform.xiaomimimo.com/#/docs)获取小米 MiMo API 密钥）

### DeepInfra

例如，要在 DeepInfra 上使用 DeepSeek 模型，请设置：

```toml
[config] # in configuration.toml
model = "deepinfra/deepseek-ai/DeepSeek-R1-Distill-Llama-70B"
fallback_models = ["deepinfra/deepseek-ai/DeepSeek-R1-Distill-Qwen-32B"]
[deepinfra] # in .secrets.toml
key = ... # your DeepInfra api key
```

（你可以从[这里](https://deepinfra.com/dash/api_keys)获取 DeepInfra 密钥）

### Mistral

例如，要在 Mistral 上使用 Mistral 或 Codestral 等模型，请设置：

```toml
[config] # in configuration.toml
model = "mistral/mistral-small-latest"
fallback_models = ["mistral/mistral-medium-latest"]
[mistral] # in .secrets.toml
key = "..." # your Mistral api key
```

（你可以从[这里](https://console.mistral.ai/api-keys)获取 Mistral 密钥）

### Codestral

例如，要在 Codestral 上使用 Codestral 模型，请设置：

```toml
[config] # in configuration.toml
model = "codestral/codestral-latest"
fallback_models = ["codestral/codestral-2405"]
[codestral] # in .secrets.toml
key = "..." # your Codestral api key
```

（你可以从[这里](https://console.mistral.ai/codestral)获取 Codestral 密钥）

### Databricks

要使用托管在 Databricks 上的模型（例如 Azure Databricks serving endpoint），请设置：

```toml
[config] # in configuration.toml
model = "databricks/databricks-claude-sonnet-4"
fallback_models = ["databricks/databricks-claude-sonnet-4"]
[databricks] # in .secrets.toml
api_key = "..." # your Databricks personal access token (PAT)
api_base = "https://adb-xxxx.azuredatabricks.net/serving-endpoints" # your workspace serving-endpoints URL
```

`databricks/` 前缀之后的模型名就是你的 serving endpoint 名称。详情见 LiteLLM 的 [Databricks 提供商文档](https://docs.litellm.ai/docs/providers/databricks)。

已配置的 PAT 和端点会按处理器捕获。当同时设置了 `DATABRICKS_CLIENT_ID` 和 `DATABRICKS_CLIENT_SECRET` 时，即使提供了 PAT，LiteLLM 也会执行 OAuth M2M 交换。交换失败可能中止请求；交换成功后，所提供的 PAT 会替换最终 Authorization 头中的 OAuth 令牌。没有 OAuth M2M 凭据或 PAT 时，可选的 Databricks SDK 身份验证仍然可用。这些由部署方拥有的凭据和配置文件选择不是按请求隔离的。不要在共享进程中于租户之间更改这些来源；请使用特定于请求的 PAT 并取消设置 OAuth M2M 凭据，或为不同的工作负载身份使用单独的进程。

### Openrouter

例如，要使用来自 Openrouter 的模型，请设置：

```toml
[config] # in configuration.toml
model="openrouter/anthropic/claude-sonnet-5"
fallback_models=["openrouter/deepseek/deepseek-chat"]
custom_model_max_tokens=20000

[openrouter]  # in .secrets.toml or passed an environment variable openrouter__key
key = "..." # your openrouter api key
```

（你可以从[这里](https://openrouter.ai/settings/keys)获取 Openrouter API 密钥）

OpenRouter 的路由器模型可以直接选择，无需设置 `custom_model_max_tokens`：

```toml
[config]
model = "openrouter/auto"
fallback_models = ["openrouter/free"]
```

PR-Agent 还注册了 `openrouter/fusion` 和 `openrouter/pareto-code`。提供商路由、推理和输出上限设置对这四个路由器模型都是可选的；省略它们即使用 OpenRouter 的默认值。参见 OpenRouter 关于 [Auto](https://openrouter.ai/docs/guides/routing/routers/auto-router)、[Free](https://openrouter.ai/docs/guides/routing/routers/free-router)、[Fusion](https://openrouter.ai/docs/guides/routing/routers/fusion-router) 和 [Pareto](https://openrouter.ai/docs/guides/routing/routers/pareto-router) 路由器的文档。

#### Openrouter 提供商路由、推理和输出上限

对于 `openrouter/...` 模型，你可以选择限制 Openrouter 使用哪些上游提供商、控制推理，并限制补全长度。所有键都位于 `configuration.toml` 的 `[openrouter]` 节。具备推理能力的模型，是指 litellm 捆绑的推理元数据在模型 id 及其带提供商前缀/`xai/` 形式上做了标记的模型、维护中的 Grok 注册表中的模型，或 `config.additional_reasoning_effort_models` 中的模型；除非设置了 Openrouter 专用的 effort 或 token 预算，否则它们继承 `config.reasoning_effort`。

```toml
[openrouter]
# Uncomment and adjust the keys you need; unset keys keep Openrouter's defaults.
# provider_only = ["z-ai"]             # hard allowlist of upstream providers; empty = default routing
# provider_order = ["z-ai", "novita"]  # preferred order instead of an allowlist; ignored when provider_only is set
# allow_fallbacks = true               # when provider_order is set, allow routing beyond the list
# reasoning_effort = "low"             # override global effort: "none", "minimal", "low", "medium", "high", "xhigh" or "max"
# reasoning_max_tokens = 2048          # explicit budget; ignored only when final effort remains "none"
# max_tokens = 16000                   # hard cap on completion tokens for the request
```

`provider_only` 和 `reasoning_effort = "none"` 可用于固定特定提供商，并限制推理模型的成本。因为 Openrouter 把 effort 和 token 预算视为互斥，当模型支持关闭推理时，显式的 Openrouter 专用 `"none"` 会保持推理关闭。Grok 4.5/4.6、Gemini 3.7/3.8 Flash，以及其页面省略了 `"none"` 的 GPT-6 模型（GPT-6 Astra 和 GPT-6.1 Sol）会在应用优先级之前把它钳制为 `"low"`，因此对这些模型，正的预算会胜出；显式的 Openrouter `"minimal"` 对 Gemini 保持不变。否则，正的 `reasoning_max_tokens` 值优先于全局 effort 和其他 Openrouter 专用值。无效的 Openrouter 专用 effort 值会被警告并视为未设置，因此已注册的推理模型会回退到 `config.reasoning_effort`。Openrouter 在此路径上把 `"max"` 规范化为 `"xhigh"`，以兼容 LiteLLM/OpenRouter。受支持的 effort 值因模型而异。对于这些钳制未覆盖的模型，不要假定 `"none"` 会关闭推理；请检查所选模型和提供商的支持情况。对于使用推理预算的 Anthropic 模型，请把有效输出 `max_tokens` 设得高于 `reasoning_max_tokens`，以便最终答案有输出余量。参见 Openrouter 的[提供商路由](https://openrouter.ai/docs/guides/routing/provider-selection)和[推理 token](https://openrouter.ai/docs/guides/best-practices/reasoning-tokens)文档。

### OrcaRouter {#orcarouter}

[OrcaRouter](https://www.orcarouter.ai) 是一个 OpenAI 兼容的 AI 网关。它在 PR-Agent 中不需要提供商专用代码：`openai/` 前缀通过 litellm 的 OpenAI 兼容路径把请求路由到 OrcaRouter 的基址 URL，处理方式与 [Neon AI Gateway](#neon-ai-gateway) 相同。

要通过 OrcaRouter 使用模型，请设置：

```toml
[config] # in configuration.toml
model = "openai/anthropic/claude-fable-5"
fallback_models = ["openai/auto"]
custom_model_max_tokens = 20000

[openai] # in .secrets.toml
api_base = "https://api.orcarouter.ai/v1"
key = "..." # your OrcaRouter api key
```

或使用环境变量（请务必使用双下划线 `__`）：

```bash
OPENAI__API_BASE=https://api.orcarouter.ai/v1
OPENAI__KEY=...
```

（你可以从[这里](https://www.orcarouter.ai/register)获取 OrcaRouter API 密钥）

无论使用哪个 OrcaRouter 模型 ID（`openai/anthropic/claude-fable-5`、`openai/auto` 等），都要在模型名上保留 `openai/` 前缀：该前缀通过 litellm 的 OpenAI 兼容路径路由请求。带前缀的名称不在[这里](https://github.com/the-pr-agent/pr-agent/blob/main/pr_agent/algo/__init__.py)的 `MAX_TOKENS` 表中，因此你还必须设置 `custom_model_max_tokens`。OrcaRouter 自己管理路由和护栏，但 `config.reasoning_effort` 仍然会到达它：PR-Agent 会用带前缀的模型 ID 对照 litellm 捆绑的推理元数据（或 `config.additional_reasoning_effort_models`）进行探测，因此即使没有额外设置，`openai/google/gemini-2.5-pro` 或 `openai/o3` 这类 ID 也会发送已配置的 effort（默认 `"medium"`）。上面示例中的 ID 没有被标记为具备推理能力，不受影响。

### Neon AI Gateway {#neon-ai-gateway}

[Neon AI Gateway](https://neon.com/docs/ai-gateway/overview) 是一个 OpenAI 兼容的推理网关。每个 Neon 分支都有自己的网关主机，因此基址 URL 指向单个分支，而不是整个账号。Neon 把该主机与凭据一起发布为 `NEON_AI_GATEWAY_BASE_URL`。该值没有路径，因此要追加 `/v1` 才能到达聊天补全。

要使用某个 Neon 分支提供的模型，请设置：

```toml
[config] # in configuration.toml
model = "openai/gpt-5-mini"
fallback_models = ["openai/gpt-5-mini"]
custom_model_max_tokens = 400000 # the context window Neon publishes for the model

[openai] # in .secrets.toml
api_base = "https://<your-neon-branch-host>/v1"
key = "..." # your Neon AI Gateway credential
```

或使用环境变量（请务必使用双下划线 `__`）：

```bash
OPENAI__API_BASE=https://<your-neon-branch-host>/v1
OPENAI__KEY=...
```

无论使用哪个 Neon 模型 ID，都要在模型名上保留 `openai/` 前缀：该前缀通过 litellm 的 OpenAI 兼容路径路由请求。带前缀的名称不在[这里](https://github.com/the-pr-agent/pr-agent/blob/main/pr_agent/algo/__init__.py)的 `MAX_TOKENS` 表中，因此你还必须设置 `custom_model_max_tokens`。请从 Neon 的[模型目录](https://neon.com/docs/ai-gateway/models)获取该值。

在 [Neon Console](https://console.neon.tech/) 中按分支创建凭据，范围是 `ai_gateway:invoke`。该凭据也可用于从创建它的分支派生出来的分支。该网关处于 beta，需要付费的 Neon 计划。它只运行在 AWS 美国东部（俄亥俄），即 `aws-us-east-2`。

:::note[仅聊天补全]
Neon 目录中的一些模型 ID 通过 OpenAI Responses API 提供，Neon 将其暴露在 `/openai/v1` 而不是 `/v1` 下。上面的配置指向聊天补全端点，因此无法到达这些模型。Neon 还记录了少数模型会把 `message.content` 作为类型化块的数组而不是字符串返回，而 PR-Agent 把回复当作字符串读取。
:::

### GitHub Copilot

有效 GitHub Copilot 订阅下的模型可通过 litellm 的 `github_copilot` 提供商使用，它以你的 GitHub 身份进行身份验证，而不是使用专用 API 密钥：

```toml
[config]
model = "github_copilot/gpt-4o"
fallback_models = ["github_copilot/gpt-4.1"]
```

模型背后的 GitHub 身份需要有效的 Copilot 订阅。这些模型的 token 预算会根据 litellm 的模型元数据自动解析，因此不需要 `custom_model_max_tokens`。不过，`get_max_tokens` 会把有效窗口钳制到 `config.max_model_tokens`，其默认值为 32000。要使用这些 Copilot 路由所记录的输入限制（例如 gpt-4o 为 64000，gpt-4.1 为 128000），请相应提高 `config.max_model_tokens`。

身份验证使用 [GitHub Copilot 提供商](https://docs.litellm.ai/docs/providers/github_copilot) 流程：

1. litellm 首先在 `GITHUB_COPILOT_TOKEN_DIR`（默认 `~/.config/litellm/github_copilot`；文件名可用 `GITHUB_COPILOT_ACCESS_TOKEN_FILE` 覆盖）下的 `access-token` 中查找预先放置的 GitHub 访问令牌。在 CI 运行器中，请在作业运行之前写入该令牌——例如把密钥挂载到该目录，或让变量指向已挂载的密钥目录——这样流程就永远不会变成交互式。
2. 只有当该文件缺失或为空时，litellm 才会回退到交互式设备代码流程（`POST https://github.com/login/device/code`，最多三次尝试），这不适合无人值守的运行器。
3. Copilot API 密钥（同一目录中的 `api-key.json`）会使用预先放置的访问令牌，自动对照 `https://api.github.com/copilot_internal/v2/token` 刷新。

Copilot 的条款是否允许这种程序化使用，是应该问 GitHub 的问题，而不是本项目能够作出的保证，因此在依赖该路由之前请先确认。

### Atlas Cloud

[Atlas Cloud](https://www.atlascloud.ai) 是一个 OpenAI 兼容的推理平台。它在 PR-Agent 中不需要提供商专用代码：`openai/` 前缀通过 litellm 的 OpenAI 兼容路径把请求路由到 Atlas 的基址 URL，处理方式与 [OrcaRouter](#orcarouter) 和 [Neon AI Gateway](#neon-ai-gateway) 相同。

要使用 Atlas Cloud 提供的模型，请设置：

```toml
[config] # in configuration.toml
model = "openai/deepseek-ai/deepseek-v4-pro"
fallback_models = ["openai/deepseek-ai/deepseek-v4-pro"]
custom_model_max_tokens = 1048000 # the context window Atlas publishes for the model

[openai] # in .secrets.toml
api_base = "https://api.atlascloud.ai/v1"
key = "..." # your Atlas Cloud api key
```

或使用环境变量（请务必使用双下划线 `__`）：

```bash
OPENAI__API_BASE=https://api.atlascloud.ai/v1
OPENAI__KEY=...
```

（你可以从[控制台](https://www.atlascloud.ai/console)获取 Atlas Cloud API 密钥）

无论使用哪个 Atlas 模型 ID（`openai/deepseek-ai/deepseek-v4-pro`、`openai/zai-org/glm-5`、`openai/moonshotai/kimi-k2.6` 等），都要在模型名上保留 `openai/` 前缀：该前缀通过 litellm 的 OpenAI 兼容路径路由请求。带前缀的名称不在[这里](https://github.com/the-pr-agent/pr-agent/blob/main/pr_agent/algo/__init__.py)的 `MAX_TOKENS` 表中，因此你还必须设置 `custom_model_max_tokens`。请从 Atlas 的[模型目录](https://www.atlascloud.ai/models)获取该值。

:::note[推理模型需要输出余量]
Atlas 的若干模型是推理模型，它们在写出答案之前会把补全 token 花在隐藏的思维链上。`deepseek-ai/deepseek-v4-pro` 在 `max_tokens = 16` 时会返回 `finish_reason = "length"` 和**空的** `message.content`——全部 16 个补全 token 都是推理 token。如果某个工具返回空白，请提高输出预算，而不是假定请求失败了。`deepseek-ai/DeepSeek-V3.1` 这类非推理 ID 不受影响。
:::

### 自定义模型

如果相关模型没有出现在[这里](https://github.com/the-pr-agent/pr-agent/blob/main/pr_agent/algo/__init__.py)，你仍然可以把它当作自定义模型使用：

1. 在配置文件中设置模型名：

```toml
[config]
model="custom_model_name"
fallback_models=["custom_model_name"]
```

2. 设置该模型的最大 token 数：

```toml
[config]
custom_model_max_tokens= ...
```

3. 前往 [litellm 文档](https://litellm.vercel.app/docs/proxy/quick_start#supported-llms)，找到你想使用的模型，并设置相关环境变量。

4. 大多数推理模型不支持聊天式输入（`system` 和 `user` 消息）或温度设置。
   要绕过聊天模板和温度控制，请在配置文件中设置 `config.custom_reasoning_model = true`。

## 专用参数

### OpenAI 模型

```toml
[config]
reasoning_effort = "medium" # "none", "minimal", "low", "medium", "high", "xhigh", "max"
```

对于支持推理 effort 的 OpenAI 模型（例如 gpt-5.6-terra），你可以通过 `config` 节指定其推理 effort。默认值是 `medium`。你可以根据使用情况把它改成任何受支持的值。可用值取决于模型和提供商。当 litellm 把某个 GPT-5 模型标记为不支持 minimal 时，PR-Agent 会改为发送 low。

对于通过 OpenAI 兼容端点提供、而 litellm 不将其识别为具备推理能力的模型，请把它的 ID 加入 `config.additional_reasoning_effort_models`。对于已知模型，支持情况由 litellm 捆绑的推理元数据加上维护中的 Grok 注册表决定（Grok id 通过其 `xai/` 前缀解析），Claude 模型被排除在元数据路径之外（它们的推理来自专用的扩展/自适应思考设置；上面列表中的显式条目仍然适用于它们）。配置 ID 可以精确匹配，也可以通过任意提供商前缀匹配（例如 `"deepseek-v4-flash-0731"` 匹配 `"openai/deepseek-v4-flash-0731"`）。当 LiteLLM 不识别该模型时，PR-Agent 会设置 `allowed_openai_params = ["reasoning_effort"]`，以便该参数到达端点。请注意，默认的 `"medium"` 可能被只接受不同子集（例如 `"none"/"low"/"high"/"max"`）的提供商拒绝；添加自定义模型 ID 会把该提供商侧错误暴露出来，而不是静默丢弃该设置。

对于在 OpenAI、Azure 或 OpenRouter 之外、以同一模型 ID 托管的 GPT-6 Sol、Luna 或 GPT-6.1 Sol，请把该 ID 加入此列表，以显式启用 `reasoning_effort`。

要使用 [GPT-6 Sol](https://developers.openai.com/api/docs/models/gpt-6-sol) 或 [GPT-6 Luna](https://developers.openai.com/api/docs/models/gpt-6-luna)：

```toml
[config]
model = "gpt-6-sol" # or "gpt-6-luna"
reasoning_effort = "medium" # "none", "low", "medium", "high", "xhigh", "max"
```

对于 OpenAI、Azure 和 OpenRouter 路由上已识别的原生 Sol 层级 GPT-6 ID，PR-Agent 会省略 temperature。GPT-6 Sol 和 GPT-6 Luna 接受 `none`：OpenAI 路由会原样传递它，Azure 路由会保留它，OpenRouter 会把它映射为关闭推理。GPT-6.1 Sol 在其受支持级别中省略了 `none`，因此 PR-Agent 会把它钳制为 `low`；见下面它自己的小节。这三者都在 Azure 和 OpenRouter 上把 `max` 映射为 `xhigh`，旧的 `minimal` 设置会被映射为 `low`。每个都有 1,050,000 token 的上下文窗口、922,000 token 的输入上限，并支持最多 128,000 个输出 token。除非某个工具绕过了该已配置上限（`/help` 就会这样做），PR-Agent 也会应用 `config.max_model_tokens`；原生输入上限仍然适用。PR-Agent 的文本请求使用现有的 Chat Completions 路径。对于 GPT-6 Sol 和 Luna，OpenAI 要求对内置工具以及带推理的函数调用使用 Responses API；Chat Completions 的函数调用仅限于 `reasoning_effort = "none"`。

未识别的 OpenRouter `_thinking` 变体，例如 `_thinking:batch` 或 `_thinking:free`，会保留其字面 ID，而不进行原生 GPT-6 的 temperature 或 effort 规范化。把完整 ID 加入 `config.additional_reasoning_effort_models` 可显式启用推理。对于未注册的字面 ID，提示词预算需要可用的 LiteLLM 元数据或 `config.custom_model_max_tokens`。对于非原生自定义提供商上的裸 Sol 层级 GPT-6 ID，正的 `config.custom_model_max_tokens` 优先于原生注册表中的值。

要使用 [GPT-6.1 Sol](https://developers.openai.com/api/docs/models/gpt-6.1-sol)：

```toml
[config]
model = "gpt-6.1-sol"
reasoning_effort = "medium" # "low", "medium", "high", "xhigh", "max"
```

GPT-6.1 Sol 共用上面的路由：同样的 temperature 处理、同样的 `max`/`minimal` 映射，以及同样的 1,050,000 token 上下文窗口、922,000 token 输入上限和 128,000 token 输出限制。其模型页面只列出 `low`、`medium`（默认）、`high`、`xhigh` 和 `max`，因此**不**支持 `none`，PR-Agent 会把已配置的 `none` 钳制为 `low`。对于 `config.reasoning_effort`，这覆盖 OpenAI、Azure、Azure AI、aiohttp 和 OpenRouter 路由。在 OpenRouter 上，它也适用于显式的 `openrouter.reasoning_effort = "none"`；正的 `openrouter.reasoning_max_tokens` 随后优先。

在非原生自定义提供商上，该 ID 被当作未知模型：除非你把它列在 `config.additional_reasoning_effort_models` 中，否则不会发送任何内容；如果列了，已配置的 effort 会按原样转发。只在接受该模型完整 effort 集合的端点上注册它。

其模型页面还要求工具调用使用 Responses API，并说明 Chat Completions 在没有工具调用时受支持，因此与 GPT-6 Sol 和 Luna 不同，该模型在任何 effort 下都没有 Chat Completions 工具调用路径。

要使用 [GPT-6 Astra](https://developers.openai.com/api/docs/models/gpt-6-astra)：

```toml
[config]
model = "gpt-6-astra"
reasoning_effort = "medium" # "low", "medium", "high", "xhigh", "max"
```

PR-Agent 会为 GPT-6 Astra 省略 temperature，并把 `none` 或 `minimal` 推理 effort 映射为 `low`。它的 1,050,000 token 上下文窗口仍然受 `config.max_model_tokens` 约束。使用的是现有的 Chat Completions 路径；能否访问取决于你的 OpenAI 账号。

### Anthropic 模型

```toml
[config]
enable_claude_extended_thinking = false # Set to true to enable extended thinking feature
extended_thinking_budget_tokens = 2048
extended_thinking_max_output_tokens = 4096
```

默认情况下，PR-Agent 只对内置的 Claude 模型列表应用扩展思考载荷（见 `pr_agent/algo/__init__.py` 中的 `CLAUDE_EXTENDED_THINKING_MODELS`）。如果你使用不在该列表中的较新或自定义 Claude 模型，可以覆盖它：

```toml
[config]
claude_extended_thinking_models_override = ["anthropic/claude-my-new-model"]
```

当 `claude_extended_thinking_models_override` 非空时，它会完全替换内置列表，因此请包含每一个应该接收扩展思考的模型。留空（默认）则使用内置默认值。

:::note[仅支持接受思考预算的模型]
PR-Agent 通过手动的 `thinking={"type": "enabled", "budget_tokens": ...}` 请求启用扩展思考。仅支持自适应的 Claude 模型（例如 Opus 4.7/4.8、Opus 5/5.5、Sonnet 5、Fable 5、Fable 5.1）会拒绝 `budget_tokens`，因此它们被有意排除在内置默认值之外。如果你仍然把其中一个加入 `claude_extended_thinking_models_override`，PR-Agent 会跳过它的扩展思考载荷并记录警告，而不是发送一个提供商会拒绝的请求——对这些模型请改用 `enable_claude_adaptive_thinking`。
:::

两道思考闸门只有在模型 id 本身可识别时才会触发：Bedrock 应用推理配置 ARN 这类不透明 id 哪个闸门都不匹配，PR-Agent 会记录警告，而不是静默地什么都不发送。参见[使用应用推理配置 ARN 的 Claude 5 思考](#claude-5-thinking-with-an-application-inference-profile-arn)。

## 输出 token 限制

```toml
[config]
max_output_tokens = 0 # 0 = unset (default)
```

默认情况下，PR-Agent 不会在模型调用上发送输出 token 限制，因此适用提供商自己的默认值。在某些提供商上，该默认值很低——例如 AWS Bedrock（Converse API）可以把 Claude 推理模型的输出 token 限制在 4096，而由于推理 token 计入该预算，可见答案可能返回为空或被截断。把 `config.max_output_tokens` 设为正值（例如 `16000`），就会把它作为 `max_completion_tokens` 发送给 LiteLLM，适用于原生 OpenAI/Azure GPT-6 模型以及已识别的 Astra ID，包括自定义提供商上的裸 Astra ID。OpenRouter Astra 仅在没有路由后缀，或带有 `:nitro`/`:floor` 时使用该参数。其他路由使用 `max_tokens`，而 `azure_text` 和 `text-completion-openai` 路由始终使用 `max_tokens`。请使用所选模型支持的值。GPT-6 Astra、Sol、Luna 和 GPT-6.1 Sol 最多支持 128,000 个输出 token，包括推理 token。PR-Agent 不会自动把该设置钳制到模型的输出限制。低于 4096 的值会被提高到 4096，非数字或负值会被忽略；两者都会记录警告。启用 Claude 扩展思考时，`extended_thinking_max_output_tokens` 优先。对于上下文窗口较小的模型，请记住提示词 token 和补全 token 共享模型的上下文窗口：请调整 `config.max_model_tokens` 的大小，使打包后的提示词为已配置的输出限制留出空间。

## 将小型拉取请求路由到更便宜的模型 {#routing-small-pull-requests-to-a-cheaper-model}

`config.model` 处理每一个拉取请求，无论多小。启用模型路由后，低于已配置规模的拉取请求会改由更便宜的模型处理，之后仍然应用 `config.fallback_models`：

```toml
[model_routing]
enable = true

[[model_routing.rules]]
max_hunks = 3
model = "gpt-5.6-luna"

[[model_routing.rules]]
max_hunks = 15
max_files = 6
model = "gpt-5.6-terra"
```

规则按顺序检查，第一个其限制能容纳该拉取请求的规则会为这次调用选择主模型。不符合任何规则的拉取请求使用 `config.model`。规模按 `[ignore]` 规则之后剩余的 diff hunk 数量（`max_hunks`）和已更改文件数量（`max_files`）衡量。每个 Git 平台都会报告这两者，并且都不依赖模型的分词器，因此无论选择哪个模型，阈值的含义都相同。

路由只适用于请求常规模型的调用：`/review`、`/improve`、`/generate_labels` 和 `/add_docs`。已经使用 `config.model_weak` 的工具（`/describe`、`/ask`、`/update_changelog`）保持不变，自我反思仍然使用专用的 `config.model_reasoning`。启用 `config.output_run_details` 后，运行详情会显示被路由的拉取请求最终落在哪个模型上。

:::note[Azure 部署]
Azure 部署绑定到一个模型，因此当设置了 `openai.deployment_id` 时，每条规则也需要自己的 `deployment_id`。没有它的规则会被跳过并给出警告，然后尝试下一条规则。
:::
