# Prompt Caching

LLMfy provides a unified `enable_prompt_caching` flag across all three providers to reduce costs when the same large context (system prompt, documents, conversation history) is reused across requests.

| Provider | Mechanism | Min tokens | Default TTL | Savings |
|----------|-----------|------------|-------------|---------|
| **AWS Bedrock** | `cachePoint` markers injected automatically | 1,024–4,096 | 5 min | ~90% on cached reads |
| **OpenAI** | Fully automatic — no markers needed | 1,024 | 5–10 min rolling | ~50% on cached tokens |
| **Google AI** | Explicit: pre-created cache object; Implicit: auto on Gemini 2.5+ | 2,048–4,096 | 1 hour (no bounds) | ~75% explicit / reduced implicit |

---

## AWS Bedrock

When `enable_prompt_caching=True`, llmfy automatically injects `cachePoint` markers into:

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
    Amazon Nova (`amazon.nova-lite-v1:0`, `amazon.nova-pro-v1:0`) cache text prompts automatically without any `cachePoint` marker. `enable_prompt_caching=True` has no effect on Nova models.

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

### Config fields

| Field | Type | Values | Description |
|-------|------|--------|-------------|
| `enable_prompt_caching` | `bool` | — | Set to `True` to inject `cachePoint` markers. |
| `prompt_caching_ttl` | `str \| None` | `"5m"`, `"1h"` | Cache TTL. Defaults to `"5m"`. `"1h"` is only supported on Claude 4.5, 4.6, 4.8, and Fable 5. |

=== "Default TTL (5 minutes)"

    ```python linenums="1"
    from llmfy import BedrockModel, BedrockConfig, LLMfy

    config = BedrockConfig(
        enable_prompt_caching=True,
    )

    llm = BedrockModel(
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
    from llmfy import BedrockModel, BedrockConfig, LLMfy

    config = BedrockConfig(
        enable_prompt_caching=True,
        prompt_caching_ttl="1h",  # only Claude 4.5, 4.6, 4.8, Fable 5
    )

    llm = BedrockModel(
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
from llmfy import BedrockModel, BedrockConfig, LLMfy, llmfy_usage_tracker

config = BedrockConfig(enable_prompt_caching=True)
llm = BedrockModel(model="anthropic.claude-sonnet-4-6", config=config)
agent = LLMfy(llm, system_message="You are a helpful assistant.")

with llmfy_usage_tracker() as usage:
    agent.invoke("What is the capital of France?")
    agent.invoke("What is the capital of Germany?")  # system served from cache

print(usage)
# cache_read_tokens and cache_write_tokens appear in Request Details when non-zero
```

---

## OpenAI

OpenAI applies caching automatically — no code changes or markers are required. The `enable_prompt_caching` flag is **informational only**; it signals intent and ensures `cache_read_tokens` are tracked in usage details.

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

!!! warning "Not supported"
    `gpt-3.5-turbo`, `gpt-4` (non-turbo), and older generation models do not support automatic prompt caching.

### Cache TTL

| Type | Duration |
|------|----------|
| Standard | 5–10 minutes of inactivity; maximum 1 hour |
| Extended | Up to 24 hours (`gpt-5.5`, `gpt-5.5-pro`, `gpt-5.4`, `gpt-5.2`, `gpt-5.1`, `gpt-5`, `gpt-4.1`) |

!!! note "Minimum tokens"
    Caching only activates for prompts containing **at least 1,024 tokens**. Shorter prompts are never cached.

### Config fields

| Field | Type | Description |
|-------|------|-------------|
| `enable_prompt_caching` | `bool` | Intent flag. Does not alter the request. Enables cache token reporting in usage details. |

```python linenums="1"
from llmfy import OpenAIModel, OpenAIConfig, LLMfy, llmfy_usage_tracker

config = OpenAIConfig(
    enable_prompt_caching=True,
)

llm = OpenAIModel(model="gpt-4o", config=config)
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

1. **Explicit caching** — you create a cache object externally and reference it via `cached_content`. Cache hits are **guaranteed** and billed at the reduced rate.
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

### Config fields

| Field | Type | Description |
|-------|------|-------------|
| `enable_prompt_caching` | `bool` | Intent flag. Does not alter the request on its own. |
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
from llmfy import GoogleAIModel, GoogleAIConfig, LLMfy, llmfy_usage_tracker

config = GoogleAIConfig(
    enable_prompt_caching=True,
    cached_content="cachedContents/abc123efg456",  # name from Step 1
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
    from llmfy import BedrockModel, BedrockConfig, LLMfy

    config = BedrockConfig(enable_prompt_caching=True)
    llm = BedrockModel(model="anthropic.claude-sonnet-4-20250514-v1:0", config=config)

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
    from llmfy import BedrockModel, BedrockConfig, LLMfy

    config = BedrockConfig(enable_prompt_caching=True)
    llm = BedrockModel(model="anthropic.claude-sonnet-4-20250514-v1:0", config=config)

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
    Use `enable_prompt_caching=True` when the system prompt is **large (hundreds to thousands of tokens) and constant** across many calls. Large stable content like reference documents, knowledge bases, or detailed instructions benefit the most.

---

## Usage Tracking

Cache token counts are exposed in `usage.to_dict()["details"]` and shown in `repr(usage)` when non-zero. They do **not** double-count against the top-level `input_tokens` total.

| Field | Providers | Meaning |
|-------|-----------|---------|
| `cache_read_tokens` | Bedrock, OpenAI, Google | Tokens served from cache this request |
| `cache_write_tokens` | Bedrock only | Tokens written to cache this request (~125% input rate) |

```python linenums="1"
from llmfy import BedrockModel, BedrockConfig, LLMfy, llmfy_usage_tracker

config = BedrockConfig(enable_prompt_caching=True)
llm = BedrockModel(model="anthropic.claude-sonnet-4-6", config=config)
agent = LLMfy(llm, system_message="You are a helpful assistant.")

with llmfy_usage_tracker() as usage:
    agent.invoke("What is 2 + 2?")

data = usage.to_dict()
for detail in data["details"]:
    print("cache_read_tokens :", detail.get("cache_read_tokens", 0))
    print("cache_write_tokens:", detail.get("cache_write_tokens", 0))
```
