# Providers

LLMfy supports three LLM providers. The table below summarises their capabilities:

| Provider | Class | Install Extra | Tool Calling | Streaming | Image | Document | Video |
|----------|-------|---------------|--------------|-----------|-------|----------|-------|
| OpenAI | `OpenAIModel` | `llmfy[openai]` | ✅ | ✅ | ✅ | ✅ | ❌ |
| AWS Bedrock | `BedrockModel` | `llmfy[boto3]` | ✅ | ✅ | ✅ | ✅ | ✅ |
| Google AI | `GoogleAIModel` | `llmfy[google-genai]` | ✅ | ✅ | ✅ | ✅ | ✅ |

---

## OpenAI

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

Alternatively, pass `api_key` directly to `OpenAIModel` — it takes precedence over the environment variable.

### Configuration

```python
from llmfy import OpenAIConfig, OpenAIThinkingConfig

config = OpenAIConfig(
    temperature=0.7,       # Sampling temperature (0.0-2.0)
    max_tokens=None,       # Max output tokens (None = model default)
    top_p=1.0,             # Nucleus sampling probability
    frequency_penalty=0.0, # Penalise repeated tokens
    presence_penalty=0.0,  # Penalise tokens already in the prompt
    # Thinking / reasoning (o-series models) — grouped in one settings object
    thinking=OpenAIThinkingConfig(
        enabled=False,   # Set True for o1/o3/o4-mini reasoning models
        effort=None,     # 'low', 'medium', 'high' — defaults to 'medium'
    ),
)
```

See [Thinking Config](thinking-config.md) for usage with reasoning models.

### Usage

```python linenums="1"
from llmfy import OpenAIModel, OpenAIConfig, LLMfy

config = OpenAIConfig(temperature=0.7)
llm = OpenAIModel(model="gpt-4o-mini", config=config)

agent = LLMfy(llm, system_message="You are a helpful assistant.")
```

You can also pass the API key directly instead of using an environment variable:

```python
llm = OpenAIModel(model="gpt-4o-mini", config=config, api_key="sk-...")
```

Common model IDs: `gpt-4o`, `gpt-4o-mini`, `gpt-3.5-turbo`

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

Alternatively, pass `aws_access_key_id`, `aws_secret_access_key`, and `aws_bedrock_region` directly to `BedrockModel` — they take precedence over the environment variables.

### Configuration

```python
from llmfy import BedrockConfig, BedrockThinkingConfig

config = BedrockConfig(
    temperature=0.7,      # Sampling temperature
    max_tokens=None,      # Max output tokens
    top_p=1.0,            # Nucleus sampling probability
    top_k=None,           # Top-k sampling
    stopSequences=None,   # List of stop sequences
    # Thinking (Claude and Nova 2 Lite models) — grouped in one settings object
    thinking=BedrockThinkingConfig(
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
from llmfy import BedrockModel, BedrockConfig, LLMfy

config = BedrockConfig(temperature=0.7)
llm = BedrockModel(model="amazon.nova-lite-v1:0", config=config)

agent = LLMfy(llm, system_message="You are a helpful assistant.")
```

You can also pass the credentials directly instead of using environment variables:

```python
llm = BedrockModel(
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

Alternatively, pass `api_key` directly to `GoogleAIModel` — it takes precedence over the environment variable.

### Configuration

```python
from llmfy import GoogleAIConfig, GoogleAIThinkingConfig

config = GoogleAIConfig(
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
    thinking=GoogleAIThinkingConfig(
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
from llmfy import GoogleAIModel, GoogleAIConfig, LLMfy

config = GoogleAIConfig(temperature=0.7)
llm = GoogleAIModel(model="gemini-2.5-flash-lite", config=config)

agent = LLMfy(llm, system_message="You are a helpful assistant.")
```

You can also pass the API key directly instead of using an environment variable:

```python
llm = GoogleAIModel(model="gemini-2.5-flash-lite", config=config, api_key="...")
```

Common model IDs: `gemini-2.0-flash`, `gemini-2.5-flash`, `gemini-2.5-flash-lite`, `gemini-2.5-pro`
