from typing import List, Optional

from pydantic import BaseModel


class BedrockConfig(BaseModel):
    """Configuration for BedrockModel."""

    temperature: Optional[float] = 0.7
    """Must be set to None when enable_thinking=True (Claude extended thinking) or
    when reasoning_effort='high' (Nova 2 Lite). The API returns an error otherwise."""
    max_tokens: Optional[int] = None
    top_p: Optional[float] = 1.0
    """Must be set to None when enable_thinking=True (Claude extended thinking)."""
    top_k: Optional[int] = None
    stopSequences: Optional[List[str]] = None

    # Unified thinking toggle
    enable_thinking: bool = False
    """Enable thinking/reasoning mode. Supported models:

    Claude extended thinking (use with thinking_budget_tokens):
      - anthropic.claude-3-7-sonnet-20250219-v1:0
      - anthropic.claude-sonnet-4-20250514-v1:0
      - anthropic.claude-opus-4-20250514-v1:0
      - anthropic.claude-sonnet-4-5-20250929-v1:0
      - anthropic.claude-haiku-4-5-20251001-v1:0
      - anthropic.claude-opus-4-5-20251101-v1:0

    Claude adaptive thinking (use with thinking_type='adaptive'):
      - anthropic.claude-sonnet-4-6
      - anthropic.claude-opus-4-6-v1
      - anthropic.claude-opus-4-7         (adaptive only)
      - anthropic.claude-fable-5          (adaptive only)
      - anthropic.claude-mythos-5         (adaptive only)

    Amazon Nova 2 reasoning (use with reasoning_effort):
      - us.amazon.nova-2-lite-v1:0
    """

    # Claude extended thinking — Claude 3.7 Sonnet, Claude 4 Sonnet/Opus/Haiku,
    # Claude Sonnet/Haiku/Opus 4.5
    thinking_budget_tokens: Optional[int] = None
    """Token budget for extended thinking (thinking_type='enabled'). Min 1024.
    temperature, top_p, and top_k must be None when using extended thinking."""

    # Claude adaptive thinking — Claude Sonnet/Opus 4.6, Fable 5, Mythos 5, Opus 4.7
    thinking_type: Optional[str] = None
    """'enabled' = extended thinking with thinking_budget_tokens (older Claude models).
    'adaptive' = adaptive thinking with optional thinking_effort (Claude 4.6+ / Fable 5 / Mythos 5).
    Fable 5, Mythos 5, Opus 4.7 only accept 'adaptive' — 'enabled' returns 400."""
    thinking_effort: Optional[str] = None
    """For adaptive thinking (thinking_type='adaptive'): 'low', 'medium', 'high', or 'max'.
    'max' is only available on Claude Opus 4.6.
    Placed in output_config (not inside thinking) — the API returns 400 if placed inside thinking."""

    # Amazon Nova 2 Lite reasoning — us.amazon.nova-2-lite-v1:0
    reasoning_effort: Optional[str] = None
    """For Amazon Nova 2 Lite only: 'low', 'medium', or 'high'. Uses reasoningConfig format.
    When set, overrides Claude thinking format (reasoningConfig takes precedence).
    'high' requires temperature, top_p, and max_tokens to be None."""

    # Prompt caching
    enable_prompt_caching: bool = False
    """Enable prompt caching via the Converse API cachePoint mechanism.

    References:
      - https://docs.aws.amazon.com/bedrock/latest/userguide/prompt-caching.html
      - https://docs.aws.amazon.com/bedrock/latest/userguide/model-cards.html

    When True, cachePoint markers are injected into the request:
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
      enable_prompt_caching=True has no effect on Nova models.
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

    prompt_caching_ttl: Optional[str] = None
    """Cache time-to-live for the cachePoint markers. Accepted values:
      - None (default): uses AWS default of 5 minutes
      - "5m":  5-minute cache (all caching-compatible models)
      - "1h":  1-hour cache (Claude 4.5, 4.6, 4.8, Fable 5 — see enable_prompt_caching
               for the per-model TTL support table)

    When multiple cachePoints with different TTLs exist in the same request,
    longer-TTL entries ("1h") must appear before shorter-TTL entries ("5m").

    The TTL is included in the injected cachePoint:
      {"cachePoint": {"type": "default", "ttl": "1h"}}
    """
