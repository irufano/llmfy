from typing import Any, List, Optional

from pydantic import BaseModel


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
    max_tokens: Optional[int] = None
    """Maps to max_output_tokens in GenerateContentConfig."""
    top_p: Optional[float] = None
    top_k: Optional[int] = None
    stop_sequences: Optional[List[str]] = None
    candidate_count: Optional[int] = None
    seed: Optional[int] = None

    # Penalty params
    presence_penalty: Optional[float] = None
    frequency_penalty: Optional[float] = None

    # Response format
    response_mime_type: Optional[str] = None
    """e.g. 'application/json' for structured output."""
    response_schema: Optional[Any] = None
    """Schema for structured output. Used with response_mime_type='application/json'."""

    # Safety
    safety_settings: Optional[List[Any]] = None
    """List of google.genai.types.SafetySetting instances."""

    # Thinking — unified fields
    enable_thinking: bool = False
    """Enable extended thinking. Supported models:

    Gemini 2.5 series (use thinking_budget_tokens for token-based control):
      - gemini-2.5-pro
      - gemini-2.5-flash
      - gemini-2.5-flash-lite

    Gemini 3 series (use thinking_level for named effort control):
      - gemini-3-flash
      - gemini-3.1-pro
      - gemini-3.1-flash-lite
      - gemini-3.5-flash

    And latest
    """
    thinking_budget_tokens: Optional[int] = None
    """Token budget for thinking. -1 = dynamic (model decides), 0 = disable explicit budget.
    Maps to thinking_budget in ThinkingConfig."""
    thinking_level: Optional[str] = None
    """Named effort level: 'MINIMAL', 'LOW', 'MEDIUM', 'HIGH'.
    Alternative to thinking_budget_tokens — use one or the other."""
    thinking_include_thoughts: Optional[bool] = None
    """Whether to include thinking steps in the response content parts."""

    # Raw thinking override (backward compat — takes priority over unified fields above)
    thinking_config: Optional[Any] = None
    """google.genai.types.ThinkingConfig instance. When set, takes priority over
    enable_thinking / thinking_budget_tokens / thinking_level / thinking_include_thoughts."""

    # Prompt caching
    enable_prompt_caching: bool = False
    """Intent flag documenting that prompt caching is desired.

    Reference: https://ai.google.dev/gemini-api/docs/caching

    Google AI supports two types of caching:

    1. Explicit caching (cachedContent):
       Create a cache externally and pass its name via cached_content.
       Guarantees cached tokens are served and billed at reduced rates.

    2. Implicit caching (automatic, Gemini 2.5 and newer):
       Enabled by default on all Gemini 2.5+ models — no setup needed.
       Cache hits are NOT guaranteed; billing benefit applies when a hit occurs.

    This flag does not alter the request on its own; set cached_content to
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

    Note: Use the full model path format (e.g. 'models/gemini-2.5-flash') when
    creating the cache. The generation request model must match exactly.

    Cache read tokens are reported in usage details as cache_read_tokens.
    """

    cached_content: Optional[str] = None
    """Resource name of a pre-created Google AI cached content object,
    e.g. 'cachedContents/abc123efg456'. When set, passed directly to
    GenerateContentConfig so the model serves tokens from the cache.

    Reference: https://ai.google.dev/gemini-api/docs/caching

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
      - This field is independent of enable_prompt_caching — the cache is used
        whenever this field is non-None.
      - Do not repeat the cached content in the request body; structure prompts
        so the cached portion appears only in the cache object, not also in
        system_instruction or messages.

    Cache read tokens are reported in usage details as cache_read_tokens.
    """
