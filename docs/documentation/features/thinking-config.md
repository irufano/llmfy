# Thinking Config

LLMfy provides a grouped `thinking` settings object across all three providers to activate extended thinking / reasoning mode. Each provider has its own `*ThinkingConfig` class with a `enabled` master switch plus additional fields to tune thinking behaviour.

| Provider | Config class | Toggle | Effort control | Budget control |
|----------|-------------|--------|---------------|----------------|
| **Anthropic** (Messages API) | `AnthropicMessagesThinkingConfig` | `thinking.enabled=True` | `thinking.effort` (adaptive) | `thinking.budget_tokens` (extended) |
| **AWS Bedrock** (Claude) | `BedrockThinkingConfig` | `thinking.enabled=True` | `thinking.effort` (adaptive) | `thinking.budget_tokens` (extended) |
| **AWS Bedrock** (Nova 2) | `BedrockThinkingConfig` | `thinking.enabled=True` | `thinking.reasoning_effort` | — |
| **OpenAI** (Chat Completions) | `OpenAIChatThinkingConfig` | `thinking.enabled=True` | `thinking.effort` | — |
| **OpenAI** (Responses API) | `OpenAIResponsesReasoningConfig` | `reasoning.enabled=True` | `reasoning.effort` | — |
| **Google AI** | `GoogleAIThinkingConfig` | `thinking.enabled=True` | `thinking.level` | `thinking.budget_tokens` |

---

## Anthropic (Messages API)

`AnthropicMessagesThinkingConfig` is a direct port of the native Anthropic `thinking` block — it supports the same two thinking modes as Claude models on Bedrock (see below), but has **no `reasoning_effort` field**, since that mechanism is Bedrock/Amazon-Nova-specific with no native Anthropic equivalent.

### Mode 1 — Extended Thinking

Uses a fixed token budget. `budget_tokens` must be strictly less than `max_tokens`.

**Supported models**

| Model | Model ID |
|-------|----------|
| Claude Sonnet 4.5 | `claude-sonnet-4-5-20250929` |
| Claude Haiku 4.5 | `claude-haiku-4-5` |
| Claude Opus 4.5 | `claude-opus-4-5-20251101` |

**`AnthropicMessagesThinkingConfig` fields used**

| Field | Type | Description |
|-------|------|-------------|
| `enabled` | `bool` | Set to `True` to enable. |
| `budget_tokens` | `int \| None` | Max thinking tokens. Min `1024`. |

```python linenums="1"
from llmfy import AnthropicMessagesModel, AnthropicMessagesConfig, AnthropicMessagesThinkingConfig, LLMfy

config = AnthropicMessagesConfig(
    max_tokens=8192,
    thinking=AnthropicMessagesThinkingConfig(
        enabled=True,
        budget_tokens=4000,
    ),
)

llm = AnthropicMessagesModel(model="claude-sonnet-4-5-20250929", config=config)

agent = LLMfy(llm, system_message="You are a helpful assistant.")
response = agent.invoke("Explain the halting problem step by step.")
print(response.result.content)
```

---

### Mode 2 — Adaptive Thinking

For current-generation models. The model dynamically decides when and how much to think, using a named effort level instead of a token budget.

**Supported models**

| Model | Model ID | Notes |
|-------|----------|-------|
| Claude Sonnet 5 | `claude-sonnet-5` | Adaptive only |
| Claude Opus 5 | `claude-opus-5` | Adaptive only |
| Claude Fable 5 | `claude-fable-5` | Adaptive only |

!!! note
    Current-generation models **only** accept `thinking.type='adaptive'`. Leaving `type` unset falls back to extended thinking, which several of these models reject with a `400` error.

**`AnthropicMessagesThinkingConfig` fields used**

| Field | Type | Values | Description |
|-------|------|--------|-------------|
| `enabled` | `bool` | — | Set to `True` to enable. |
| `type` | `str \| None` | `'adaptive'` | Must be set to `'adaptive'` for this mode. |
| `effort` | `str \| None` | `'low'`, `'medium'`, `'high'`, `'xhigh'`, `'max'` | Controls thinking depth. Sent via a top-level `output_config.effort` field, not nested inside `thinking`. |

```python linenums="1"
from llmfy import AnthropicMessagesModel, AnthropicMessagesConfig, AnthropicMessagesThinkingConfig, LLMfy

config = AnthropicMessagesConfig(
    thinking=AnthropicMessagesThinkingConfig(
        enabled=True,
        type="adaptive",
        effort="high",
    ),
)

llm = AnthropicMessagesModel(model="claude-sonnet-5", config=config)

agent = LLMfy(llm, system_message="You are a helpful assistant.")
response = agent.invoke("Solve this step by step: If 3x + 7 = 22, find x.")
print(response.result.content)
```

---

## AWS Bedrock

Bedrock supports three distinct thinking modes depending on the model family, all configured through `BedrockThinkingConfig`.

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
    `temperature`, `top_p`, and `top_k` must be set to `None` on `BedrockConfig` when extended thinking is enabled. The API returns an error if they are present.

**`BedrockThinkingConfig` fields used**

| Field | Type | Description |
|-------|------|-------------|
| `enabled` | `bool` | Set to `True` to enable. |
| `budget_tokens` | `int \| None` | Max thinking tokens. Min `1024`. |

```python linenums="1"
from llmfy import BedrockModel, BedrockConfig, BedrockThinkingConfig, LLMfy

config = BedrockConfig(
    thinking=BedrockThinkingConfig(
        enabled=True,
        budget_tokens=4000,
    ),
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
    Fable 5, Mythos 5, and Opus 4.7 **only** accept `thinking.type='adaptive'`. Sending `thinking.type='enabled'` returns a `400` error.

**`BedrockThinkingConfig` fields used**

| Field | Type | Values | Description |
|-------|------|--------|-------------|
| `enabled` | `bool` | — | Set to `True` to enable. |
| `type` | `str \| None` | `'adaptive'` | Must be set to `'adaptive'` for this mode. |
| `effort` | `str \| None` | `'low'`, `'medium'`, `'high'`, `'max'` | Controls thinking depth. `'max'` is Opus 4.6 only. |

```python linenums="1"
from llmfy import BedrockModel, BedrockConfig, BedrockThinkingConfig, LLMfy

config = BedrockConfig(
    thinking=BedrockThinkingConfig(
        enabled=True,
        type="adaptive",
        effort="high",
    ),
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
    When `thinking.reasoning_effort='high'`, `temperature`, `top_p`, and `max_tokens` on `BedrockConfig` must be set to `None`.

**`BedrockThinkingConfig` fields used**

| Field | Type | Values | Description |
|-------|------|--------|-------------|
| `enabled` | `bool` | — | Set to `True` to enable. |
| `reasoning_effort` | `str \| None` | `'low'`, `'medium'`, `'high'` | Controls reasoning depth. |

```python linenums="1"
from llmfy import BedrockModel, BedrockConfig, BedrockThinkingConfig, LLMfy

config = BedrockConfig(
    thinking=BedrockThinkingConfig(
        enabled=True,
        reasoning_effort="medium",
    ),
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
    thinking=BedrockThinkingConfig(
        enabled=True,
        reasoning_effort="high",
    ),
    temperature=None,  # must be unset for high effort
    top_p=None,
    max_tokens=None,
)
```

---

## OpenAI (Chat Completions)

Reasoning is enabled on o-series models via `OpenAIChatThinkingConfig`. These models always reason internally — `enabled` only controls whether `effort` is sent explicitly; it does not turn reasoning off entirely (the API applies its own default when omitted).

**Supported models**

| Model | Model ID |
|-------|----------|
| o1 | `o1` |
| o1-mini | `o1-mini` |
| o3 | `o3` |
| o3-mini | `o3-mini` |
| o4-mini | `o4-mini` |

**`OpenAIChatThinkingConfig` fields**

| Field | Type | Values | Description |
|-------|------|--------|-------------|
| `enabled` | `bool` | — | Set to `True` to enable. |
| `effort` | `str \| None` | `'low'`, `'medium'`, `'high'` | Defaults to `'medium'` when not set. |

```python linenums="1"
from llmfy import OpenAIChatModel, OpenAIChatConfig, OpenAIChatThinkingConfig, LLMfy

config = OpenAIChatConfig(
    thinking=OpenAIChatThinkingConfig(
        enabled=True,
        effort="high",
    ),
)

llm = OpenAIChatModel(model="o4-mini", config=config)

agent = LLMfy(llm, system_message="You are a helpful assistant.")
response = agent.invoke("What is the time complexity of Dijkstra's algorithm?")
print(response.result.content)
```

---

## OpenAI (Responses API)

Reasoning on `OpenAIResponsesModel` is controlled through `OpenAIResponsesReasoningConfig`, nested under `reasoning` (not `thinking`) since the Responses API itself nests reasoning params under a `reasoning` object. Same o-series/GPT-5.x models as Chat Completions — see the table above.

Unlike `OpenAIChatThinkingConfig`, this adds a `summary` field: the Responses API can return a natural-language summary of the model's internal reasoning, useful for debugging without exposing the raw chain of thought.

**`OpenAIResponsesReasoningConfig` fields**

| Field | Type | Values | Description |
|-------|------|--------|-------------|
| `enabled` | `bool` | — | Set to `True` to enable. |
| `effort` | `str \| None` | `'none'`, `'minimal'`, `'low'`, `'medium'`, `'high'`, `'xhigh'`, `'max'` | Defaults to `'medium'` when not set. Not every value is supported by every model. |
| `summary` | `str \| None` | `'auto'`, `'concise'`, `'detailed'` | Requests a summary of the model's reasoning. Left unset (`None`) omits the field entirely. |

```python linenums="1"
from llmfy import OpenAIResponsesModel, OpenAIResponsesConfig, OpenAIResponsesReasoningConfig, LLMfy

config = OpenAIResponsesConfig(
    reasoning=OpenAIResponsesReasoningConfig(
        enabled=True,
        effort="high",
        summary="concise",
    ),
)

llm = OpenAIResponsesModel(model="gpt-5.6-terra", config=config)

agent = LLMfy(llm, system_message="You are a helpful assistant.")
response = agent.invoke("What is the time complexity of Dijkstra's algorithm?")
print(response.result.content)
```

---

## Google AI

Thinking is controlled through `GoogleAIThinkingConfig`. You can use either a named effort level (`level`) or a token budget (`budget_tokens`).

!!! note
    `gemini-2.5-pro` cannot fully disable thinking — it has a non-zero minimum thinking budget regardless of this config. Only `gemini-2.5-flash` and `gemini-2.5-flash-lite` support a true off state via `budget_tokens=0`.

**Supported models**

| Series | Models |
|--------|--------|
| Gemini 2.5 | `gemini-2.5-pro`, `gemini-2.5-flash`, `gemini-2.5-flash-lite` |
| Gemini 3 | `gemini-3-flash`, `gemini-3.1-pro`, `gemini-3.1-flash-lite`, `gemini-3.5-flash` |

**`GoogleAIThinkingConfig` fields**

| Field | Type | Values | Description |
|-------|------|--------|-------------|
| `enabled` | `bool` | — | Set to `True` to enable. Ignored when `raw` is set. |
| `level` | `str \| None` | `'MINIMAL'`, `'LOW'`, `'MEDIUM'`, `'HIGH'` | Named effort level. Preferred for Gemini 3 series. |
| `budget_tokens` | `int \| None` | e.g. `1024`, `-1` (dynamic), `0` (disable) | Token budget for thinking. Preferred for Gemini 2.5. |
| `include_thoughts` | `bool \| None` | `True` / `False` | Include thinking steps in the response. |
| `raw` | `ThinkingConfig \| None` | — | Pre-built `google.genai.types.ThinkingConfig`. Takes priority over all fields above. |

=== "Named level (level)"

    ```python linenums="1"
    from llmfy import GoogleAIModel, GoogleAIConfig, GoogleAIThinkingConfig, LLMfy

    config = GoogleAIConfig(
        thinking=GoogleAIThinkingConfig(
            enabled=True,
            level="HIGH",
        ),
    )

    llm = GoogleAIModel(model="gemini-2.5-flash", config=config)

    agent = LLMfy(llm, system_message="You are a helpful assistant.")
    response = agent.invoke("Explain how transformers work in deep learning.")
    print(response.result.content)
    ```

=== "Token budget (budget_tokens)"

    ```python linenums="1"
    from llmfy import GoogleAIModel, GoogleAIConfig, GoogleAIThinkingConfig, LLMfy

    config = GoogleAIConfig(
        thinking=GoogleAIThinkingConfig(
            enabled=True,
            budget_tokens=2048,
            include_thoughts=True,
        ),
    )

    llm = GoogleAIModel(model="gemini-2.5-pro", config=config)

    agent = LLMfy(llm, system_message="You are a helpful assistant.")
    response = agent.invoke("Explain how transformers work in deep learning.")
    print(response.result.content)
    ```

=== "Raw ThinkingConfig (backward compat)"

    ```python linenums="1"
    from google.genai import types
    from llmfy import GoogleAIModel, GoogleAIConfig, GoogleAIThinkingConfig, LLMfy

    config = GoogleAIConfig(
        thinking=GoogleAIThinkingConfig(
            raw=types.ThinkingConfig(thinking_budget=1024),
        ),
    )

    llm = GoogleAIModel(model="gemini-2.5-flash", config=config)

    agent = LLMfy(llm, system_message="You are a helpful assistant.")
    response = agent.invoke("Explain how transformers work in deep learning.")
    print(response.result.content)
    ```

!!! note
    When `thinking.raw` is set, it takes priority over `enabled` and the other unified fields.
