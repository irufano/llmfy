# Thinking Config

LLMfy provides a unified `enable_thinking` flag across all three providers to activate extended thinking / reasoning mode. Each provider has additional fields to tune thinking behaviour.

| Provider | Toggle | Effort control | Budget control |
|----------|--------|---------------|----------------|
| **AWS Bedrock** (Claude) | `enable_thinking=True` | `thinking_effort` (adaptive) | `thinking_budget_tokens` (extended) |
| **AWS Bedrock** (Nova 2) | `enable_thinking=True` | `reasoning_effort` | — |
| **OpenAI** | `enable_thinking=True` | `reasoning_effort` | — |
| **Google AI** | `enable_thinking=True` | `thinking_level` | `thinking_budget_tokens` |

---

## AWS Bedrock

Bedrock supports three distinct thinking modes depending on the model family.

### Mode 1 — Claude Extended Thinking

For Claude 3.7 and Claude 4 series (pre-4.6). Uses a fixed token budget.

**Supported models**

| Model | Model ID |
|-------|----------|
| Claude 3.7 Sonnet | `anthropic.claude-3-7-sonnet-20250219-v1:0` |
| Claude Sonnet 4 | `anthropic.claude-sonnet-4-20250514-v1:0` |
| Claude Opus 4 | `anthropic.claude-opus-4-20250514-v1:0` |
| Claude Sonnet 4.5 | `anthropic.claude-sonnet-4-5-20250929-v1:0` |
| Claude Haiku 4.5 | `anthropic.claude-haiku-4-5-20251001-v1:0` |
| Claude Opus 4.5 | `anthropic.claude-opus-4-5-20251101-v1:0` |

!!! warning "Constraints"
    `temperature`, `top_p`, and `top_k` must be set to `None` when extended thinking is enabled. The API returns an error if they are present.

**Config fields**

| Field | Type | Description |
|-------|------|-------------|
| `enable_thinking` | `bool` | Set to `True` to enable. |
| `thinking_budget_tokens` | `int \| None` | Max thinking tokens. Min `1024`. |

```python linenums="1"
from llmfy import BedrockModel, BedrockConfig, LLMfy

config = BedrockConfig(
    enable_thinking=True,
    thinking_budget_tokens=4000,
    temperature=None,  # must be unset
    top_p=None,        # must be unset
)

llm = BedrockModel(
    model="anthropic.claude-3-7-sonnet-20250219-v1:0",
    config=config,
)

agent = LLMfy(llm, system_message="You are a helpful assistant.")
response = agent.invoke("Explain the halting problem step by step.")
print(response.result.content)
```

---

### Mode 2 — Claude Adaptive Thinking

For Claude 4.6 and newer. The model dynamically decides when and how much to think. Uses a named effort level instead of a token budget.

**Supported models**

| Model | Model ID | Notes |
|-------|----------|-------|
| Claude Sonnet 4.6 | `anthropic.claude-sonnet-4-6` | Adaptive preferred (`enabled` deprecated) |
| Claude Opus 4.6 | `anthropic.claude-opus-4-6-v1` | Supports `max` effort level |
| Claude Opus 4.7 | `anthropic.claude-opus-4-7` | Adaptive only |
| Claude Fable 5 | `anthropic.claude-fable-5` | Adaptive only |
| Claude Mythos 5 | `anthropic.claude-mythos-5` | Adaptive only |

!!! note
    Fable 5, Mythos 5, and Opus 4.7 **only** accept `thinking_type='adaptive'`. Sending `thinking_type='enabled'` returns a `400` error.

**Config fields**

| Field | Type | Values | Description |
|-------|------|--------|-------------|
| `enable_thinking` | `bool` | — | Set to `True` to enable. |
| `thinking_type` | `str \| None` | `'adaptive'` | Must be set to `'adaptive'` for this mode. |
| `thinking_effort` | `str \| None` | `'low'`, `'medium'`, `'high'`, `'max'` | Controls thinking depth. `'max'` is Opus 4.6 only. |

```python linenums="1"
from llmfy import BedrockModel, BedrockConfig, LLMfy

config = BedrockConfig(
    enable_thinking=True,
    thinking_type="adaptive",
    thinking_effort="high",
)

llm = BedrockModel(
    model="anthropic.claude-sonnet-4-6",
    config=config,
)

agent = LLMfy(llm, system_message="You are a helpful assistant.")
response = agent.invoke("Solve this step by step: If 3x + 7 = 22, find x.")
print(response.result.content)
```

---

### Mode 3 — Amazon Nova 2 Lite Reasoning

For Amazon Nova 2 Lite. Uses a named effort level via the `reasoningConfig` API format.

**Supported models**

| Model | Model ID |
|-------|----------|
| Amazon Nova 2 Lite | `us.amazon.nova-2-lite-v1:0` |

!!! warning "Constraints"
    When `reasoning_effort='high'`, `temperature`, `top_p`, and `max_tokens` must be set to `None`.

**Config fields**

| Field | Type | Values | Description |
|-------|------|--------|-------------|
| `enable_thinking` | `bool` | — | Set to `True` to enable. |
| `reasoning_effort` | `str \| None` | `'low'`, `'medium'`, `'high'` | Controls reasoning depth. |

```python linenums="1"
from llmfy import BedrockModel, BedrockConfig, LLMfy

config = BedrockConfig(
    enable_thinking=True,
    reasoning_effort="medium",
)

llm = BedrockModel(
    model="us.amazon.nova-2-lite-v1:0",
    config=config,
)

agent = LLMfy(llm, system_message="You are a helpful assistant.")
response = agent.invoke("Plan a 5-step strategy to learn Python in 30 days.")
print(response.result.content)
```

For `high` effort, unset inference params:

```python linenums="1"
config = BedrockConfig(
    enable_thinking=True,
    reasoning_effort="high",
    temperature=None,  # must be unset for high effort
    top_p=None,
    max_tokens=None,
)
```

---

## OpenAI

Reasoning is enabled on o-series models via the `reasoning_effort` field.

**Supported models**

| Model | Model ID |
|-------|----------|
| o1 | `o1` |
| o1-mini | `o1-mini` |
| o3 | `o3` |
| o3-mini | `o3-mini` |
| o4-mini | `o4-mini` |

**Config fields**

| Field | Type | Values | Description |
|-------|------|--------|-------------|
| `enable_thinking` | `bool` | — | Set to `True` to enable. |
| `reasoning_effort` | `str \| None` | `'low'`, `'medium'`, `'high'` | Defaults to `'medium'` when not set. |

```python linenums="1"
from llmfy import OpenAIModel, OpenAIConfig, LLMfy

config = OpenAIConfig(
    enable_thinking=True,
    reasoning_effort="high",
)

llm = OpenAIModel(model="o4-mini", config=config)

agent = LLMfy(llm, system_message="You are a helpful assistant.")
response = agent.invoke("What is the time complexity of Dijkstra's algorithm?")
print(response.result.content)
```

---

## Google AI

Thinking is controlled through `ThinkingConfig` parameters. You can use either a named effort level (`thinking_level`) or a token budget (`thinking_budget_tokens`).

**Supported models**

| Series | Models |
|--------|--------|
| Gemini 2.5 | `gemini-2.5-pro`, `gemini-2.5-flash`, `gemini-2.5-flash-lite` |
| Gemini 3 | `gemini-3-flash`, `gemini-3.1-pro`, `gemini-3.1-flash-lite`, `gemini-3.5-flash` |

**Config fields**

| Field | Type | Values | Description |
|-------|------|--------|-------------|
| `enable_thinking` | `bool` | — | Set to `True` to enable. |
| `thinking_level` | `str \| None` | `'MINIMAL'`, `'LOW'`, `'MEDIUM'`, `'HIGH'` | Named effort level. Preferred for Gemini 3 series. |
| `thinking_budget_tokens` | `int \| None` | e.g. `1024`, `-1` (dynamic), `0` (disable) | Token budget for thinking. Preferred for Gemini 2.5. |
| `thinking_include_thoughts` | `bool \| None` | `True` / `False` | Include thinking steps in the response. |

=== "Named level (thinking_level)"

    ```python linenums="1"
    from llmfy import GoogleAIModel, GoogleAIConfig, LLMfy

    config = GoogleAIConfig(
        enable_thinking=True,
        thinking_level="HIGH",
    )

    llm = GoogleAIModel(model="gemini-2.5-flash", config=config)

    agent = LLMfy(llm, system_message="You are a helpful assistant.")
    response = agent.invoke("Explain how transformers work in deep learning.")
    print(response.result.content)
    ```

=== "Token budget (thinking_budget_tokens)"

    ```python linenums="1"
    from llmfy import GoogleAIModel, GoogleAIConfig, LLMfy

    config = GoogleAIConfig(
        enable_thinking=True,
        thinking_budget_tokens=2048,
        thinking_include_thoughts=True,
    )

    llm = GoogleAIModel(model="gemini-2.5-pro", config=config)

    agent = LLMfy(llm, system_message="You are a helpful assistant.")
    response = agent.invoke("Explain how transformers work in deep learning.")
    print(response.result.content)
    ```

=== "Raw ThinkingConfig (backward compat)"

    ```python linenums="1"
    from google.genai import types
    from llmfy import GoogleAIModel, GoogleAIConfig, LLMfy

    config = GoogleAIConfig(
        thinking_config=types.ThinkingConfig(thinking_budget=1024),
    )

    llm = GoogleAIModel(model="gemini-2.5-flash", config=config)

    agent = LLMfy(llm, system_message="You are a helpful assistant.")
    response = agent.invoke("Explain how transformers work in deep learning.")
    print(response.result.content)
    ```

!!! note
    When `thinking_config` (raw) is set, it takes priority over `enable_thinking` and the other unified fields.
