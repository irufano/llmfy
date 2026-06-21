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
