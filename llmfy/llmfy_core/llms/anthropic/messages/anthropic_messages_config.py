from typing import Literal

from pydantic import BaseModel


class AnthropicMessagesThinkingConfig(BaseModel):
    """Grouped thinking settings for AnthropicMessagesModel.

    This is a direct port of the native Anthropic `thinking` block — unlike
    BedrockThinkingConfig there is no `reasoning_effort` field, since that is
    a Bedrock/Amazon-Nova-only mechanism with no equivalent on the native
    Anthropic Messages API.

    Extended thinking (use with budget_tokens; older models e.g. Sonnet 4.5,
    Haiku 4.5):
      thinking={"type": "enabled", "budget_tokens": N}

    Adaptive thinking (use with type='adaptive' + optional effort; current
    models e.g. Opus/Sonnet 4.6+, Fable 5, Mythos 5):
      thinking={"type": "adaptive"}
      output_config={"effort": "low"|"medium"|"high"|"xhigh"|"max"}
    """

    enabled: bool = False
    """Master switch. False: no `thinking` field is sent at all. True: the
    request is built from `type`/`budget_tokens`/`effort` below (type='adaptive'
    takes priority; otherwise falls back to extended thinking)."""

    budget_tokens: int | None = None
    """Extended thinking only (type left unset). Token budget for the
    reasoning pass. Minimum 1024. Must be strictly less than `max_tokens`.
    Not accepted (400) on current-generation adaptive-only models."""

    type: Literal["adaptive"] | None = None
    """Thinking mode selector. Leave unset for extended thinking
    (budget_tokens); set to 'adaptive' for current-generation models, several
    of which reject `budget_tokens` entirely and require 'adaptive'."""

    effort: str | None = None
    """Adaptive thinking only (type='adaptive'): 'low'/'medium'/'high'/'xhigh'/
    'max' (exact set depends on model). Sent via `output_config.effort`, a
    top-level request field — NOT nested inside `thinking`."""


class AnthropicMessagesPromptCachingConfig(BaseModel):
    """Grouped prompt caching settings for AnthropicMessagesModel.

    Native Anthropic caching uses an inline `cache_control` key attached
    directly to the last content block of the prefix to cache — NOT a
    sibling block like Bedrock's Converse API `cachePoint`.

    When enabled=True, `cache_control` is attached to:
      - The last block of `system` (when a system prompt is present) — this
        implicitly caches `tools + system` together, since Anthropic's
        render order is tools -> system -> messages and caching is a byte
        prefix match.
      - The last content block of the last message (grows the cached
        conversation prefix each turn).

    Reference: https://platform.claude.com/docs/en/build-with-claude/prompt-caching

    Pricing: cache reads ~10% of input price, cache writes ~125% (5m TTL) or
    ~200% (1h TTL) of input price. `ModelPricing` has a single `cache_write`
    field with no TTL distinction — set it explicitly per model if the 1h
    write premium needs to be modeled precisely (same simplification already
    made by BedrockPromptCachingConfig).

    Minimum cacheable prefix is model-dependent (as low as 1024 tokens on
    current models, up to 4096 on some older/smaller models) — shorter
    prefixes silently won't cache (no error, `cache_creation_input_tokens: 0`).
    """

    enabled: bool = False
    """Master switch. False: no `cache_control` markers are injected."""

    ttl: str | None = None
    """Cache time-to-live. Accepted values:
      - None (default): 5-minute TTL
      - "5m": 5-minute TTL (all caching-compatible models)
      - "1h": 1-hour TTL (most current models; ~2x write premium instead of ~1.25x)
    """


class AnthropicMessagesConfig(BaseModel):
    """Configuration for AnthropicMessagesModel."""

    max_tokens: int = 4096
    """REQUIRED by the Anthropic Messages API (unlike OpenAI/Bedrock, where
    it's optional) — always sent on every request. Increase for long outputs;
    the API rejects `max_tokens` values it estimates will exceed model limits."""

    temperature: float | None = None
    """None -> omitted, API uses its own default (1.0). Several current
    models reject non-default temperature/top_p/top_k entirely when adaptive
    thinking is in play — leave unset unless you have a specific reason."""

    top_p: float | None = None
    top_k: int | None = None
    stop_sequences: list[str] | None = None

    thinking: AnthropicMessagesThinkingConfig = AnthropicMessagesThinkingConfig()
    """Grouped thinking settings. See AnthropicMessagesThinkingConfig."""

    prompt_caching: AnthropicMessagesPromptCachingConfig = (
        AnthropicMessagesPromptCachingConfig()
    )
    """Grouped prompt caching settings. See AnthropicMessagesPromptCachingConfig."""
