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

### Configuration

```python
from llmfy import OpenAIConfig

config = OpenAIConfig(
    temperature=0.7,       # Sampling temperature (0.0-2.0)
    max_tokens=None,       # Max output tokens (None = model default)
    top_p=1.0,             # Nucleus sampling probability
    frequency_penalty=0.0, # Penalise repeated tokens
    presence_penalty=0.0,  # Penalise tokens already in the prompt
    # Thinking / reasoning (o-series models)
    enable_thinking=False,    # Set True for o1/o3/o4-mini reasoning models
    reasoning_effort=None,    # 'low', 'medium', 'high' — defaults to 'medium'
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

### Configuration

```python
from llmfy import BedrockConfig

config = BedrockConfig(
    temperature=0.7,      # Sampling temperature
    max_tokens=None,      # Max output tokens
    top_p=1.0,            # Nucleus sampling probability
    top_k=None,           # Top-k sampling
    stopSequences=None,   # List of stop sequences
    # Thinking (Claude and Nova 2 Lite models)
    enable_thinking=False,        # Set True to enable thinking
    thinking_budget_tokens=None,  # Claude extended thinking: token budget (min 1024)
    thinking_type=None,           # 'enabled' | 'adaptive' — Claude mode selector
    thinking_effort=None,         # Claude adaptive: 'low', 'medium', 'high', 'max'
    reasoning_effort=None,        # Nova 2 Lite: 'low', 'medium', 'high'
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

### Configuration

```python
from llmfy import GoogleAIConfig

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
    # Thinking (Gemini 2.5+ and Gemini 3 series)
    enable_thinking=False,            # Set True to enable thinking
    thinking_level=None,              # 'MINIMAL', 'LOW', 'MEDIUM', 'HIGH'
    thinking_budget_tokens=None,      # Token budget (-1=dynamic, 0=disable)
    thinking_include_thoughts=None,   # Include thinking steps in response
    thinking_config=None,             # Raw ThinkingConfig override (backward compat)
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

Common model IDs: `gemini-2.0-flash`, `gemini-2.5-flash`, `gemini-2.5-flash-lite`, `gemini-2.5-pro`
