from pydantic import BaseModel


class OpenAIResponsesReasoningConfig(BaseModel):
    """Grouped reasoning settings for OpenAIResponsesModel.

    The Responses API nests reasoning under a `reasoning: {effort, summary}`
    object, unlike Chat Completions' top-level `reasoning_effort` string.

    Applies to o-series reasoning models and the GPT-5.x family, same as
    `OpenAIChatThinkingConfig` (see that class for the supported-model list).
    """

    enabled: bool = False
    """Master switch. False: `reasoning` is never sent, the API falls back to
    its own default for the model. True: `reasoning` is sent (see effort/summary
    below)."""

    effort: str | None = None
    """One of 'none', 'minimal', 'low', 'medium', 'high', 'xhigh', 'max'.
    Sent as `reasoning.effort`. Defaults to 'medium' when enabled=True and left
    unset. Not every value is supported by every model — check the model's docs."""

    summary: str | None = None
    """One of 'auto', 'concise', 'detailed'. Sent as `reasoning.summary` to
    request a summary of the model's internal reasoning, useful for debugging.
    Left unset (None) omits the field."""


class OpenAIResponsesPromptCachingConfig(BaseModel):
    """Grouped prompt caching settings for OpenAIResponsesModel.

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


class OpenAIResponsesConfig(BaseModel):
    """Configuration for OpenAIResponsesModel."""

    temperature: float = 0.7
    max_output_tokens: int | None = None
    top_p: float = 1.0

    # Thinking / reasoning — grouped so all reasoning-related fields live in one place
    reasoning: OpenAIResponsesReasoningConfig = OpenAIResponsesReasoningConfig()
    """Grouped reasoning settings. See OpenAIResponsesReasoningConfig for
    supported models and field details."""

    # Prompt caching
    prompt_caching: OpenAIResponsesPromptCachingConfig = (
        OpenAIResponsesPromptCachingConfig()
    )
    """Grouped prompt caching settings. See OpenAIResponsesPromptCachingConfig for
    supported models and details."""
