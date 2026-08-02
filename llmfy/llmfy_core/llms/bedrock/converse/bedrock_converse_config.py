from typing import Literal

from pydantic import BaseModel


class BedrockConverseThinkingConfig(BaseModel):
    """Grouped thinking/reasoning settings for BedrockConverseModel.

    Bedrock exposes three distinct thinking modes depending on the model family.
    Only set the field(s) relevant to the mode your model uses — the others are
    ignored.

    Claude extended thinking (use with budget_tokens):
      - anthropic.claude-3-7-sonnet-20250219-v1:0
      - anthropic.claude-sonnet-4-20250514-v1:0
      - anthropic.claude-opus-4-20250514-v1:0
      - anthropic.claude-sonnet-4-5-20250929-v1:0
      - anthropic.claude-haiku-4-5-20251001-v1:0
      - anthropic.claude-opus-4-5-20251101-v1:0

    Claude adaptive thinking (use with type='adaptive' + effort):
      - anthropic.claude-sonnet-4-6
      - anthropic.claude-opus-4-6-v1
      - anthropic.claude-opus-4-7         (adaptive only)
      - anthropic.claude-fable-5          (adaptive only)
      - anthropic.claude-mythos-5         (adaptive only)

    Amazon Nova 2 reasoning (use with reasoning_effort):
      - us.amazon.nova-2-lite-v1:0
    """

    enabled: bool = False
    """Master switch. False: no thinking-related field is sent to Bedrock at all —
    the model behaves as a standard non-reasoning call. True: the request is built
    from whichever of the fields below are set (reasoning_effort takes priority,
    then type='adaptive', then extended thinking as the fallback)."""

    budget_tokens: int | None = None
    """Claude extended thinking only (type left unset or 'enabled'). Token budget
    for the reasoning pass. Min 1024. Requires BedrockConverseConfig.temperature, top_p,
    and top_k to all be None — the API errors otherwise.

    Supported models:
      - anthropic.claude-3-7-sonnet-20250219-v1:0
      - anthropic.claude-sonnet-4-20250514-v1:0
      - anthropic.claude-opus-4-20250514-v1:0
      - anthropic.claude-sonnet-4-5-20250929-v1:0
      - anthropic.claude-haiku-4-5-20251001-v1:0
      - anthropic.claude-opus-4-5-20251101-v1:0
    """

    type: Literal["adaptive"] | None = None
    """Claude thinking mode selector: 'enabled' (extended thinking, the default
    when left unset) or 'adaptive'. Fable 5, Mythos 5, and Opus 4.7 only accept
    'adaptive' — 'enabled' returns a 400 on those models.

    Supported models (adaptive):
      - anthropic.claude-sonnet-4-6
      - anthropic.claude-opus-4-6-v1
      - anthropic.claude-opus-4-7         (adaptive only)
      - anthropic.claude-fable-5          (adaptive only)
      - anthropic.claude-mythos-5         (adaptive only)
    """

    effort: str | None = None
    """Claude adaptive thinking only (type='adaptive'): 'low', 'medium', 'high',
    or 'max'. 'max' is Opus 4.6 only. Sent via output_config rather than inside
    the thinking block — the API returns 400 if placed inside thinking.

    Supported models:
      - anthropic.claude-sonnet-4-6
      - anthropic.claude-opus-4-6-v1      ('max' effort supported)
      - anthropic.claude-opus-4-7
      - anthropic.claude-fable-5
      - anthropic.claude-mythos-5
    """

    reasoning_effort: str | None = None
    """Amazon Nova 2 Lite only: 'low', 'medium', or 'high'. Uses the Nova
    reasoningConfig request format instead of Claude's thinking block — when set,
    it takes priority over type/effort above. 'high' requires BedrockConverseConfig
    temperature, top_p, and max_tokens to all be None.

    Supported models:
      - us.amazon.nova-2-lite-v1:0
    """


class BedrockConversePromptCachingConfig(BaseModel):
    """Grouped prompt caching settings for BedrockConverseModel.

    Enables prompt caching via the Converse API cachePoint mechanism.

    References:
      - https://docs.aws.amazon.com/bedrock/latest/userguide/prompt-caching.html
      - https://docs.aws.amazon.com/bedrock/latest/userguide/model-cards.html

    When enabled=True, cachePoint markers are injected into the request:
      - After the system content (when a system prompt is present)
      - At the end of the last message content

    Supported Anthropic Claude models (from AWS model cards + prompt caching docs):

      Claude 3.5 / 3.7 series (min 1,024 tokens per checkpoint):
        - anthropic.claude-3-5-sonnet-20241022-v2:0      TTL: 5m only
        - anthropic.claude-3-7-sonnet-20250219-v1:0      TTL: 5m only

      Claude 4 series (min 1,024 tokens per checkpoint):
        - anthropic.claude-opus-4-20250514-v1:0          TTL: 5m only

      Claude 4.5 series (min 4,096 tokens per checkpoint):
        - anthropic.claude-haiku-4-5-20251001-v1:0       TTL: 5m and 1h
        - anthropic.claude-sonnet-4-5-20250929-v1:0      TTL: 5m and 1h
        - anthropic.claude-opus-4-5-20251101-v1:0        TTL: 5m and 1h

      Claude 4.6 series (min 1,024 tokens per checkpoint):
        - anthropic.claude-sonnet-4-6                    TTL: 5m and 1h
        - anthropic.claude-opus-4-6-v1                   TTL: 5m and 1h

      Claude 4.8 / Fable 5 (min 4,096 and 1,024 tokens respectively):
        - anthropic.claude-opus-4-8                      TTL: 5m and 1h (min 4,096)
        - anthropic.claude-fable-5                       TTL: 5m and 1h (min 1,024)

    Cross-region inference IDs (us., eu. prefixes) are also supported,
    e.g. us.anthropic.claude-3-5-sonnet-20241022-v2:0.

    Amazon Nova (automatic — cachePoint NOT required):
      Nova models cache text prompts automatically without any cachePoint marker.
      enabled=True has no effect on Nova models.
      - amazon.nova-lite-v1:0
      - amazon.nova-pro-v1:0

    Not supported: Meta Llama, DeepSeek, Mistral, and any model not listed above.
    Prompt caching is exclusive to Anthropic Claude and Amazon Nova on Bedrock.

    Pricing:
      - Cache reads:  ~10% of normal input price (~90% savings)
      - Cache writes: ~125% of normal input price (one-time on first write)
      - Standard tokens: billed at regular rate
      - On-demand inference only — NOT compatible with the Batch API

    General constraints:
      - Maximum 4 cachePoint checkpoints per request
      - Checkpoints are evaluated cumulatively: tools → system → messages
      - The cached prefix must be byte-identical on subsequent requests
      - Cross-region inference (us., eu., ap. prefixes) is supported

    Cache read and write tokens are reported in usage details as
    cache_read_tokens and cache_write_tokens.
    """

    enabled: bool = False
    """Master switch. False: no cachePoint markers are injected — request is
    sent as-is. True: cachePoint markers are added after the system content
    and at the end of the last message content.

    Supported models: see class docstring — Anthropic Claude (explicit
    cachePoint) and Amazon Nova (automatic, this flag has no effect)."""

    ttl: str | None = None
    """Cache time-to-live for the cachePoint markers. Accepted values:
      - None (default): uses AWS default of 5 minutes
      - "5m":  5-minute cache (all caching-compatible models)
      - "1h":  1-hour cache (Claude 4.5, 4.6, 4.8, Fable 5 — see class
               docstring for the per-model TTL support table)

    When multiple cachePoints with different TTLs exist in the same request,
    longer-TTL entries ("1h") must appear before shorter-TTL entries ("5m").

    The TTL is included in the injected cachePoint:
      {"cachePoint": {"type": "default", "ttl": "1h"}}

    Supported models: Claude 4.5, 4.6, 4.8, and Fable 5 support "1h"; all
    caching-compatible Claude models support "5m" (see class docstring)."""


class BedrockConverseConfig(BaseModel):
    """Configuration for BedrockConverseModel."""

    temperature: float | None = 0.7
    """Must be set to None when thinking.enabled=True (Claude extended thinking) or
    when thinking.reasoning_effort='high' (Nova 2 Lite). The API returns an error
    otherwise."""
    max_tokens: int | None = None
    top_p: float | None = 1.0
    """Must be set to None when thinking.enabled=True (Claude extended thinking)."""
    top_k: int | None = None
    stopSequences: list[str] | None = None

    # Thinking / reasoning — grouped so all thinking-related fields live in one place
    thinking: BedrockConverseThinkingConfig = BedrockConverseThinkingConfig()
    """Grouped thinking/reasoning settings. See BedrockConverseThinkingConfig for which
    fields apply to which model family (Claude extended, Claude adaptive, or
    Amazon Nova 2 Lite reasoning)."""

    # Prompt caching — grouped so all caching-related fields live in one place
    prompt_caching: BedrockConversePromptCachingConfig = BedrockConversePromptCachingConfig()
    """Grouped prompt caching settings. See BedrockConversePromptCachingConfig for
    supported models, TTL rules, and pricing."""
