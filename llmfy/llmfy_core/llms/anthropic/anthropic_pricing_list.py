"""
Price per 1M tokens for different Claude models (USD), for the native
Anthropic Messages API (api.anthropic.com).

References:
- https://platform.claude.com/docs/en/about-claude/pricing
- https://platform.claude.com/docs/en/about-claude/models/overview

Flat model -> pricing shape (NOT region-keyed like `BEDROCK_PRICING` — native
Anthropic API pricing does not vary by region), shared across all Anthropic
API variants (per-model, not per-endpoint).

Completeness:
- This list does not cover every Claude model/alias. If your model is
  missing, define a custom pricing dict and pass it via
  `llmfy_usage_tracker(anthropic_pricing=prices)`.

Cache pricing:
- `cache_read`/`cache_write` are left unset below, so `LLMfyUsage` falls back
  to the standard ratios (~10% of input for cache reads, ~125% of input for
  cache writes — the 5-minute TTL rate). The 1-hour TTL write premium is
  ~200% of input instead of ~125% — set `cache_write` explicitly per model
  via a custom pricing dict if you need that modeled precisely.
"""

ANTHROPIC_PRICING = {
    # ── Claude 5 family ──────────────────────────────────────────────────────
    "claude-opus-5": {
        "input": 5.50,
        "output": 27.50,
        "token_unit": 1_000_000,
    },
    "claude-sonnet-5": {
        "input": 3.30,
        "output": 16.50,
        "token_unit": 1_000_000,
    },
    "claude-fable-5": {
        "input": 5.50,
        "output": 27.50,
        "token_unit": 1_000_000,
    },
    "claude-haiku-4-5": {
        "input": 1.10,
        "output": 5.50,
        "token_unit": 1_000_000,
    },
    "claude-haiku-4-5-20251001": {
        "input": 1.10,
        "output": 5.50,
        "token_unit": 1_000_000,
    },
    # ── Claude 4.x series ────────────────────────────────────────────────────
    "claude-opus-4-6": {
        "input": 5.50,
        "output": 27.50,
        "token_unit": 1_000_000,
    },
    "claude-sonnet-4-6": {
        "input": 3.30,
        "output": 16.50,
        "token_unit": 1_000_000,
    },
    "claude-opus-4-5-20251101": {
        "input": 5.50,
        "output": 27.50,
        "token_unit": 1_000_000,
    },
    "claude-sonnet-4-5-20250929": {
        "input": 3.30,
        "output": 16.50,
        "token_unit": 1_000_000,
    },
    "claude-sonnet-4-20250514": {
        "input": 3.00,
        "output": 15.00,
        "token_unit": 1_000_000,
    },
    "claude-3-7-sonnet-20250219": {
        "input": 3.00,
        "output": 15.00,
        "token_unit": 1_000_000,
    },
    "claude-3-5-sonnet-20241022": {
        "input": 3.00,
        "output": 15.00,
        "token_unit": 1_000_000,
    },
    "claude-3-5-sonnet-20240620": {
        "input": 3.00,
        "output": 15.00,
        "token_unit": 1_000_000,
    },
    "claude-3-5-haiku-20241022": {
        "input": 0.80,
        "output": 4.00,
        "token_unit": 1_000_000,
    },
    "claude-3-opus-20240229": {
        "input": 15.00,
        "output": 75.00,
        "token_unit": 1_000_000,
    },
    "claude-3-haiku-20240307": {
        "input": 0.25,
        "output": 1.25,
        "token_unit": 1_000_000,
    },
}
