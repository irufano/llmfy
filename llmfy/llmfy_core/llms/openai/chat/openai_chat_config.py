
from pydantic import BaseModel


class OpenAIChatThinkingConfig(BaseModel):
    """Grouped reasoning settings for OpenAIChatModel.

    Applies to o-series reasoning models and the GPT-5.x family:
      - o1, o1-mini, o3, o3-mini, o4-mini (and any future o-series models)
      - gpt-5, gpt-5.1, gpt-5.2, gpt-5.4, gpt-5.5, gpt-5.5-pro (and later
        GPT-5.x releases)

    o-series models always reason internally — `enabled` only controls whether
    `reasoning_effort` is sent explicitly; it does not turn reasoning off.
    GPT-5.x models are hybrid — reasoning can be minimized via effort='minimal'
    but the field must still be set through this same reasoning_effort
    mechanism.
    """

    enabled: bool = False
    """Master switch. False: reasoning_effort is never sent, the API falls back
    to its own default for the model. True: reasoning_effort is sent (see effort
    below).

    Supported models:
      - o1
      - o1-mini
      - o3
      - o3-mini
      - o4-mini
      (and any future o-series reasoning models)
      - gpt-5, gpt-5.1, gpt-5.2, gpt-5.4, gpt-5.5, gpt-5.5-pro
      (and later GPT-5.x releases)
    """

    effort: str | None = None
    """'low', 'medium', or 'high' — supported on o-series and GPT-5.x alike.
    'minimal' is additionally available on GPT-5.x only (not o-series).
    Sent as reasoning_effort via the Chat Completions API. Defaults to 'medium'
    when enabled=True and left unset.

    Supported models:
      - o1, o1-mini, o3, o3-mini, o4-mini — 'low'/'medium'/'high'
      - gpt-5, gpt-5.1, gpt-5.2, gpt-5.4, gpt-5.5, gpt-5.5-pro —
        'minimal'/'low'/'medium'/'high'
    """


class OpenAIChatPromptCachingConfig(BaseModel):
    """Grouped prompt caching settings for OpenAIChatModel.

    Reference: https://platform.openai.com/docs/guides/prompt-caching

    OpenAI applies caching automatically for all API requests — no explicit
    markers or request changes are needed. `enabled` does not alter the
    request; it signals intent and ensures cache usage stats appear in usage
    details.

    How it works:
      - The longest common prompt prefix is cached server-side automatically.
      - Requests that reuse the same prefix within the TTL window benefit from
        cached tokens. No additional fees are associated with prompt caching.
      - Static content (system prompt, documents) must appear at the beginning
        of the prompt; images and tool definitions must be identical across calls.

    Cache TTL:
      - Standard:          5–10 minutes of inactivity; maximum 1 hour
      - Extended (24h):    gpt-5.5, gpt-5.5-pro, gpt-5.4, gpt-5.2, gpt-5.1, gpt-5,
                           gpt-4.1, and select other models

    Minimum: prompts must contain at least 1,024 tokens to be cached. Requests
    below this threshold show zero cached tokens.

    Supported models (all gpt-4o and newer — caching is automatic):
      GPT-4o family:
        - gpt-4o, gpt-4o-mini (and all dated snapshots)
      GPT-4.1 family:
        - gpt-4.1, gpt-4.1-mini, gpt-4.1-nano
      o-series reasoning models:
        - o1, o1-mini, o3, o3-mini, o3-pro, o4-mini
      GPT-5 family (extended 24h retention):
        - gpt-5, gpt-5.1, gpt-5.2, gpt-5.4, gpt-5.5, gpt-5.5-pro

    Not supported: gpt-3.5-turbo, gpt-4 (non-turbo), and older generation models.

    Cached tokens are reported in usage details as cache_read_tokens whenever
    the API returns prompt_tokens_details.cached_tokens.
    """

    enabled: bool = False
    """Intent flag documenting that prompt caching is desired. Does not alter
    the request — OpenAI caches automatically regardless of this flag. Set it
    to True so cache usage stats are surfaced in usage details.

    Supported models: see class docstring."""


class OpenAIChatConfig(BaseModel):
    """Configuration for OpenAIChatModel."""

    temperature: float = 0.7
    max_tokens: int | None = None
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0

    # Thinking / reasoning — grouped so all reasoning-related fields live in one place
    thinking: OpenAIChatThinkingConfig = OpenAIChatThinkingConfig()
    """Grouped reasoning settings. See OpenAIChatThinkingConfig for supported models
    and field details."""

    # Prompt caching — grouped so all caching-related fields live in one place
    prompt_caching: OpenAIChatPromptCachingConfig = OpenAIChatPromptCachingConfig()
    """Grouped prompt caching settings. See OpenAIChatPromptCachingConfig for
    supported models and details — caching itself is automatic on OpenAI's
    side; this is an intent flag for usage-stat visibility."""
