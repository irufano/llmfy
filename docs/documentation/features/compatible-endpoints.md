# Compatible Endpoints (`base_url`)

`AnthropicMessagesModel`, `OpenAIChatModel`, and `OpenAIResponsesModel` don't hardcode a vendor endpoint. Their constructors just forward `api_key`, `base_url`, and `default_headers` straight into the official SDK client:

```python
# AnthropicMessagesModel.__init__
self.client = anthropic.Anthropic(api_key=api_key, base_url=base_url, default_headers=default_headers)

# OpenAIChatModel.__init__ / OpenAIResponsesModel.__init__
self.client = openai.OpenAI(api_key=api_key, base_url=base_url, default_headers=default_headers)
```

Because of that, **any provider exposing an API compatible with the Anthropic Messages API, OpenAI Chat Completions API, or OpenAI Responses API spec** can be used through llmfy — not just Anthropic/OpenAI themselves — with no code changes to the library.

!!! note "Not every provider class supports this"
    `BedrockModel` and `GoogleAIModel` are **not** part of this mechanism — they authenticate via AWS SigV4 / Google's own SDK conventions, which have no simple bearer-token `base_url` override.

---

## Why it works: auth cheat sheet

Each SDK sends a fixed auth header shape regardless of what `base_url` points at. A provider only "just works" via `api_key`/`base_url` if it accepts that exact shape:

| Model class | SDK | Header(s) sent automatically | `base_url` must stop before |
|---|---|---|---|
| `OpenAIChatModel` | `openai.OpenAI` | `Authorization: Bearer <api_key>` | `/chat/completions` (i.e. `base_url` ends in `.../v1`) |
| `OpenAIResponsesModel` | `openai.OpenAI` | `Authorization: Bearer <api_key>` | `/responses` (i.e. `base_url` ends in `.../v1`) |
| `AnthropicMessagesModel` | `anthropic.Anthropic` | `x-api-key: <api_key>` + a fixed `anthropic-version` header | `/v1/messages` (SDK appends this itself) |

If a provider needs *extra* headers on top of that fixed shape — e.g. a workspace/project-scoping header — pass `default_headers={"header-name": "value"}`, forwarded as-is to the SDK client. If a provider needs a *different* auth scheme entirely (a different header name in place of `Authorization`/`x-api-key`, query-string keys, or AWS SigV4 signing), `api_key`/`base_url`/`default_headers` aren't enough — none of the three model classes expose a way to swap the SDK's underlying auth mechanism or plug in a custom `httpx` client.

---

## Example: AWS Bedrock via `bedrock-mantle`

AWS Bedrock's [`bedrock-mantle` endpoint](https://docs.aws.amazon.com/bedrock/latest/userguide/bedrock-mantle.html) exposes OpenAI-compatible Chat Completions/Responses APIs and an Anthropic-compatible Messages API, authenticated with a [Bedrock API key](https://docs.aws.amazon.com/bedrock/latest/userguide/api-keys.html) (a bearer token) instead of SigV4. It matches the auth cheat sheet above exactly:

- OpenAI-compatible APIs → `Authorization: Bearer <bedrock-api-key>`
- Anthropic-compatible Messages API → `x-api-key: <bedrock-api-key>` + `anthropic-version: 2023-06-01`

!!! tip "Runnable example"
    A complete, runnable script covering all three APIs is at [Compatible Endpoints — AWS Bedrock Mantle Example](../../examples/example-bedrock-mantle.md) (source: `llmfy/example/bedrock_mantle_example.py`).

### 1. Chat Completions

```python linenums="1"
from llmfy import OpenAIChatModel, OpenAIChatConfig, LLMfy

BEDROCK_REGION = "us-east-1"
BEDROCK_API_KEY = "..."  # short-term or long-term Bedrock API key

llm = OpenAIChatModel(
    model="anthropic.claude-sonnet-4-6-v1",  # Bedrock-style model ID, not "claude-sonnet-5"
    config=OpenAIChatConfig(temperature=0.7),
    api_key=BEDROCK_API_KEY,
    base_url=f"https://bedrock-mantle.{BEDROCK_REGION}.api.aws/v1",
)

agent = LLMfy(llm, system_message="You are a helpful assistant.")
result = agent.invoke("Explain quantum computing in one sentence.")
print(result.result.content)
```

### 2. Responses API

```python linenums="1"
from llmfy import OpenAIResponsesModel, OpenAIResponsesConfig, LLMfy

llm = OpenAIResponsesModel(
    model="openai.gpt-oss-120b",  # a model actually hosted on bedrock-mantle
    config=OpenAIResponsesConfig(temperature=0.7),
    api_key=BEDROCK_API_KEY,
    base_url=f"https://bedrock-mantle.{BEDROCK_REGION}.api.aws/v1",
)

agent = LLMfy(llm, system_message="You are a helpful assistant.")
result = agent.invoke("Tell me a short story about clouds.")
print(result.result.content)
```

### 3. Anthropic Messages API

The Anthropic SDK appends `/v1/messages` to `base_url` itself, and Bedrock's actual path is `/anthropic/v1/messages` — so `base_url` must stop at `.../anthropic`, not `.../anthropic/v1`:

```python linenums="1"
from llmfy import AnthropicMessagesModel, AnthropicMessagesConfig, LLMfy

llm = AnthropicMessagesModel(
    model="anthropic.claude-sonnet-4-6-v1",
    config=AnthropicMessagesConfig(max_tokens=4096, temperature=0.7),
    api_key=BEDROCK_API_KEY,
    base_url=f"https://bedrock-mantle.{BEDROCK_REGION}.api.aws/anthropic",
)

agent = LLMfy(llm, system_message="You are a helpful assistant.")
result = agent.invoke("Explain quantum computing in one sentence.")
print(result.result.content)
```

### 4. Streaming + usage tracking with custom pricing

Built-in pricing tables don't know Bedrock's model IDs or rates, so wrap calls in `llmfy_usage_tracker` with a custom pricing dict (see [Usage Tracking](usage.md#customize-prices-data)):

```python linenums="1"
from llmfy import AnthropicMessagesModel, AnthropicMessagesConfig, LLMfy, llmfy_usage_tracker

llm = AnthropicMessagesModel(
    model="anthropic.claude-sonnet-4-6-v1",
    config=AnthropicMessagesConfig(max_tokens=4096),
    api_key=BEDROCK_API_KEY,
    base_url=f"https://bedrock-mantle.{BEDROCK_REGION}.api.aws/anthropic",
)
agent = LLMfy(llm, system_message="You are a helpful assistant.")

# Bedrock's per-token price for this model — not OpenAI's/Anthropic's native price
bedrock_mantle_pricing = {
    "anthropic.claude-sonnet-4-6-v1": {
        "input": 3.00,
        "output": 15.00,
        "token_unit": 1_000_000,
    },
}

with llmfy_usage_tracker(anthropic_pricing=bedrock_mantle_pricing) as usage:
    async for chunk in agent.invoke_stream("Write a haiku about the cloud."):
        if chunk.result and chunk.result.content:
            print(chunk.result.content, end="", flush=True)

print(f"\n\nUsage:\n{usage}")
```

### 5. Workspace scoping via `default_headers`

Bedrock Mantle's Messages API supports [Workspaces](https://docs.aws.amazon.com/bedrock/latest/userguide/workspaces.html) (the Anthropic-compatible equivalent of the OpenAI-compatible surface's "Projects") for isolating and tracking usage per application. Scoping a request to a Workspace is done with an `anthropic-workspace-id` header, which the `anthropic` SDK doesn't send by default — so it goes through `default_headers`:

```python linenums="1"
from llmfy import AnthropicMessagesModel, AnthropicMessagesConfig, LLMfy

llm = AnthropicMessagesModel(
    model="anthropic.claude-sonnet-4-6-v1",
    config=AnthropicMessagesConfig(max_tokens=4096),
    api_key=BEDROCK_API_KEY,
    base_url=f"https://bedrock-mantle.{BEDROCK_REGION}.api.aws/anthropic",
    default_headers={"anthropic-workspace-id": "ws_..."},
)

agent = LLMfy(llm, system_message="You are a helpful assistant.")
result = agent.invoke("What is Amazon Bedrock?")
print(result.result.content)
```

`default_headers` is a plain passthrough to `anthropic.Anthropic(...)`/`openai.OpenAI(...)`, so it works the same way for any other header a compatible provider might require (custom tenant IDs, tracing headers, etc.) — not just Bedrock's Workspace/Project scoping.

!!! warning "Not every model supports every API surface"
    On `bedrock-mantle`, model availability is per-*API*, not just per-account. Per AWS's [API compatibility by models](https://docs.aws.amazon.com/bedrock/latest/userguide/models-api-compatibility.html) table, the GPT-5.x family (5.4, 5.5, 5.6 Sol/Terra/Luna) supports the **Responses API only** — calling `OpenAIChatModel` with one of those model IDs fails with a 400 (`"The model '...' does not support the '/v1/chat/completions' API"`). `gpt-oss-120b`/`gpt-oss-20b` (and the Safeguard variants) are the OpenAI-family models that support **both** Chat Completions and Responses. Check that table (or trial-and-error against a non-production call) before picking a model for `OpenAIChatModel` vs `OpenAIResponsesModel`.

!!! warning "Not every model shares the same base_url path, even for the same API"
    Even after confirming a model supports (say) Responses, the `base_url` itself can differ per model. `gpt-oss-120b`'s [model card](https://docs.aws.amazon.com/bedrock/latest/userguide/model-card-openai-gpt-oss-120b.html) lists its `bedrock-mantle` Responses URL as `.../v1`; GPT-5.6 Luna's [model card](https://docs.aws.amazon.com/bedrock/latest/userguide/model-card-openai-gpt-56-luna.html) explicitly documents a *different* path — `.../openai/v1` — noting *"This is different from the v1/responses path used by other models on the responses endpoint."* Using the wrong one produces the same `"does not support the '/v1/responses' API"` 400 as an actual unsupported model, so it's easy to misdiagnose as a model-support problem when it's really a URL problem. There's no way to know a given model's required path except checking its own model card's "Programmatic Access" table — don't assume every OpenAI-family model shares one `base_url` constant. See the [Bedrock Mantle example](../../examples/example-bedrock-mantle.md) for a `base_url` that's split out per-model for exactly this reason.

---

## Other OpenAI Chat-Completions-compatible providers

Most third-party "OpenAI-compatible" providers only implement **Chat Completions** — the older, more widely cloned surface. Few implement the newer **Responses API**; Bedrock Mantle above is one of the rare exceptions. So `OpenAIChatModel` is the one to reach for outside of OpenAI/Bedrock:

| Provider | Typical `base_url` | Auth |
|---|---|---|
| Groq | `https://api.groq.com/openai/v1` | `Authorization: Bearer <GROQ_API_KEY>` |
| Together AI | `https://api.together.xyz/v1` | `Authorization: Bearer <TOGETHER_API_KEY>` |
| OpenRouter | `https://openrouter.ai/api/v1` | `Authorization: Bearer <OPENROUTER_API_KEY>` |
| DeepSeek | `https://api.deepseek.com` | `Authorization: Bearer <DEEPSEEK_API_KEY>` |
| Ollama (local) | `http://localhost:11434/v1` | any placeholder string — not validated |
| Self-hosted vLLM / LiteLLM proxy | whatever you deploy, e.g. `http://localhost:8000/v1` | depends on your proxy config |

!!! warning "Verify before relying on this table"
    Base URLs and supported endpoints can change without notice. Always check the provider's own "OpenAI compatibility" doc page for the current `base_url` and which Chat Completions fields it actually supports before wiring it into production.

Example — Groq:

```python linenums="1"
from llmfy import OpenAIChatModel, OpenAIChatConfig, LLMfy

llm = OpenAIChatModel(
    model="llama-3.3-70b-versatile",  # Groq-hosted model ID
    config=OpenAIChatConfig(temperature=0.7),
    api_key=GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1",
)

agent = LLMfy(llm, system_message="You are a helpful assistant.")
result = agent.invoke("What's the fastest way to sort a list in Python?")
print(result.result.content)
```

Example — a local Ollama server (no real API key needed, but the `openai` SDK still requires a non-empty string):

```python linenums="1"
from llmfy import OpenAIChatModel, OpenAIChatConfig, LLMfy

llm = OpenAIChatModel(
    model="llama3.1",
    config=OpenAIChatConfig(temperature=0.7),
    api_key="ollama",  # placeholder — Ollama doesn't check it
    base_url="http://localhost:11434/v1",
)

agent = LLMfy(llm, system_message="You are a helpful assistant.")
result = agent.invoke("Summarize this in one sentence: llmfy is a Python LLM framework.")
print(result.result.content)
```

---

## Checklist before pointing at a new provider

1. **Confirm the auth header shape** the provider expects matches the [cheat sheet](#why-it-works-auth-cheat-sheet) above (`Authorization: Bearer` for OpenAI-shaped, `x-api-key` for Anthropic-shaped). If it doesn't, this mechanism won't work without SDK-level changes.
2. **Get the exact `base_url`** from the provider's own compatibility docs, and check where their spec's path (`/chat/completions`, `/responses`, `/v1/messages`) is appended — get the trailing segment wrong and requests 404.
3. **Test with `curl` first**, outside of llmfy, to confirm the request/response shape before debugging through the library:
   ```shell
   curl -X POST "$BASE_URL/chat/completions" \
     -H "Authorization: Bearer $API_KEY" \
     -H "Content-Type: application/json" \
     -d '{"model": "...", "messages": [{"role": "user", "content": "hi"}]}'
   ```
4. **Use the provider's own model ID naming** — not OpenAI's/Anthropic's native IDs.
5. **Run one non-streaming `invoke()` call** through llmfy and inspect the raw result before trying streaming or tool calling — streaming (SSE event shape) and tool-call encoding are the parts most likely to diverge between "compatible" implementations.
6. **Add a custom pricing dict** via `llmfy_usage_tracker(...)` (see [Usage Tracking](usage.md#customize-prices-data)) if you want accurate cost tracking — built-in pricing tables only cover native OpenAI/Anthropic model IDs and rates.

---

## Caveats

!!! warning "\"Compatible\" is a claim, not a guarantee"
    llmfy's formatters and usage parsers (e.g. `openai_chat_usage.py`, `anthropic_messages_usage.py`) assume the response/streaming shape matches the real OpenAI/Anthropic spec exactly. A provider that only implements a subset — different `usage` fields, different SSE event shapes, different tool-call encoding — can fail to parse or under/over-count tokens even though it advertises "OpenAI/Anthropic compatible".

!!! info "Error mapping is HTTP-status-driven, so it mostly just works"
    `OPENAI_ERROR_MAP`/`ANTHROPIC_ERROR_MAP` (`exception_mapper.py`) key off the SDK's exception *class name* (`RateLimitError`, `AuthenticationError`, `BadRequestError`, ...) — not the provider's JSON error body. The `openai`/`anthropic` SDKs derive that class purely from the HTTP status code (400→`BadRequestError`, 401→`AuthenticationError`, 429→`RateLimitError`, 500→`InternalServerError`, ...) before llmfy's code runs at all. So a compatible endpoint that returns the *correct* standard status code for a given failure produces the exact same `LLMfyException` subclass as the real vendor, regardless of body shape.

    Two things still differ: (1) a provider that returns the *wrong* status code for a situation (e.g. `500` for what's actually a rate limit) maps to the wrong exception type — e.g. `ServiceUnavailableException` instead of `RateLimitException` — since llmfy has no way to see past the SDK's status-code-driven classification; (2) the exception's `provider` field stays `ServiceProvider.OPENAI`/`ANTHROPIC` regardless of the real vendor behind `base_url` (see below).

!!! warning "`ServiceProvider`/`ModelBackend` labels don't change"
    `self.provider`/`self.backend` stay `OPENAI`/`ANTHROPIC` (etc.) regardless of the actual vendor behind `base_url` — usage/cost breakdowns and error reporting will show `"openai"`/`"anthropic"`, not the real provider name.

!!! info "Pricing needs a custom dict"
    Built-in pricing tables (`OPENAI_PRICING`, `ANTHROPIC_PRICING`) only cover native OpenAI/Anthropic model IDs and prices — a third-party provider's model won't be found, or worse, will collide with an unrelated OpenAI/Anthropic model ID that happens to share the same string. Always pass a custom pricing dict keyed by *that provider's* model IDs and rates via `llmfy_usage_tracker(openai_pricing=..., anthropic_pricing=...)`.

!!! info "Model-specific features may not be supported"
    `thinking`/`reasoning` config fields (`reasoning_effort`, `cache_control`, `output_config.effort`, etc.) map to real OpenAI/Anthropic model behavior. A compatible third-party provider may not recognize these fields at all, may silently ignore them, or may reject the request with a 400. Test with `thinking.enabled=False` / `prompt_caching.enabled=False` first, then enable and verify against a non-native endpoint before relying on it.
