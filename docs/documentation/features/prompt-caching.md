# Prompt Caching

LLMfy provides a grouped `prompt_caching` settings object across all three providers to reduce costs when the same large context (system prompt, documents, conversation history) is reused across requests.

| Provider | Config class | Mechanism | Min tokens | Default TTL | Savings |
|----------|-------------|-----------|------------|-------------|---------|
| **Anthropic** (Messages API) | `AnthropicMessagesPromptCachingConfig` | Inline `cache_control` markers injected on the last content block | 1,024–4,096 | 5 min (or 1h) | ~90% on cached reads |
| **AWS Bedrock** | `BedrockConversePromptCachingConfig` | `cachePoint` markers injected automatically | 1,024–4,096 | 5 min | ~90% on cached reads |
| **OpenAI** (Chat Completions) | `OpenAIChatPromptCachingConfig` | Fully automatic — no markers needed | 1,024 | 5–10 min rolling | ~50% pre-GPT-5.6 / ~90% GPT-5.6+ on cached reads |
| **OpenAI** (Responses API) | `OpenAIResponsesPromptCachingConfig` | Fully automatic — no markers needed | 1,024 | 5–10 min rolling | Same as Chat Completions — pricing is per-model, not per-endpoint |
| **Google AI** | `GoogleAIPromptCachingConfig` | Explicit: pre-created cache object; Implicit: auto on Gemini 2.5+ | 2,048–4,096 | 1 hour (no bounds) | ~75% explicit / reduced implicit |

---

## Anthropic (Messages API)

When `prompt_caching.enabled=True`, llmfy injects an inline `cache_control` key directly onto the **last content block** of:

- The **system** prompt (when present) — since Anthropic's render order is `tools → system → messages` and caching is a byte-prefix match, caching the end of `system` implicitly caches `tools + system` together.
- The **last message** (grows the cached conversation prefix each turn).

This is a different mechanism from Bedrock's Converse API, which injects a sibling `cachePoint` block instead of an inline key — the two are not wire-compatible, even though both ultimately cache the same underlying Claude model.

### Supported models

| Model | Model ID | Min tokens | TTL support |
|-------|----------|------------|-------------|
| Claude Sonnet 4.5 | `claude-sonnet-4-5-20250929` | 4,096 | 5m and 1h |
| Claude Haiku 4.5 | `claude-haiku-4-5` | 4,096 | 5m and 1h |
| Claude Opus 4.5 | `claude-opus-4-5-20251101` | 4,096 | 5m and 1h |
| Claude Sonnet 5 | `claude-sonnet-5` | 1,024 | 5m and 1h |
| Claude Opus 5 | `claude-opus-5` | 1,024 | 5m and 1h |
| Claude Fable 5 | `claude-fable-5` | 1,024 | 5m and 1h |

!!! info "Minimum cacheable prefix"
    The minimum cacheable prefix is model-dependent (as low as 1,024 tokens on current models, up to 4,096 on some others). Shorter prefixes silently don't cache — no error, `cache_creation_input_tokens` is just `0`.

### Pricing

| Item | Cost |
|------|------|
| Cache reads | ~10% of normal input price (~90% savings) |
| Cache writes (5m TTL) | ~125% of normal input price (one-time, on first write) |
| Cache writes (1h TTL) | ~200% of normal input price (one-time, on first write) |
| Uncached tokens | Billed at the standard rate |

!!! note "TTL pricing simplification"
    `ModelPricing.cache_write` has no TTL dimension, so `ANTHROPIC_PRICING` relies on the same 125% default fallback regardless of TTL (matching `BedrockConversePromptCachingConfig`'s simplification). Set `cache_write` explicitly per model via a custom `llmfy_usage_tracker(anthropic_pricing=...)` dict if you need the 1-hour ~200% premium modeled precisely.

### `AnthropicMessagesPromptCachingConfig` fields

| Field | Type | Values | Description |
|-------|------|--------|-------------|
| `enabled` | `bool` | — | Set to `True` to inject `cache_control` markers. |
| `ttl` | `str \| None` | `"5m"`, `"1h"` | Cache TTL. Defaults to `"5m"` when unset. |

=== "Default TTL (5 minutes)"

    ```python linenums="1"
    from llmfy import AnthropicMessagesModel, AnthropicMessagesConfig, AnthropicMessagesPromptCachingConfig, LLMfy

    config = AnthropicMessagesConfig(
        prompt_caching=AnthropicMessagesPromptCachingConfig(enabled=True),
    )

    llm = AnthropicMessagesModel(
        model="claude-sonnet-5",
        config=config,
    )

    agent = LLMfy(
        llm,
        system_message="You are an expert analyst. " + open("large_document.txt").read(),
    )

    # First call — caches system + message prefix
    response = agent.invoke("Summarize the key points.")
    print(response.result.content)

    # Second call — system served from cache (~90% cheaper)
    response = agent.invoke("What are the risks mentioned?")
    print(response.result.content)
    ```

=== "Extended TTL (1 hour)"

    ```python linenums="1"
    from llmfy import AnthropicMessagesModel, AnthropicMessagesConfig, AnthropicMessagesPromptCachingConfig, LLMfy

    config = AnthropicMessagesConfig(
        prompt_caching=AnthropicMessagesPromptCachingConfig(
            enabled=True,
            ttl="1h",
        ),
    )

    llm = AnthropicMessagesModel(
        model="claude-sonnet-5",
        config=config,
    )

    agent = LLMfy(
        llm,
        system_message="You are an expert analyst. " + open("large_document.txt").read(),
    )

    response = agent.invoke("Summarize the key points.")
    print(response.result.content)
    ```

### Cache usage in usage tracking

```python linenums="1"
from llmfy import AnthropicMessagesModel, AnthropicMessagesConfig, AnthropicMessagesPromptCachingConfig, LLMfy, llmfy_usage_tracker

config = AnthropicMessagesConfig(prompt_caching=AnthropicMessagesPromptCachingConfig(enabled=True))
llm = AnthropicMessagesModel(model="claude-sonnet-5", config=config)
agent = LLMfy(llm, system_message="You are a helpful assistant.")

with llmfy_usage_tracker() as usage:
    agent.invoke("What is the capital of France?")
    agent.invoke("What is the capital of Germany?")  # system served from cache

print(usage)
# cache_read_tokens and cache_write_tokens appear in Request Details when non-zero
```

---

## AWS Bedrock

When `prompt_caching.enabled=True`, llmfy automatically injects `cachePoint` markers into:

- The end of the **system** array (caches the system prompt)
- The end of the **last message** content (caches the full conversation prefix for the next turn)

### Supported models

| Model | Model ID | Min tokens | TTL support |
|-------|----------|------------|-------------|
| Claude 3.5 Sonnet v2 | `anthropic.claude-3-5-sonnet-20241022-v2:0` | 1,024 | 5m only |
| Claude 3.7 Sonnet | `anthropic.claude-3-7-sonnet-20250219-v1:0` | 1,024 | 5m only |
| Claude Opus 4 | `anthropic.claude-opus-4-20250514-v1:0` | 1,024 | 5m only |
| Claude Haiku 4.5 | `anthropic.claude-haiku-4-5-20251001-v1:0` | 4,096 | 5m and 1h |
| Claude Sonnet 4.5 | `anthropic.claude-sonnet-4-5-20250929-v1:0` | 4,096 | 5m and 1h |
| Claude Opus 4.5 | `anthropic.claude-opus-4-5-20251101-v1:0` | 4,096 | 5m and 1h |
| Claude Sonnet 4.6 | `anthropic.claude-sonnet-4-6` | 1,024 | 5m and 1h |
| Claude Opus 4.6 | `anthropic.claude-opus-4-6-v1` | 1,024 | 5m and 1h |
| Claude Opus 4.8 | `anthropic.claude-opus-4-8` | 4,096 | 5m and 1h |
| Claude Fable 5 | `anthropic.claude-fable-5` | 1,024 | 5m and 1h |

Cross-region inference IDs (`us.`, `eu.`, `ap.` prefixes) are also supported, e.g. `us.anthropic.claude-3-5-sonnet-20241022-v2:0`.

!!! info "Amazon Nova — automatic caching"
    Amazon Nova (`amazon.nova-lite-v1:0`, `amazon.nova-pro-v1:0`) cache text prompts automatically without any `cachePoint` marker. `prompt_caching.enabled=True` has no effect on Nova models.

!!! warning "Not supported"
    Meta Llama, DeepSeek, Mistral, and other non-Claude models on Bedrock do not support `cachePoint`. Prompt caching is exclusive to Anthropic Claude on Bedrock.

### Pricing

| Item | Cost |
|------|------|
| Cache reads | ~10% of normal input price (~90% savings) |
| Cache writes | ~125% of normal input price (one-time, on first write) |
| Uncached tokens | Billed at the standard rate |

!!! note "Batch API"
    Prompt caching is only available with on-demand inference. It is **not** compatible with the Bedrock Batch API.

### `BedrockConversePromptCachingConfig` fields

| Field | Type | Values | Description |
|-------|------|--------|-------------|
| `enabled` | `bool` | — | Set to `True` to inject `cachePoint` markers. |
| `ttl` | `str \| None` | `"5m"`, `"1h"` | Cache TTL. Defaults to `"5m"`. `"1h"` is only supported on Claude 4.5, 4.6, 4.8, and Fable 5. |

=== "Default TTL (5 minutes)"

    ```python linenums="1"
    from llmfy import BedrockConverseModel, BedrockConverseConfig, BedrockConversePromptCachingConfig, LLMfy

    config = BedrockConverseConfig(
        prompt_caching=BedrockConversePromptCachingConfig(enabled=True),
    )

    llm = BedrockConverseModel(
        model="anthropic.claude-3-5-sonnet-20241022-v2:0",
        config=config,
    )

    agent = LLMfy(
        llm,
        system_message="You are an expert analyst. " + open("large_document.txt").read(),
    )

    # First call — caches system + message prefix
    response = agent.invoke("Summarize the key points.")
    print(response.result.content)

    # Second call — system served from cache (~90% cheaper)
    response = agent.invoke("What are the risks mentioned?")
    print(response.result.content)
    ```

=== "Extended TTL (1 hour)"

    ```python linenums="1"
    from llmfy import BedrockConverseModel, BedrockConverseConfig, BedrockConversePromptCachingConfig, LLMfy

    config = BedrockConverseConfig(
        prompt_caching=BedrockConversePromptCachingConfig(
            enabled=True,
            ttl="1h",  # only Claude 4.5, 4.6, 4.8, Fable 5
        ),
    )

    llm = BedrockConverseModel(
        model="anthropic.claude-sonnet-4-5-20250929-v1:0",
        config=config,
    )

    agent = LLMfy(
        llm,
        system_message="You are an expert analyst. " + open("large_document.txt").read(),
    )

    response = agent.invoke("Summarize the key points.")
    print(response.result.content)
    ```

### Cache usage in usage tracking

When `llmfy_usage_tracker()` is active, cache token counts appear in the `details` list:

```python linenums="1"
from llmfy import BedrockConverseModel, BedrockConverseConfig, BedrockConversePromptCachingConfig, LLMfy, llmfy_usage_tracker

config = BedrockConverseConfig(prompt_caching=BedrockConversePromptCachingConfig(enabled=True))
llm = BedrockConverseModel(model="anthropic.claude-sonnet-4-6", config=config)
agent = LLMfy(llm, system_message="You are a helpful assistant.")

with llmfy_usage_tracker() as usage:
    agent.invoke("What is the capital of France?")
    agent.invoke("What is the capital of Germany?")  # system served from cache

print(usage)
# cache_read_tokens and cache_write_tokens appear in Request Details when non-zero
```

---

## OpenAI (Chat Completions)

OpenAI applies caching automatically — no code changes or markers are required. `prompt_caching.enabled` is **informational only**; it signals intent and ensures `cache_read_tokens` are tracked in usage details.

### How it works

- The longest common prompt **prefix** is cached server-side on every API call.
- Subsequent requests that share the same prefix pay a reduced token price automatically.
- Static content (system prompt, document context) must appear **at the beginning** of the prompt.
- Images and tool definitions must be identical across requests for the cache to apply.

### Supported models

| Family | Models |
|--------|--------|
| GPT-4o | `gpt-4o`, `gpt-4o-mini` (and all dated snapshots) |
| GPT-4.1 | `gpt-4.1`, `gpt-4.1-mini`, `gpt-4.1-nano` |
| o-series | `o1`, `o1-mini`, `o3`, `o3-mini`, `o3-pro`, `o4-mini` |
| GPT-5 (24h TTL) | `gpt-5`, `gpt-5.1`, `gpt-5.2`, `gpt-5.4`, `gpt-5.5`, `gpt-5.5-pro` |
| GPT-5.6 (24h TTL, cache writes billed) | `gpt-5.6-sol`, `gpt-5.6-terra`, `gpt-5.6-luna` |

!!! warning "Not supported"
    `gpt-3.5-turbo`, `gpt-4` (non-turbo), and older generation models do not support automatic prompt caching.

### Cache TTL

| Type | Duration |
|------|----------|
| Standard | 5–10 minutes of inactivity; maximum 1 hour |
| Extended | Up to 24 hours (`gpt-5.5`, `gpt-5.5-pro`, `gpt-5.4`, `gpt-5.2`, `gpt-5.1`, `gpt-5`, `gpt-4.1`) |

!!! note "Minimum tokens"
    Caching only activates for prompts containing **at least 1,024 tokens**. Shorter prompts are never cached.

### Pricing

The cache-read discount is **not** the same across all model generations — check the rate for your specific model in `OPENAI_PRICING` before relying on the numbers below.

| Item | Cost |
|------|------|
| Cache reads — `gpt-4o`, `gpt-4.1`, o-series | 50% of normal input price |
| Cache reads — GPT-5.6 family and later | 10% of normal input price (~90% savings) |
| Cache writes — GPT-5.6 family and later | 125% of normal input price (reported in `cache_write_tokens`) |
| Cache writes — pre-GPT-5.6 models | No additional fee |
| Uncached tokens | Billed at the standard rate |

### `OpenAIChatPromptCachingConfig` fields

| Field | Type | Description |
|-------|------|-------------|
| `enabled` | `bool` | Intent flag. Does not alter the request. Enables cache token reporting in usage details. |

```python linenums="1"
from llmfy import OpenAIChatModel, OpenAIChatConfig, OpenAIChatPromptCachingConfig, LLMfy, llmfy_usage_tracker

config = OpenAIChatConfig(
    prompt_caching=OpenAIChatPromptCachingConfig(enabled=True),
)

llm = OpenAIChatModel(model="gpt-4o", config=config)
agent = LLMfy(llm, system_message="You are a helpful assistant.")

with llmfy_usage_tracker() as usage:
    # Both calls share the same large system prompt prefix
    agent.invoke("What is the capital of France?")
    agent.invoke("What is the capital of Germany?")

print(usage)
# cache_read_tokens appears in Request Details when the prefix was served from cache
```

---

## OpenAI (Responses API)

Same automatic, marker-free caching as Chat Completions above — same models, TTLs, and pricing (pricing is tracked per-model, not per-endpoint, so `OpenAIChatModel` and `OpenAIResponsesModel` share the same rate table). The only difference is the config class name, since it lives alongside `OpenAIResponsesModel`'s other Responses-specific settings.

### `OpenAIResponsesPromptCachingConfig` fields

| Field | Type | Description |
|-------|------|-------------|
| `enabled` | `bool` | Intent flag. Does not alter the request. Enables cache token reporting in usage details. |

```python linenums="1"
from llmfy import OpenAIResponsesModel, OpenAIResponsesConfig, OpenAIResponsesPromptCachingConfig, LLMfy, llmfy_usage_tracker

config = OpenAIResponsesConfig(
    prompt_caching=OpenAIResponsesPromptCachingConfig(enabled=True),
)

llm = OpenAIResponsesModel(model="gpt-4o", config=config)
agent = LLMfy(llm, system_message="You are a helpful assistant.")

with llmfy_usage_tracker() as usage:
    # Both calls share the same large system prompt prefix
    agent.invoke("What is the capital of France?")
    agent.invoke("What is the capital of Germany?")

print(usage)
# cache_read_tokens appears in Request Details when the prefix was served from cache
```

---

## Google AI

Google AI supports two caching modes:

1. **Explicit caching** — you create a cache object externally and reference it via `prompt_caching.cached_content`. Cache hits are **guaranteed** and billed at the reduced rate.
2. **Implicit caching** — enabled by default on all Gemini 2.5+ models with no setup. Cache hits are **not guaranteed** but apply a billing benefit when they occur.

### Supported models (explicit caching)

| Model | Model ID | Min tokens |
|-------|----------|------------|
| Gemini 2.5 Pro | `models/gemini-2.5-pro` | 2,048 |
| Gemini 2.5 Flash | `models/gemini-2.5-flash` | 2,048 |
| Gemini 3.1 Pro Preview | `models/gemini-3.1-pro-preview` | 4,096 |
| Gemini 3.5 Flash | `models/gemini-3.5-flash` | 4,096 |

!!! info "Implicit caching"
    All **Gemini 2.5 and newer** models have implicit caching enabled by default. No `cached_content` is required; savings are applied automatically when a cache hit occurs.

!!! warning "Not supported"
    `gemini-2.0-flash-lite`, `gemini-3.x` preview/pre-GA models, and embedding models (`gemini-embedding-*`) do not support explicit context caching.

### Pricing

| Item | Cost |
|------|------|
| Explicit cache reads | ~25% of normal input price (~75% savings) |
| Implicit cache reads | Reduced rate when a hit occurs (no guarantee) |
| Cache storage | Charged per token-hour (varies by model) |

### Cache TTL

- **Default**: 1 hour
- **Minimum / Maximum**: No enforced bounds — set any value (e.g. `"300s"`, `"3600s"`)

### `GoogleAIPromptCachingConfig` fields

| Field | Type | Description |
|-------|------|-------------|
| `enabled` | `bool` | Intent flag. Does not alter the request on its own. |
| `cached_content` | `str \| None` | Resource name of a pre-created cache object, e.g. `'cachedContents/abc123'`. When set, the cache is passed to `GenerateContentConfig` automatically. |

### Step 1 — Create the cache

Create the cache once externally before running requests. The model in `caches.create()` must **exactly match** the model used for generation.

```python linenums="1"
from google import genai
from google.genai import types

client = genai.Client(api_key="YOUR_GOOGLE_API_KEY")

cache = client.caches.create(
    model="models/gemini-2.5-flash",   # must match generation model
    config=types.CreateCachedContentConfig(
        system_instruction="You are an expert analyst.",
        contents=["<large document text here>"],
        ttl="3600s",  # 1 hour cache lifetime
    ),
)

print(cache.name)  # e.g. 'cachedContents/abc123efg456'
```

### Step 2 — Use the cache in requests

```python linenums="1"
from llmfy import GoogleAIModel, GoogleAIConfig, GoogleAIPromptCachingConfig, LLMfy, llmfy_usage_tracker

config = GoogleAIConfig(
    prompt_caching=GoogleAIPromptCachingConfig(
        enabled=True,
        cached_content="cachedContents/abc123efg456",  # name from Step 1
    ),
)

llm = GoogleAIModel(model="gemini-2.5-flash", config=config)

# Note: do NOT repeat the cached content in system_message —
# it is already inside the cache object
agent = LLMfy(llm)

with llmfy_usage_tracker() as usage:
    response = agent.invoke("Summarize the key findings.")
    print(response.result.content)

print(usage)
# cache_read_tokens appears in Request Details when explicit caching is active
```

!!! warning "Do not repeat cached content"
    Do not include the cached system prompt or documents in the request body (`system_message`, `messages`). Only pass the **question or instruction** — the cached content is already injected by the API.

---

## Dynamic Variables and Caching

LLMfy supports template variables in the system message using `{{variable_name}}` syntax. Understanding how this interacts with caching is important to get the expected cost savings.

### How it works

Template substitution happens **before** `generate()` is called. By the time the `cachePoint` is injected, the system prompt already contains the resolved value. No error or duplication occurs — but caching effectiveness depends on how often the resolved value changes.

### Cache behaviour with dynamic variables

Each provider caches based on a **byte-identical prefix match**. If the resolved system prompt changes between calls, the cache prefix changes and a new cache entry is created.

```
T+0:00  Call 1: language="Python"      → cache WRITE (new prefix, miss)
T+0:30  Call 2: language="JavaScript"  → cache WRITE (different prefix, separate cache)
T+1:00  Call 3: language="Python"      → cache READ  ✅ (same as Call 1, still within TTL)
T+6:00  Call 4: language="Python"      → cache WRITE (Call 1 cache expired after 5 min)
```

Call 3 **does** get a cache hit from Call 1 as long as the same value is reused within the TTL window. The problem arises when:

| Problem | Effect |
|---------|--------|
| **Cache fragmentation** | Each unique variable value creates a separate cache entry. Many unique values → many writes, few reads |
| **TTL expiry** | If the same value is not reused within TTL (5 min default), the cache expires and the next call pays write cost again |
| **Diminishing returns** | A small system prompt with a changing variable saves very few tokens even on a hit |

### When dynamic variables are safe to cache

| Scenario | Caching effective? |
|----------|-------------------|
| Large stable text + small dynamic variable | ✅ Yes — most tokens are stable, few unique variants |
| Same variable value repeated many times within TTL | ✅ Yes — cache reused effectively |
| Small system prompt with frequently changing variable | ❌ No — mostly writes, few reads |
| Many unique variable values, rarely repeated | ❌ No — each unique value creates its own cache entry |

### Recommended pattern

Move the **dynamic part into the user message**. Keep only the **large stable content** in the system prompt so the cache prefix stays constant across calls.

=== "✅ Recommended"

    ```python linenums="1"
    from llmfy import BedrockConverseModel, BedrockConverseConfig, BedrockConversePromptCachingConfig, LLMfy

    config = BedrockConverseConfig(prompt_caching=BedrockConversePromptCachingConfig(enabled=True))
    llm = BedrockConverseModel(model="anthropic.claude-sonnet-4-20250514-v1:0", config=config)

    # Large stable knowledge base in the system prompt — always cached
    agent = LLMfy(
        llm,
        system_message="You are a programming expert.\n\n" + large_reference_document,
    )

    # Dynamic part goes in the query — does not affect the cache prefix
    response = agent.invoke(f"Explain closures using a {language} example.")
    ```

=== "❌ Avoid"

    ```python linenums="1"
    from llmfy import BedrockConverseModel, BedrockConverseConfig, BedrockConversePromptCachingConfig, LLMfy

    config = BedrockConverseConfig(prompt_caching=BedrockConversePromptCachingConfig(enabled=True))
    llm = BedrockConverseModel(model="anthropic.claude-sonnet-4-20250514-v1:0", config=config)

    # Dynamic variable in the system prompt — different value = different cache prefix
    agent = LLMfy(
        llm,
        system_message="You are a {{language}} expert.",
        input_variables=["language"],
    )

    # Each unique language creates its own cache entry
    response = agent.invoke("Explain closures.", language="Python")
    response = agent.invoke("Explain closures.", language="Go")  # new cache, no hit
    ```

!!! tip "Best practice"
    Use `prompt_caching=BedrockConversePromptCachingConfig(enabled=True)` (or the equivalent for OpenAI/Google) when the system prompt is **large (hundreds to thousands of tokens) and constant** across many calls. Large stable content like reference documents, knowledge bases, or detailed instructions benefit the most.

---

## Usage Tracking

Cache token counts are exposed in `usage.to_dict()["details"]` and shown in `repr(usage)` when non-zero. They do **not** double-count against the top-level `input_tokens` total.

| Field | Providers | Meaning |
|-------|-----------|---------|
| `cache_read_tokens` | Anthropic, Bedrock, OpenAI, Google | Tokens served from cache this request |
| `cache_write_tokens` | Anthropic, Bedrock, OpenAI (GPT-5.6+ only) | Tokens written to cache this request (Anthropic: ~125%/~200% input rate for 5m/1h TTL; Bedrock: ~125% input rate; OpenAI GPT-5.6+: 125% input rate; 0 on older OpenAI models, which have no write fee) |

```python linenums="1"
from llmfy import BedrockConverseModel, BedrockConverseConfig, BedrockConversePromptCachingConfig, LLMfy, llmfy_usage_tracker

config = BedrockConverseConfig(prompt_caching=BedrockConversePromptCachingConfig(enabled=True))
llm = BedrockConverseModel(model="anthropic.claude-sonnet-4-6", config=config)
agent = LLMfy(llm, system_message="You are a helpful assistant.")

with llmfy_usage_tracker() as usage:
    agent.invoke("What is 2 + 2?")

data = usage.to_dict()
for detail in data["details"]:
    print("cache_read_tokens :", detail.get("cache_read_tokens", 0))
    print("cache_write_tokens:", detail.get("cache_write_tokens", 0))
```
