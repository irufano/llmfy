# LLMfy behavior checklist (for porting to other language SDKs)

This is a plain-language checklist of every observable behavior the Python
`llmfy` package's test suite (`tests/`) verifies. It exists so a port to
another language doesn't require reading Python test code (fixtures,
`unittest.mock`, `monkeypatch`, pytest idioms) to know what to reproduce —
read this instead, then consult the referenced test file only when a bullet
needs more precision than a sentence can give.

**How to use this for a port**: copy this file into the new SDK's repo and
check items off (`- [ ]` → `- [x]`) as its own test suite proves each
behavior. Every box here is already checked for the Python implementation —
they're all backed by a passing test in `tests/` as of this writing. A box
you can't check means either a genuine behavior gap in the port, or a
deliberate, documented difference — which should be written down, not left
silent.

**Scope**: everything below mirrors `tests/`, which covers all of `llmfy/`
**except `llmfy/flow_engine/`** — that module has no tests yet (a refactor is
planned first) and is intentionally absent from this checklist too. It will
get its own section here once that lands.

Each section names its source test file(s) so behavior and proof stay linked.

---

## Public API contract
*`tests/test_public_api.py`*

- [x] Every name in `llmfy.__all__` is actually importable from the top-level package.
- [x] `__all__` has no duplicate entries.
- [x] Core chat API is exported: `LLMfy`, `Message`, `Role`, `Tool`, `ToolRegistry`, `AIResponse`, `GenerationResponse`.
- [x] Every provider's model + config class is exported (all 5 backends).
- [x] The full exception hierarchy is exported, and every exported exception class is a subclass of `LLMfyException`.
- [x] Chunking/text-preprocessing utilities are exported: `chunk_text`, `chunk_markdown_by_header`, `clean_text_for_embedding`.
- [x] `__version__` is exported and is a string.

## Supply-chain / optional-dependency isolation
*`tests/test_dependency_isolation.py`*

- [x] With **zero** provider SDKs installed (`openai`, `boto3`/`aioboto3`, `anthropic`, `google-genai` all blocked), `import llmfy` still succeeds.
- [x] Provider-agnostic features still work with no SDKs installed: constructing `Message`, using `@Tool`, calling `chunk_text`, raising/catching `LLMfyException`, constructing `Content`.
- [x] Instantiating `OpenAIChatModel` without `openai` installed raises a clean `LLMfyException` naming the missing package and the install extra — never a raw `ModuleNotFoundError`.
- [x] Same clean-failure guarantee for `AnthropicMessagesModel` (missing `anthropic`), `BedrockConverseModel` (missing `boto3`), `GoogleAIGenerateModel` (missing `google-genai`).

## Exceptions
*`tests/exception/`*

**`LLMfyException` hierarchy** (`test_llmfy_exception.py`)
- [x] Base exception constructs with just a message; `status_code`/`raw_error`/`provider` all default to `None`.
- [x] `str(exception) == message` (standard `Exception` behavior via `super().__init__(message)`).
- [x] `repr()` format is exactly `ClassName(message='...', status_code=..., provider='...')` — note `raw_error` is deliberately excluded from `repr()` (could carry sensitive data).
- [x] Every leaf subclass (`RateLimitException`, `QuotaExceededException`, `InvalidRequestException`, `AuthenticationException`, `PermissionDeniedException`, `ModelNotFoundException`, `ServiceUnavailableException`, `ContentFilterException`, `ModelErrorException`) is a plain subclass with no added fields, and `repr()` uses the concrete class name.
- [x] `TimeoutException` adds one extra field, `timeout_type` (an enum: `CONNECT`, `READ`, `WRITE`, `POOL`, `MODEL`), defaulting to `None`. `TimeoutException` does **not** override `repr()`, so `timeout_type` never appears in it.

**Error-code → exception-class maps** (`test_exception_mapper.py`) — pin the exact shape, since the error handlers depend on it:
- [x] Bedrock: 9 entries keyed by AWS error-code string, each mapping to `(ExceptionClass, default_http_status)`. `ThrottlingException`→429 rate-limit, `ModelTimeoutException`→408 timeout, `ValidationException`→400 invalid-request, `AccessDeniedException`→403 auth, `ResourceNotFoundException`→404 model-not-found.
- [x] OpenAI and Anthropic share the same 9 SDK-exception-class-name keys and the same shape (both SDKs use matching class names): `RateLimitError`→429, `APITimeoutError`→408 timeout, `APIConnectionError`→`(ServiceUnavailable, None)` (no default status — a network failure has no HTTP response), `AuthenticationError`→401, `PermissionDeniedError`→403, `BadRequestError`→400, `NotFoundError`→404, `UnprocessableEntityError`→422, `InternalServerError`→500.
- [x] Google is keyed directly by **HTTP status int** (not a class name), values are plain exception classes (no status tuple, since the key already is the status): 400, 401, 403, 404, 408, 429, 500, 503 all mapped; 403 → `PermissionDeniedException`.

**Error handlers** (`test_exception_handler.py`) — tested against real SDK exception instances (`botocore`, `httpx`, `google-genai`), not mocks, for the ones that dispatch via `isinstance`:
- [x] Bedrock: `ReadTimeoutError`/`ConnectTimeoutError` (real botocore exceptions) map to `TimeoutException` with `timeout_type=READ`/`CONNECT` respectively — checked *before* the generic `ClientError` handling.
- [x] A non-`ClientError`, non-timeout exception becomes a plain `LLMfyException` (status code stays `None`).
- [x] A mapped `ClientError` error code produces the mapped exception class; an explicit non-zero `HTTPStatusCode` from the response always wins over the map's default status; a missing `HTTPStatusCode` falls back to the map default; an unknown error code falls back to a plain `LLMfyException`.
- [x] A missing `Message` key in the error response falls back to `str(exception)`.
- [x] `ModelTimeoutException` (a *ClientError code*, not a raw botocore timeout type) still resolves to `TimeoutException` with `timeout_type=MODEL`.
- [x] OpenAI/Anthropic (identical dispatch logic, different provider tag): dispatch is purely by `type(exception).__name__` string match plus `hasattr` checks — never `isinstance` against the real SDK — so an unknown exception-class name always falls back to plain `LLMfyException`.
- [x] `response`/`request_id`/`body` attributes are copied into `raw_error` only when present on the source exception (never invented).
- [x] An explicit non-falsy `status_code` on the source exception wins over the map's default; a falsy/absent one falls back to the map default.
- [x] Timeout-type resolution for OpenAI/Anthropic inspects `exception.__cause__`'s exact type against `httpx.ConnectTimeout`/`ReadTimeout`/`WriteTimeout`/`PoolTimeout` — an unrelated or missing cause yields `timeout_type=None`.
- [x] Google: `httpx.TimeoutException` subclasses map to `TimeoutException` (status_code stays `None` here — an asymmetry versus the other three providers, which do set one). A real `google.genai.errors.APIError` maps by its `.code` (HTTP status); an unmapped code falls back to plain `LLMfyException`; `.details` is copied into `raw_error` only when present. Any other exception type (not a timeout, not an `APIError`) becomes a generic `LLMfyException` with `raw_error={"error": str(e)}`.

**Package exports** (`test_exception_package_exports.py`)
- [x] Every name in `llmfy.exception.__all__` is importable and is a subclass of `LLMfyException`.
- [x] `TimeoutType` is intentionally **not** re-exported at the `llmfy.exception` package level (only from `llmfy_exception` directly).

## Messages
*`tests/llmfy_core/messages/`*

**`Message`** (`test_message.py`)
- [x] Valid role/field combinations construct without error (user+content, system+content, assistant+tool_calls, tool+tool_call_id+tool_results).
- [x] Four cross-field invariants, checked in this exact order (a message violating more than one always fails on the first): `tool_results` set on a non-`tool` role → error; `tool` role with no (or empty-list) `tool_results` → error; `tool_call_id` set on a non-`tool` role → error; `tool_calls` set on a non-`assistant` role → error.
- [x] These validation errors are raised via the framework's model-validation mechanism (a pydantic `ValidationError` in the Python implementation, wrapping the original message text) — a port should decide and document its own equivalent (exception type or `Result`/`Either`).
- [x] `id` defaults to a fresh unique value per instance; `timestamp` defaults to an ISO-8601 string.
- [x] Unknown/extra fields on construction are rejected (strict schema).
- [x] Role accepts a plain string and coerces it to the enum; an invalid role string is rejected.

**`MessageTemp`** (`test_message_temp.py`) — in-memory, per-request chat history:
- [x] `add_system_message` always inserts at the **front** of history, not the end.
- [x] Calling `add_system_message` twice keeps **both** (no dedup/replace) — most recent ends up frontmost.
- [x] `add_user_message` appends with the given id.
- [x] `add_assistant_message` mutates each given `ToolCall`'s `request_call_id` **in place** to the new message's id — a documented side effect on the caller's own objects, not a copy.
- [x] `add_tool_message` delegates to the backend-specific formatter's own tool-result logic (see per-provider formatter sections below); an unsupported/unregistered backend raises a clean error.
- [x] `get_messages(backend)` formats every message in history, in order, for that backend; an unsupported backend raises a clean error.
- [x] Formatting is **cached per message id per backend** — calling `get_messages` repeatedly on an unchanged history does not re-format already-formatted messages; only genuinely new messages get formatted.
- [x] The cache evicts entries for messages no longer in history (e.g. after `clear()`), so it can't grow unbounded across many calls on one instance.
- [x] `get_instance_messages()` returns a **live reference** to the internal list, not a defensive copy — mutating the returned list mutates internal state.
- [x] `clear()` empties history but keeps the most-recently-inserted system message (if any) — this is "reset conversation, keep the current system prompt," and only ever keeps **one** system message even if multiple were added.

**`Content`** (`test_content.py`)
- [x] `type` defaults to `TEXT`. `value` is required (no default) and accepts either a string or raw bytes.
- [x] Optional fields (`filename`, `format`, `use_s3`, `bucket_owner`) all have sensible defaults (`None`/`False`).
- [x] Unknown/extra fields rejected (strict schema).
- [x] **No** provider-specific format/content validation happens at this level (e.g. an invalid image format string is accepted here) — that validation is each provider formatter's job, not this shared data class's.

**`ContentType` / `Role` enums** (`test_content_type.py`, `test_role.py`)
- [x] Exact string values for every member (`ContentType`: text/image/document/video; `Role`: system/user/assistant/tool).
- [x] String-enum members compare equal to their plain string value.
- [x] Construct-from-string works for a valid value; an invalid value is rejected.

**`ToolCall`** (`test_tool_call.py`)
- [x] All 4 fields (`tool_call_id`, `request_call_id`, `name`, `arguments`) are required — missing any one is rejected.
- [x] Unlike `Message`/`Content`, **unknown extra fields are silently ignored** here, not rejected — a deliberate contrast worth preserving or explicitly deciding against in a port.
- [x] `arguments` accepts arbitrarily nested structures (dict of dict of list, etc.).

## Tools
*`tests/llmfy_core/tools/`*

**Docstring parameter-description extraction** (`test_function_param_desc_extractor.py`)
- [x] Supports three docstring styles, tried in this exact priority order: Google-style (`name (type): description`), reST-style (`:param name: description`), Sphinx-with-type-style (`:param type name: description`).
- [x] Multi-line descriptions are collapsed to a single line (internal whitespace/newlines normalized to single spaces).
- [x] Description extraction correctly stops before the next parameter or before `Returns:`/`Raises:`/etc. sections.
- [x] No match (empty docstring, param not present, garbage input) returns an empty string — never raises.
- [x] A parameter name that's a substring of another name in the docstring (e.g. `loc` vs. `location`) does **not** false-match.
- [x] **Security**: parameter names are matched literally, not as regex syntax — a name containing regex metacharacters (`.`, `*`, `(`, `|`) must not corrupt the match, widen it unexpectedly, or crash the parser.

**Function metadata extraction** (`test_function_parser.py`)
- [x] Extracts function name, a short description (text before the first `Args:`/`:param`/etc. section — falls back to the whole docstring if no such section exists), the raw parameter signature, resolved type hints, and the raw docstring.
- [x] No docstring → empty description and empty docstring string (never `None`, never raises).
- [x] Default values on parameters are reflected faithfully in the extracted signature.
- [x] Extracting metadata from a bound method includes `self` in the parameter list (callers are expected to skip it, which every formatter does — see below).

**Type mapping** (`test_function_type_mapping.py`)
- [x] Fixed mapping from Python's `int`/`float`/`str`/`bool`/`list`/`dict`/`NoneType` to JSON-Schema-style type names (`integer`/`number`/`string`/`boolean`/`array`/`object`/`null`). Any other Python type falls back to `"string"` at the call site (the mapping itself has no catch-all entry).

**`@Tool` decorator** (`test_tool.py`)
- [x] Marks the decorated function (default `strict=True`, or the value passed to `Tool(strict=...)`) without wrapping it — the function is returned unchanged and remains directly callable with its original behavior.
- [x] The decorator does **not** inspect or cache the docstring at decoration time — reassigning `__doc__` after decoration is picked up correctly when the tool definition is later built.
- [x] Building a tool definition dispatches to the registered formatter for every one of the 5 real backends without error; an unregistered/missing backend raises a clean error.

**Tool registry** (`test_tool_registry.py`)
- [x] Registering a function not decorated with `@Tool` raises a clean error (checked via a simple attribute-presence marker, not a type check).
- [x] Registering two functions with the same `__name__` silently keeps only the later one (last-write-wins on both the callable and its schema — no error).
- [x] `get_tool_definitions()` returns definitions in registration order (post-dedup).
- [x] `execute_tool(name, arguments)` calls the registered function via dict lookup + keyword-argument spread — never `eval`/dynamic-attribute-lookup on an arbitrary object.
- [x] **Security**: calling with an unregistered name — including deliberately hostile names like `__import__`, `os.system`, or a path-traversal-shaped string — always raises a clean "tool not found" error and never executes anything.
- [x] A tool call with missing/wrong arguments raises a plain `TypeError` from the underlying function, unwrapped — the registry does not catch or reinterpret it.

## Usage tracking
*`tests/llmfy_core/usage/`*

**Pricing-table validation** (`test_llmfy_usage.py`)
- [x] OpenAI/Anthropic pricing: every model entry must be a dict whose values are all numeric (int/float); anything else is rejected.
- [x] Bedrock pricing: only the first two levels of dict nesting are checked (model → region → dict) — the innermost leaf values (price numbers) are **not** validated here, unlike OpenAI/Anthropic; a malformed leaf (missing `input`/`output` key) passes this check and fails later, downstream, when building the internal pricing model.
- [x] Google pricing supports 4 combinable shapes: flat numeric, per-content-type (a dict with a required `default` key), tiered (`threshold`+`input_high`+`output_high`, which must **all** be present together — partial tier config is rejected), and tiered+typed combined. Missing `input`/`output` keys altogether is rejected.
- [x] Passing an explicitly **empty** pricing dict (`{}`) for any provider skips validation (an empty dict is "falsy") **and** falls back to that provider's bundled default pricing table — it does *not* mean "use zero pricing." This footgun is worth flagging explicitly in a port rather than silently replicating.
- [x] Passing nothing (`None`, the default) uses the bundled default pricing table for every provider.

**Usage-update dispatch** (`test_llmfy_usage.py`)
- [x] `update()` never raises for an unrecognized combination of service-type/backend/provider — it's a silent no-op (all counters stay at zero). This applies to: LLM type with no/unknown backend, embedding type with no/unknown provider (including `ANTHROPIC`, which has no embedding update path by design), and a completely unrecognized service type.
- [x] Usage payloads are accepted either as a plain dict or as an arbitrary object exposing the same fields as attributes (`vars(obj)` is used internally) — both must produce identical accounting.

**Per-provider cost math** (one section per backend in `test_llmfy_usage.py`) — each of these is a concrete, checkable numeric contract a port must reproduce exactly:
- [x] OpenAI Chat/Responses: input/output token counts and cost use the standard `tokens / token_unit * price` formula; **cache-read and cache-write tokens are subsets of the input-token count** and are billed at their own (possibly custom) rate, subtracted from the "regular" input portion first so nothing is double-counted. Cache-read rate defaults to 50% of the input price if not set; cache-write defaults to 0 (free) if not set. Responses API uses different raw field names (`input_tokens`/`output_tokens` vs. Chat's `prompt_tokens`/`completion_tokens`) but shares the *same* pricing table (pricing is per-model, not per-API-variant).
- [x] Bedrock: pricing is looked up by **model AND region** (an environment variable supplies the region) — a model present in the pricing table but missing the specific region raises a raw `KeyError` (this is *not* treated as "model not found," which only warns). Cache-read defaults to 10% of the input rate, cache-write defaults to 125% of the input rate, both additive to the base input cost (not subtracted from it).
- [x] Anthropic: same additive cache-rate defaults and math as Bedrock (10% read / 125% write), but pricing has **no region dimension** — a flat per-model lookup.
- [x] Google: **the only provider with a fundamentally different cache-discount formula.** The full (non-discounted) input cost is computed first from the raw token count, then a "savings" amount (`normal_price_for_cached_tokens − actual_cached_price`) is *subtracted* from the total — mathematically equivalent to the other providers' "subtract cached tokens before pricing" approach only when the discount ratio matches the assumed default (25% of the input rate, i.e. 75% off), but computed via a different code path. A tiered (threshold-based) rate applies when total input tokens exceed a configured threshold, falling back to the normal rate if the high-tier rate is absent from the pricing entry even when the threshold is exceeded. Per-content-type pricing (text/image/video/audio each billed at a different rate, defaulting to a `default` rate for any type without its own entry) is only used when the usage payload actually reports a type breakdown; otherwise a flat `default` rate applies even for typed pricing entries.
- [x] Embedding updates (OpenAI, Bedrock, Google) always force `output_tokens = 0` and never touch cache accounting (embeddings have no output tokens or caching in this SDK's model). Bedrock's embedding usage reads its token count from an unusual hyphenated key (a raw AWS response field name), unlike every other usage payload's key naming.
- [x] Every "model not found in pricing table" case (LLM and embedding, every provider) emits a **warning** (not an error), still records the request in the running totals with a **zero** cost contribution, and still appends a detail entry (with `input_price`/`output_price` left `None` so it's distinguishable from a genuinely free request).

**Reporting / reset** (`test_llmfy_usage.py`)
- [x] `to_dict()` produces a stable nested summary shape (`total_request`, `tokens.*`, `costs.*` including a human-formatted trimmed-decimal cost string, `cache.*`, `details`).
- [x] The human-readable `repr()` omits its "Cache:" section entirely when no cache activity has occurred, and omits the per-request "backend:" line for embedding entries (which have no backend, only a provider).
- [x] `reset()` zeroes every running counter and clears history lists, but **does not** touch the loaded pricing tables — pricing persists across a reset.

**Usage-tracker context manager** (`test_usage_tracker.py`)
- [x] `with llmfy_usage_tracker() as usage:` yields a fresh tracker instance and installs it into the ambient/thread-local context; the tracker is retrievable from inside the `with` block via that same context mechanism.
- [x] Invalid pricing passed to the tracker raises before the `with` block's body ever runs.
- [x] An exception raised inside the `with` block propagates normally — never swallowed.
- [x] **Documented current behavior, not necessarily desirable**: exiting the `with` block does **not** reset the ambient context back to `None` (or restore a prior value) — the just-used tracker instance remains retrievable afterward. A port should decide deliberately whether to keep or fix this.

## Enums: `ModelBackend`, `ServiceProvider`, `ServiceType`
*`tests/llmfy_core/test_model_backend.py`, `test_service_provider.py`, `test_service_type.py`*

- [x] `ModelBackend` has exactly 5 members, one per (vendor, API-variant) pair, each following a `VENDOR_APIVARIANT` naming convention matching its string value: `openai_chat`, `openai_responses`, `bedrock_converse`, `google_generate`, `anthropic_messages`.
- [x] `ServiceProvider` has exactly 4 members (one per vendor, no API-variant split): `openai`, `bedrock`, `google`, `anthropic`.
- [x] `ServiceType` has exactly 2 members: `llm`, `embedding`.
- [x] All three: string-enum semantics (compare equal to their plain string value), and an invalid value is rejected.

## Responses
*`tests/llmfy_core/responses/`*

- [x] `AIResponse`: all 3 fields (`content`, `thinking`, `tool_calls`) are optional/nullable; unknown extra fields rejected.
- [x] `GenerationResponse`: `result` is required; `messages` defaults to an empty list, and that default is **not** a shared mutable default across instances (a common footgun in several languages' default-value semantics — verify explicitly in a port). Unknown extra fields rejected.

## LLM provider formatters
*`tests/llmfy_core/llms/{openai/chat,openai/responses,anthropic/messages,bedrock/converse,google/generate}/test_*_formatter.py`*

These are the highest-value, highest-bug-risk logic in the whole package —
tested exhaustively for **all 5 backends**. This section is the closest
thing to a spec for "how does a `Message` become provider wire JSON."

**Cross-provider behaviors to specifically watch for** (each already covered per-provider by name below, called out together here because they're easy to get subtly wrong when porting one provider at a time without comparing against the others):
- [x] **Tool-result merge vs. new-message asymmetry**: Anthropic and Bedrock *merge* multiple tool results from the same assistant turn (same `request_call_id`) into a single tool-role message; OpenAI (both APIs) and Google *always* create a brand-new message per tool result, never merging.
- [x] **Required-tool-parameter asymmetry**: OpenAI marks every parameter required regardless of a Python default (because `strict=True` is hardcoded); Anthropic and Bedrock also mark every parameter unconditionally required (no `strict` concept at all); Google is the **only** one of the five that respects a parameter's default value when deciding required-ness.
- [x] **Role mapping for tool-result messages**: every non-OpenAI-Chat provider maps the internal `tool` role to that provider's own conversational role for tool results (`"user"` for Anthropic/Bedrock/Google) rather than a distinct `tool` role — OpenAI Chat is the only one with a genuine native `tool` role.
- [x] Every provider (except Bedrock/Google, which support VIDEO) raises a clear, provider-specific error for unsupported content — e.g. OpenAI Chat/Responses reject `VIDEO`, Responses also rejects `DOCUMENT`, Anthropic rejects `VIDEO`.
- [x] A `Union[X, None]` (i.e. `X | None`) Python type hint on a tool parameter unwraps to `X`'s mapped JSON type in every formatter, not a generic fallback.

**OpenAI Chat** (`test_openai_chat_formatter.py`)
- [x] Text/image/document content blocks format correctly; `DOCUMENT` requires a `filename` (raises if absent); `VIDEO` always raises.
- [x] Tool calls format as OpenAI's `{"id","type":"function","function":{"name","arguments"}}` shape (arguments JSON-serialized).
- [x] A tool-result message uses **only the first** item of `tool_results` as the message content (documented single-result assumption for this API).
- [x] Tool-function schema: every parameter is required (via `strict=True`); a default value is appended to the parameter's description text; the `self` parameter is skipped for bound methods; an unmapped Python type falls back to `"string"`.
- [x] `format_tool_message` always appends a brand-new message (see cross-provider note above).

**OpenAI Responses** (`test_openai_responses_formatter.py`)
- [x] A single `Message` with multiple tool calls must expand into **multiple** flat top-level API items — represented internally as a private `{"__items__": [...]}` wrapper that the model layer unwraps (this API's `input` array is flat, unlike Chat Completions' single nested message).
- [x] Prior assistant-turn text replays as `"output_text"`; every other role's text is `"input_text"`.
- [x] `DOCUMENT` content is **not supported at all** on this API variant (raises), unlike Chat Completions (which supports it).
- [x] Tool-function schema omits the `"type": "function"` wrapper key (the model layer adds it) but otherwise mirrors Chat Completions' required-params-always logic.

**Anthropic Messages** (`test_anthropic_messages_formatter.py`)
- [x] Image content requires an explicit, supported `format` (`jpeg`/`png`/`gif`/`webp`); raw bytes are base64-encoded inline; the Bedrock-only `use_s3` flag is explicitly rejected as unsupported on this native API.
- [x] `DOCUMENT` requires a `filename`; `VIDEO` always raises (not supported at all on this API).
- [x] The internal `name` field is **never** emitted (the native Messages API has no per-message name field).
- [x] Tool-result blocks use the field name `tool_use_id` (not `id`) and merge multiple parallel results from the same turn into one message's `tool_results` list.
- [x] Tool-function schema description falls back to the function's name when no docstring description is available.

**Bedrock Converse** (`test_bedrock_converse_formatter.py`)
- [x] Richest content-type support of the five: text/image/document/video, each with both a `bytes`-source and an `s3Location`-source variant (the latter requires `bucket_owner`, raises if absent).
- [x] Video supports Bedrock's own 9-format list (`wmv`/`mpg`/`mpeg`/`three_gp`/`flv`/`mp4`/`mov`/`mkv`/`webm`).
- [x] The `name` field is dropped specifically for tool-role messages but kept for every other role.
- [x] Tool-result merging follows the same same-`request_call_id` rule as Anthropic (both support this "batch tool results into one message" behavior, documented in-repo as supporting two historically-different wire-format generations).

**Google AI Generate** (`test_googleai_generate_formatter.py`)
- [x] Role mapping is distinctive: `assistant`→`"model"` (not `"assistant"`); a placeholder `"system"` role is emitted for system messages (the model layer strips it out and passes it separately, same pattern as Anthropic/Bedrock but with a different placeholder string).
- [x] Image content branches on 3 input shapes: raw bytes (base64-encoded inline, hardcoded `image/jpeg` mime type), a `data:` URI string (mime type parsed **from the URI header itself**), or an `http`-prefixed URL string (passed as a file reference) — anything else raises.
- [x] Document content supports the same 3 shapes **except** it does *not* parse the mime type from a data-URI header the way image does — it hardcodes `application/pdf` regardless. This is a known inconsistency in the reference implementation, worth a deliberate decision (reproduce as-is for parity, or fix) rather than accidentally diverging.
- [x] Video content defaults its format to `mp4` when unset, validates against a Google-specific 9-format list, and — unlike image/document — has **no** data-URI support (only raw bytes or an http URL).
- [x] Tool-function schema is the only one of the five that respects a Python default value for required-ness (see cross-provider note above).
- [x] `format_tool_message` never merges (always a new message) despite `format_message`'s tool-result branch reading the *whole* `tool_results` list — meaning any merging behavior for Google would have to happen before this call, not inside it.

## LLM provider model classes
*`tests/llmfy_core/llms/{openai/chat,openai/responses,anthropic/messages,bedrock/converse,google/generate}/test_*_model.py`*

Depth policy: **OpenAI Chat is tested in full** (it's the reference
implementation for the shared streaming/error-wrapping/async patterns every
other backend follows); the other four get a smoke pass (construction
validation + one successful call + one mapped-error call) since their
formatting-specific logic is already covered above.

**Shared behavior across all 5 model classes** (each verified at least once):
- [x] Constructing a model without the required API credentials (API key, or for Bedrock all three of access key / secret key / region) raises a clean, actionable `LLMfyException` naming the missing credential — never a raw SDK error.
- [x] A provider SDK error raised by the mocked client call surfaces as the **correctly-mapped** `LLMfyException` subclass (e.g. a rate-limit error becomes `RateLimitException`) — this proves the model-to-error-handler wiring end-to-end, not just the handler in isolation.
- [x] A non-provider, generic exception (e.g. a plain network failure) is wrapped as a generic `LLMfyException` rather than left unwrapped or misclassified.
- [x] A response with a tool-call/function-call result parses into `AIResponse.tool_calls` with `content=None`; a plain-text response parses into `AIResponse.content` with `tool_calls=None`.

**OpenAI Chat only** (`test_openai_chat_model.py`) — full depth:
- [x] Both sync (`generate`) and async (`agenerate`) paths tested against their respective client objects.
- [x] Streaming: a chunk with an empty `choices` list (the trailing usage-only chunk) is silently skipped, never yielded as a response.
- [x] Streaming: **two parallel tool calls, with their argument-JSON deltas interleaved across chunks**, are accumulated **independently keyed by each tool call's index** — proving the accumulator can't accidentally merge one tool call's arguments into another's when the model streams them concurrently.
- [x] `max_tokens` is omitted entirely from the request payload when unset (not sent as an explicit null) — some models reject an explicit null outright.
- [x] Passing `tools` adds `tool_choice: "auto"` and wraps each tool definition in the `{"type": "function", "function": ...}` envelope.

**System-message handling** (Anthropic + Bedrock model smoke tests):
- [x] A `system`-role message present in the *formatted* message list gets hoisted out into that provider's dedicated top-level `system` parameter before the API call, and is **not** present in the `messages`/`contents` array sent to the SDK.

## Embeddings
*`tests/llmfy_core/embeddings/test_openai_embedding.py`* (OpenAI only — Bedrock/Google embeddings are not yet covered by this suite; a good next addition, not done in this pass)

- [x] Construction validation mirrors the chat models (missing API key / missing SDK → clean `LLMfyException`).
- [x] `encode()` returns the first (and only) embedding vector from the response; an empty response raises `ValueError`; any other underlying error propagates **unwrapped** (not re-wrapped as `LLMfyException` — a deliberate contrast with the chat models).
- [x] `encode_batch()`: a single string input is wrapped into a one-item list; requires numpy installed (clean error if missing); batches respect the configured `batch_size` (verified via captured per-call batch sizes); a mismatched response length (fewer embeddings returned than texts sent) raises `ValueError`.
- [x] **Response ordering is not guaranteed by the provider** — `encode_batch` must re-sort returned embeddings by each item's `index` field before returning, verified with a deliberately out-of-order fake response.
- [x] Rate-limit errors (detected via substring match on the error message) are retried with exponential backoff up to `max_retries`, then re-raised if still failing after the last attempt.

## `LLMfy` — the main chat/generation class
*`tests/llmfy_core/test_llmfy.py`* — tested against a fake `BaseAIModel` test double, never a real provider.

- [x] Constructor validates a `{{placeholder}}`-containing system message against the supplied `input_variables` at **construction time**: a placeholder with no `input_variables` at all raises; a placeholder missing from a non-empty `input_variables` list raises; a fully matching set succeeds.
- [x] `register_tool` requires every function to already carry the `@Tool` marker — a plain undecorated function (even a lambda) raises a clean error.
- [x] `invoke`/`chat` **record** any tool calls the model returns in conversation history but **never execute them** — only the `_with_tools` variants execute tools. Verified explicitly: a tool registered to flip a flag is proven *not* to have been called.
- [x] A generic exception raised by the underlying model is wrapped as `LLMfyException`; an `LLMfyException` raised by the model (including its `status_code`) is re-raised as-is, not double-wrapped.
- [x] The system-message template is rendered at **call time** using kwargs passed to `invoke`/`chat` (not only validated at construction time) — a call missing a required kwarg raises even if construction-time validation passed (construction only checks the variable *names* line up, not that every call site remembers to supply them).
- [x] `invoke_with_tools`/`chat_with_tools`: the tool-calling loop terminates as soon as the model responds with no more tool calls — verified for both a single round-trip and a **multi-round** scenario (two separate tool-call rounds before a final content answer), proving the loop actually advances rather than looping forever or exiting too early.
- [x] A tool's return value is **stringified** before being recorded as the tool result message content, regardless of its original type.
- [x] Calling an unregistered tool name during the tool-calling loop raises a clean error (same guarantee as the standalone `ToolRegistry`).
- [x] `chat`/`chat_with_tools` replaying a caller-supplied message history dispatches each message by its role (`user`/`assistant`/`tool`) to the matching history-builder method; a tool-role message carrying **multiple** `tool_results` only replays the **first** one (a documented truncation, not a crash).
- [x] Streaming (`invoke_stream`/`chat_stream`): content chunks are yielded as they arrive and their text is accumulated; a **final terminal chunk** is always yielded after the stream ends, carrying an empty `AIResponse` (`content=None`) paired with the full accumulated message history — this is the signal consumers use to retrieve final history, and it must be distinguishable from a genuine empty-string content chunk (which is a separate, real edge case also verified: an empty-string chunk from the model is indistinguishable from "no content this chunk" by design).
- [x] `clear_messages_temp()` empties the instance's conversation history.
- [x] Every async method (`ainvoke`, `ainvoke_with_tools`, `achat`, `achat_with_tools`) mirrors its sync counterpart's behavior exactly, including the tool-execution-loop and exception-wrapping rules; `ainvoke_stream`/`achat_stream` are thread-offloaded wrappers around the sync streaming generator (not independently-implemented native async streams) and must be verified to produce identical output to their sync counterparts.

## Utilities: chunking & text preprocessing
*`tests/llmfy_utils/`*

**`chunk_text`** (`chunk/test_chunk.py`)
- [x] Splits on whitespace into words, then slides a window of `chunk_size` words with a step of `chunk_size − chunk_overlap`.
- [x] **Chunks whose joined character length is ≤100 are silently dropped** — even otherwise-valid short input can produce zero chunks. Chunk ids only increment for chunks actually kept, so a dropped chunk never "uses up" an id.
- [x] `chunk_overlap == chunk_size` (step of exactly 0) is an **error** condition; `chunk_overlap > chunk_size` (a negative step) instead silently produces an **empty result** with no error — two different failure modes for two similar-looking misconfigurations, both worth deciding deliberately in a port rather than picking one behavior arbitrarily.
- [x] Accepts either a plain string or a `(text, metadata)` tuple; non-dict metadata gets wrapped as `{"meta": metadata}` rather than rejected.
- [x] **Security/robustness**: `None` input fails cleanly rather than silently producing garbage; ~1MB of input processes without hanging; unicode text (including scripts with no whitespace, like CJK) doesn't crash, even though the whitespace-splitting approach is documented as imperfect for such scripts.

**`chunk_markdown_by_header`** (`chunk/test_chunk.py`)
- [x] Recognizes ATX-style headers (`# `, `## `, ... up to 6 `#`s) that have **exactly one space** after the hashes — `#NoSpace` is never matched. Setext-style headers (underline-style) are never supported.
- [x] Each chunk's content includes its header line and runs up to (but not including) the next header, or end of text.
- [x] An optional `header_level` filters which header depths start a new chunk — a deeper header nested under a shallower one becomes ordinary chunk content, not its own chunk.
- [x] Content appearing before the very first header in the document is dropped entirely (never a "preamble" chunk).
- [x] `header_level=0` is an invalid quantifier and fails cleanly at the regex-construction level; a **negative** `header_level` does *not* fail the same way — it silently compiles into a pattern that never matches anything, producing an empty result instead of an error. (This is the header-level equivalent of the `chunk_text` overlap-edge-case inconsistency above — same category of "two similar misconfigurations, two different failure shapes.")
- [x] No headers anywhere in the input produces an empty result, not an error.

**`clean_text_for_embedding`** (`text_preprocessing/test_text_preprocessing.py`)
- [x] Unicode-normalizes text (NFKC form) — e.g. full-width characters collapse to their standard-width equivalent.
- [x] Collapses every run of whitespace (including newlines and tabs) into a single regular space, then trims leading/trailing whitespace. **This destroys paragraph/line structure** — multi-paragraph input becomes one line — which is intentional for this function's purpose (preparing text for an embedding model) but must not be assumed to also be "safe" for anything that needs line structure preserved.
- [x] Non-string input (including `None`) fails cleanly rather than silently coercing or crashing further downstream.
- [x] ~1MB of input processes without hanging.

**`deprecated` decorator** (`test_deprecated.py`)
- [x] Works on both plain functions and classes; decorating a class wraps its `__init__` (warns on instantiation, not on class definition), and works even for a class with no explicit `__init__` of its own.
- [x] **Decoration itself never warns** — only actually calling the decorated function, or instantiating the decorated class, does.
- [x] The warning message assembles from whichever of `reason`/`version`/`alternative` were supplied, in a fixed order and format; a custom warning category is honored (defaults to `DeprecationWarning`).
- [x] Function metadata (`__name__`, `__doc__`) is preserved on the wrapped function.
- [x] Decorating a class returns the **same class object** (not a copy/subclass) — identity-preserving.
