from typing import Any

from pydantic import BaseModel


class GoogleAIThinkingConfig(BaseModel):
    """Grouped thinking settings for GoogleAIModel.

    Supported models:

    Gemini 2.5 series (use budget_tokens for token-based control):
      - gemini-2.5-pro       (cannot fully disable — has a non-zero minimum
                               thinking budget even when this config is unset)
      - gemini-2.5-flash
      - gemini-2.5-flash-lite

    Gemini 3 series (use level for named effort control):
      - gemini-3-flash
      - gemini-3.1-pro
      - gemini-3.1-flash-lite
      - gemini-3.5-flash

    And latest.
    """

    enabled: bool = False
    """Master switch. False: no ThinkingConfig is sent — the model falls back to
    its own default. True: a ThinkingConfig is built from budget_tokens / level /
    include_thoughts below. Ignored when raw is set."""

    budget_tokens: int | None = None
    """Token budget for thinking. -1 = dynamic (model decides), 0 = disable
    explicit budget. Maps to thinking_budget in ThinkingConfig. Alternative to
    level — use one or the other.

    Supported models (Gemini 2.5 series — preferred control here):
      - gemini-2.5-pro       (0 not supported — non-zero minimum budget, cannot
                               fully disable)
      - gemini-2.5-flash     (0 = fully disable thinking)
      - gemini-2.5-flash-lite (0 = fully disable thinking)
    """

    level: str | None = None
    """Named effort level: 'MINIMAL', 'LOW', 'MEDIUM', 'HIGH'. Alternative to
    budget_tokens — use one or the other.

    Supported models (Gemini 3 series — preferred control here):
      - gemini-3-flash
      - gemini-3.1-pro
      - gemini-3.1-flash-lite
      - gemini-3.5-flash
    """

    include_thoughts: bool | None = None
    """Whether to include thinking steps in the response content parts.

    Supported models: all Gemini 2.5+ and Gemini 3 series models listed above.
    """

    raw: Any | None = None
    """Escape hatch (backward compat): a pre-built google.genai.types.ThinkingConfig
    instance. When set, takes priority over enabled / budget_tokens / level /
    include_thoughts above.

    Supported models: any model accepted by google.genai's ThinkingConfig —
    use this to pass provider-specific fields not yet covered by the unified
    fields above.
    """


class GoogleAIPromptCachingConfig(BaseModel):
    """Grouped prompt caching settings for GoogleAIModel.

    Reference: https://ai.google.dev/gemini-api/docs/caching

    Google AI supports two types of caching:

    1. Explicit caching (cachedContent):
       Create a cache externally and pass its name via cached_content.
       Guarantees cached tokens are served and billed at reduced rates.

    2. Implicit caching (automatic, Gemini 2.5 and newer):
       Enabled by default on all Gemini 2.5+ models — no setup needed.
       Cache hits are NOT guaranteed; billing benefit applies when a hit occurs.

    `enabled` does not alter the request on its own; set cached_content to
    use explicit caching, or rely on implicit caching for Gemini 2.5+ models.

    Pricing:
      - Explicit cache reads: ~25% of normal input price (~75% savings)
      - Implicit cache reads: reduced rate when a hit occurs (no guarantee)
      - Cache storage:        charged per token-hour (varies by model)
      - Default TTL:          1 hour; no minimum or maximum bounds enforced

    Minimum tokens for explicit cache creation (enforced at cache creation time):
      - gemini-2.5-pro, gemini-2.5-flash:  2,048 tokens
      - gemini-3.5-flash, gemini-3.1-pro:  4,096 tokens

    Supported models for explicit caching (cachedContent):
      Gemini 2.5 family:
        - models/gemini-2.5-pro
        - models/gemini-2.5-flash
      Gemini 3.x family:
        - models/gemini-3.1-pro-preview
        - models/gemini-3.5-flash

    Implicit caching (automatic, no cached_content required):
      - All Gemini 2.5 and newer models have implicit caching enabled by default.

    Cache read tokens are reported in usage details as cache_read_tokens.
    """

    enabled: bool = False
    """Intent flag documenting that prompt caching is desired. Does not alter
    the request by itself — pair with cached_content for explicit caching, or
    rely on automatic implicit caching on Gemini 2.5+ models.

    Supported models: see class docstring."""

    cached_content: str | None = None
    """Resource name of a pre-created Google AI cached content object,
    e.g. 'cachedContents/abc123efg456'. When set, passed directly to
    GenerateContentConfig so the model serves tokens from the cache.

    Create the cache externally before referencing it here:

      from google import genai
      from google.genai import types

      client = genai.Client(api_key="YOUR_API_KEY")
      cache = client.caches.create(
          model="models/gemini-2.5-flash",    # full model path — must match generation model
          config=types.CreateCachedContentConfig(
              system_instruction="Your system prompt...",
              contents=["Your long document or context..."],
              ttl="3600s",    # cache lifetime; no min/max bounds, default is 1 hour
          ),
      )
      cached_content_name = cache.name   # e.g. 'cachedContents/abc123...'

    Important constraints:
      - The model in caches.create() must exactly match the model used for generation.
      - Minimum tokens required at cache creation (returns 400 if below threshold):
          2,048 tokens for gemini-2.5-pro / gemini-2.5-flash
          4,096 tokens for gemini-3.1-pro-preview / gemini-3.5-flash
      - This field is independent of enabled above — the cache is used
        whenever this field is non-None.
      - Do not repeat the cached content in the request body; structure prompts
        so the cached portion appears only in the cache object, not also in
        system_instruction or messages.

    Cache read tokens are reported in usage details as cache_read_tokens.

    Supported models: models/gemini-2.5-pro, models/gemini-2.5-flash,
    models/gemini-3.1-pro-preview, models/gemini-3.5-flash."""


class GoogleAIConfig(BaseModel):
    """Configuration for GoogleAIModel.

    Maps to `google.genai.types.GenerateContentConfig` parameters.

    Example:
    ```python
    config = GoogleAIConfig(temperature=0.7)
    ```
    """

    # Core generation params
    temperature: float = 0.7
    max_tokens: int | None = None
    """Maps to max_output_tokens in GenerateContentConfig."""
    top_p: float | None = None
    top_k: int | None = None
    stop_sequences: list[str] | None = None
    candidate_count: int | None = None
    seed: int | None = None

    # Penalty params
    presence_penalty: float | None = None
    frequency_penalty: float | None = None

    # Response format
    response_mime_type: str | None = None
    """e.g. 'application/json' for structured output."""
    response_schema: Any | None = None
    """Schema for structured output. Used with response_mime_type='application/json'."""

    # Safety
    safety_settings: list[Any] | None = None
    """List of google.genai.types.SafetySetting instances."""

    # Thinking — grouped so all thinking-related fields live in one place
    thinking: GoogleAIThinkingConfig = GoogleAIThinkingConfig()
    """Grouped thinking settings. See GoogleAIThinkingConfig for supported models
    and field details."""

    # Prompt caching — grouped so all caching-related fields live in one place
    prompt_caching: GoogleAIPromptCachingConfig = GoogleAIPromptCachingConfig()
    """Grouped prompt caching settings. See GoogleAIPromptCachingConfig for
    explicit vs implicit caching, supported models, and pricing."""
