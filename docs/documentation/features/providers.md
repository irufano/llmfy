# Providers

LLMfy supports four LLM providers. The table below summarises their capabilities:

| Provider | Class | Install Extra | Tool Calling | Streaming | Image | Document | Video |
|----------|-------|---------------|--------------|-----------|-------|----------|-------|
| Anthropic (Messages API) | `AnthropicMessagesModel` | `llmfy[anthropic]` | ✅ | ✅ | ✅ | ✅ | ❌ |
| OpenAI (Chat Completions) | `OpenAIChatModel` | `llmfy[openai]` | ✅ | ✅ | ✅ | ✅ | ❌ |
| OpenAI (Responses API) | `OpenAIResponsesModel` | `llmfy[openai]` | ✅ | ✅ | ✅ | ❌ | ❌ |
| AWS Bedrock | `BedrockConverseModel` | `llmfy[boto3]` | ✅ | ✅ | ✅ | ✅ | ✅ |
| Google AI | `GoogleAIGenerateModel` | `llmfy[google-genai]` | ✅ | ✅ | ✅ | ✅ | ✅ |

!!! note "Two OpenAI backends, one vendor"
    `OpenAIChatModel` and `OpenAIResponsesModel` both talk to OpenAI — they just use different API surfaces (Chat Completions vs the newer Responses API). Pick one per `LLMfy` instance; they are not interchangeable mid-conversation since their wire formats differ. See [OpenAI (Responses API)](#openai-responses-api) below.

---

## Anthropic (Messages API)

`AnthropicMessagesModel` talks directly to Anthropic's native [Messages API](https://platform.claude.com/docs/en/build-with-claude/working-with-messages) (`api.anthropic.com`) via the official `anthropic` Python SDK — distinct from using Claude models through AWS Bedrock's Converse API (see [AWS Bedrock](#aws-bedrock) below, which is a separate backend/provider pairing: `ModelBackend.ANTHROPIC_MESSAGES` vs `ModelBackend.BEDROCK_CONVERSE`).

!!! warning "Video input not supported"
    `ContentType.VIDEO` raises `LLMfyException` on `AnthropicMessagesModel` — the native Messages API has no video input support. Text, image, and document (PDF) input are implemented.

### Installation

=== "UV"

    ```shell
    uv add "llmfy[anthropic]"
    ```

=== "pip"

    ```shell
    pip install "llmfy[anthropic]"
    ```

### Environment Variables

- `ANTHROPIC_API_KEY`

Alternatively, pass `api_key` directly to `AnthropicMessagesModel` — it takes precedence over the environment variable. A `base_url` argument is also accepted, for pointing at a proxy or compatible endpoint.

### Configuration

```python
from llmfy import AnthropicMessagesConfig, AnthropicMessagesThinkingConfig

config = AnthropicMessagesConfig(
    max_tokens=4096,       # REQUIRED by the Messages API — always sent
    temperature=None,      # None = API default (1.0)
    top_p=None,            # Nucleus sampling probability
    top_k=None,            # Top-k sampling
    stop_sequences=None,   # List of stop sequences
    # Thinking — grouped in one settings object
    thinking=AnthropicMessagesThinkingConfig(
        enabled=False,   # Set True to enable
        budget_tokens=None,  # Extended thinking: token budget (min 1024)
        type=None,           # 'adaptive' for current-generation models
        effort=None,         # Adaptive: 'low', 'medium', 'high', 'xhigh', 'max'
    ),
)
```

See [Thinking Config](thinking-config.md#anthropic-messages-api) for usage with reasoning models and [Prompt Caching](prompt-caching.md#anthropic-messages-api) for caching.

### Usage

```python linenums="1"
from llmfy import AnthropicMessagesModel, AnthropicMessagesConfig, LLMfy

config = AnthropicMessagesConfig(temperature=0.7)
llm = AnthropicMessagesModel(model="claude-sonnet-5", config=config)

agent = LLMfy(llm, system_message="You are a helpful assistant.")
```

You can also pass the API key directly instead of using an environment variable:

```python
llm = AnthropicMessagesModel(model="claude-sonnet-5", config=config, api_key="sk-ant-...")
```

Common model IDs: `claude-opus-5`, `claude-sonnet-5`, `claude-haiku-4-5`, `claude-fable-5`

---

## OpenAI (Chat Completions)

### Installation

=== "UV"

    ```shell
    uv add "llmfy[openai]"
    ```

=== "pip"

    ```shell
    pip install "llmfy[openai]"
    ```

### Environment Variables

- `OPENAI_API_KEY`

Alternatively, pass `api_key` directly to `OpenAIChatModel` — it takes precedence over the environment variable.

### Configuration

```python
from llmfy import OpenAIChatConfig, OpenAIChatThinkingConfig

config = OpenAIChatConfig(
    temperature=0.7,       # Sampling temperature (0.0-2.0); None omits the field entirely
                            # — needed for models that reject it outright rather than
                            # accepting a default (400 unsupported_parameter)
    max_tokens=None,       # Max output tokens (None = model default)
    top_p=1.0,             # Nucleus sampling probability; None omits the field, same as temperature
    frequency_penalty=0.0, # Penalise repeated tokens
    presence_penalty=0.0,  # Penalise tokens already in the prompt
    # Thinking / reasoning (o-series models) — grouped in one settings object
    thinking=OpenAIChatThinkingConfig(
        enabled=False,   # Set True for o1/o3/o4-mini reasoning models
        effort=None,     # 'low', 'medium', 'high' — defaults to 'medium'
    ),
)
```

See [Thinking Config](thinking-config.md) for usage with reasoning models.

### Usage

```python linenums="1"
from llmfy import OpenAIChatModel, OpenAIChatConfig, LLMfy

config = OpenAIChatConfig(temperature=0.7)
llm = OpenAIChatModel(model="gpt-4o-mini", config=config)

agent = LLMfy(llm, system_message="You are a helpful assistant.")
```

You can also pass the API key directly instead of using an environment variable:

```python
llm = OpenAIChatModel(model="gpt-4o-mini", config=config, api_key="sk-...")
```

Common model IDs: `gpt-4o`, `gpt-4o-mini`, `gpt-3.5-turbo`

---

## OpenAI (Responses API)

`OpenAIResponsesModel` talks to OpenAI's newer [Responses API](https://developers.openai.com/api/reference/responses/overview) instead of Chat Completions. Same vendor, same `OPENAI_API_KEY`/install extra as above — just a different wire format (flat `input`/`output` items instead of nested `messages`/`tool_calls`), and access to Responses-only features like `reasoning.summary`.

!!! warning "Document input not yet supported"
    `ContentType.DOCUMENT` and `ContentType.VIDEO` raise `LLMfyException` on `OpenAIResponsesModel` — only text and image input are implemented. Use `OpenAIChatModel` for document input on OpenAI.

### Installation

Same as [OpenAI (Chat Completions)](#openai-chat-completions) above — `llmfy[openai]`.

### Environment Variables

- `OPENAI_API_KEY`

Alternatively, pass `api_key` directly to `OpenAIResponsesModel` — it takes precedence over the environment variable.

### Configuration

```python
from llmfy import OpenAIResponsesConfig, OpenAIResponsesReasoningConfig

config = OpenAIResponsesConfig(
    temperature=0.7,        # Sampling temperature (0.0-2.0); None omits the field entirely
                             # — needed for models that reject it outright rather than
                             # accepting a default (400 unsupported_parameter)
    max_output_tokens=None, # Max output tokens (None = model default)
    top_p=1.0,               # Nucleus sampling probability; None omits the field, same as temperature
    # Reasoning (o-series and GPT-5.x models) — grouped in one settings object
    reasoning=OpenAIResponsesReasoningConfig(
        enabled=False,  # Set True for o-series/GPT-5.x reasoning models
        effort=None,    # 'none', 'minimal', 'low', 'medium', 'high', 'xhigh', 'max'
        summary=None,   # 'auto', 'concise', 'detailed' — request a reasoning summary
    ),
)
```

See [Thinking Config](thinking-config.md#openai-responses-api) for usage with reasoning models.

### Usage

```python linenums="1"
from llmfy import OpenAIResponsesModel, OpenAIResponsesConfig, LLMfy

config = OpenAIResponsesConfig(temperature=0.7)
llm = OpenAIResponsesModel(model="gpt-4o-mini", config=config)

agent = LLMfy(llm, system_message="You are a helpful assistant.")
```

You can also pass the API key directly instead of using an environment variable:

```python
llm = OpenAIResponsesModel(model="gpt-4o-mini", config=config, api_key="sk-...")
```

Common model IDs: `gpt-4o`, `gpt-4o-mini`, `gpt-5.6-sol`, `gpt-5.6-terra`, `gpt-5.6-luna`

---

## AWS Bedrock

### Installation

=== "UV"

    ```shell
    uv add "llmfy[boto3]"
    ```

=== "pip"

    ```shell
    pip install "llmfy[boto3]"
    ```

### Environment Variables

- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_BEDROCK_REGION`

Alternatively, pass `aws_access_key_id`, `aws_secret_access_key`, and `aws_bedrock_region` directly to `BedrockConverseModel` — they take precedence over the environment variables.

### Configuration

```python
from llmfy import BedrockConverseConfig, BedrockConverseThinkingConfig

config = BedrockConverseConfig(
    temperature=0.7,      # Sampling temperature
    max_tokens=None,      # Max output tokens
    top_p=1.0,            # Nucleus sampling probability
    top_k=None,           # Top-k sampling
    stopSequences=None,   # List of stop sequences
    # Thinking (Claude and Nova 2 Lite models) — grouped in one settings object
    thinking=BedrockConverseThinkingConfig(
        enabled=False,          # Set True to enable thinking
        budget_tokens=None,     # Claude extended thinking: token budget (min 1024)
        type=None,              # 'enabled' | 'adaptive' — Claude mode selector
        effort=None,            # Claude adaptive: 'low', 'medium', 'high', 'max'
        reasoning_effort=None,  # Nova 2 Lite: 'low', 'medium', 'high'
    ),
)
```

See [Thinking Config](thinking-config.md) for per-model details and constraints.

### Usage

```python linenums="1"
from llmfy import BedrockConverseModel, BedrockConverseConfig, LLMfy

config = BedrockConverseConfig(temperature=0.7)
llm = BedrockConverseModel(model="amazon.nova-lite-v1:0", config=config)

agent = LLMfy(llm, system_message="You are a helpful assistant.")
```

You can also pass the credentials directly instead of using environment variables:

```python
llm = BedrockConverseModel(
    model="amazon.nova-lite-v1:0",
    config=config,
    aws_access_key_id="...",
    aws_secret_access_key="...",
    aws_bedrock_region="us-east-1",
)
```

Common model IDs: `amazon.nova-lite-v1:0`, `amazon.nova-pro-v1:0`, `anthropic.claude-3-5-sonnet-20240620-v1:0`

---

## Google AI

### Installation

=== "UV"

    ```shell
    uv add "llmfy[google-genai]"
    ```

=== "pip"

    ```shell
    pip install "llmfy[google-genai]"
    ```

### Environment Variables

- `GOOGLE_API_KEY`

Alternatively, pass `api_key` directly to `GoogleAIGenerateModel` — it takes precedence over the environment variable.

### Configuration

```python
from llmfy import GoogleAIGenerateConfig, GoogleAIGenerateThinkingConfig

config = GoogleAIGenerateConfig(
    temperature=0.7,              # Sampling temperature
    max_tokens=None,              # Max output tokens (maps to max_output_tokens)
    top_p=None,                   # Nucleus sampling probability
    top_k=None,                   # Top-k sampling
    stop_sequences=None,          # List of stop sequences
    candidate_count=None,         # Number of response candidates
    seed=None,                    # Random seed for reproducibility
    presence_penalty=None,        # Penalise tokens already in the prompt
    frequency_penalty=None,       # Penalise repeated tokens
    response_mime_type=None,      # e.g. "application/json" for structured output
    response_schema=None,         # Schema for structured output
    safety_settings=None,         # List of SafetySetting instances
    # Thinking (Gemini 2.5+ and Gemini 3 series) — grouped in one settings object
    thinking=GoogleAIGenerateThinkingConfig(
        enabled=False,            # Set True to enable thinking
        level=None,               # 'MINIMAL', 'LOW', 'MEDIUM', 'HIGH'
        budget_tokens=None,       # Token budget (-1=dynamic, 0=disable)
        include_thoughts=None,    # Include thinking steps in response
        raw=None,                 # Raw ThinkingConfig override (backward compat)
    ),
)
```

See [Thinking Config](thinking-config.md) for per-model details.

### Usage

```python linenums="1"
from llmfy import GoogleAIGenerateModel, GoogleAIGenerateConfig, LLMfy

config = GoogleAIGenerateConfig(temperature=0.7)
llm = GoogleAIGenerateModel(model="gemini-2.5-flash-lite", config=config)

agent = LLMfy(llm, system_message="You are a helpful assistant.")
```

You can also pass the API key directly instead of using an environment variable:

```python
llm = GoogleAIGenerateModel(model="gemini-2.5-flash-lite", config=config, api_key="...")
```

Common model IDs: `gemini-2.0-flash`, `gemini-2.5-flash`, `gemini-2.5-flash-lite`, `gemini-2.5-pro`

---

## Using a Compatible Endpoint (`base_url`)

`AnthropicMessagesModel`, `OpenAIChatModel`, and `OpenAIResponsesModel` accept `base_url`, so any provider exposing an Anthropic-Messages- or OpenAI-compatible API can be used through llmfy — not just Anthropic/OpenAI themselves. See [Compatible Endpoints](compatible-endpoints.md) for detailed examples (AWS Bedrock Mantle, Groq, Together AI, OpenRouter, self-hosted servers) and the caveats to check before pointing a config at a third-party endpoint.
