"""
Price per 1M tokens for different models (USD):

- [https://platform.openai.com/docs/pricing](https://platform.openai.com/docs/pricing)

Note: Prices are per 1M tokens (token_unit = 1_000_000).
Verify current prices at the OpenAI pricing page as they may change.

Completeness:
- This list does not cover all available OpenAI models. If your model is missing or has
  different pricing, define a custom pricing dict and pass it via
  `llmfy_usage_tracker(openai_pricing=prices)`.
"""
OPENAI_PRICING = {
    # ── GPT-5.x series ────────────────────────────────────────────────────────
    # GPT-5.6+ family: cached_input = 10% of input, cache_write = 1.25x of input
    "gpt-5.6-sol": {
        "input": 5.00,
        "output": 30.00,
        "cache_read": 0.50,
        "cache_write": 6.25,
        "token_unit": 1_000_000,
    },
    "gpt-5.6-terra": {
        "input": 2.50,
        "output": 15.00,
        "cache_read": 0.25,
        "cache_write": 3.125,
        "token_unit": 1_000_000,
    },
    "gpt-5.6-luna": {
        "input": 1.00,
        "output": 6.00,
        "cache_read": 0.10,
        "cache_write": 1.25,
        "token_unit": 1_000_000,
    },
    # Pre-GPT-5.6: cached_input = 50% of input, no cache_write fee
    "gpt-5.5": {
        "input": 5.00,
        "output": 30.00,
        "cache_read": 2.50,
        "token_unit": 1_000_000,
    },
    "gpt-5.5-pro": {
        "input": 30.00,
        "output": 180.00,
        "cache_read": 15.00,
        "token_unit": 1_000_000,
    },
    "gpt-5.4": {
        "input": 2.50,
        "output": 15.00,
        "cache_read": 1.25,
        "token_unit": 1_000_000,
    },
    "gpt-5.4-mini": {
        "input": 0.75,
        "output": 4.50,
        "cache_read": 0.375,
        "token_unit": 1_000_000,
    },
    "gpt-5.4-nano": {
        "input": 0.20,
        "output": 1.25,
        "cache_read": 0.10,
        "token_unit": 1_000_000,
    },
    "gpt-5.4-pro": {
        "input": 30.00,
        "output": 180.00,
        "cache_read": 15.00,
        "token_unit": 1_000_000,
    },
    # ── GPT-4.1 ───────────────────────────────────────────────────────────────
    "gpt-4.1": {
        "input": 2.00,
        "output": 8.00,
        "cache_read": 1.00,
        "token_unit": 1_000_000,
    },
    "gpt-4.1-mini": {
        "input": 0.40,
        "output": 1.60,
        "cache_read": 0.20,
        "token_unit": 1_000_000,
    },
    "gpt-4.1-nano": {
        "input": 0.10,
        "output": 0.40,
        "cache_read": 0.05,
        "token_unit": 1_000_000,
    },
    # ── GPT-4o ────────────────────────────────────────────────────────────────
    "gpt-4o": {
        "input": 2.50,
        "output": 10.00,
        "cache_read": 1.25,
        "token_unit": 1_000_000,
    },
    "gpt-4o-mini": {
        "input": 0.15,
        "output": 0.60,
        "cache_read": 0.075,
        "token_unit": 1_000_000,
    },
    # ── o-series (reasoning models) ───────────────────────────────────────────
    "o3": {
        "input": 10.00,
        "output": 40.00,
        "cache_read": 5.00,
        "token_unit": 1_000_000,
    },
    "o3-mini": {
        "input": 1.10,
        "output": 4.40,
        "cache_read": 0.55,
        "token_unit": 1_000_000,
    },
    "o4-mini": {
        "input": 1.10,
        "output": 4.40,
        "cache_read": 0.55,
        "token_unit": 1_000_000,
    },
    "o1": {
        "input": 15.00,
        "output": 60.00,
        "cache_read": 7.50,
        "token_unit": 1_000_000,
    },
    "o1-mini": {
        "input": 1.10,
        "output": 4.40,
        "cache_read": 0.55,
        "token_unit": 1_000_000,
    },
    "o1-pro": {
        "input": 150.00,
        "output": 600.00,
        "token_unit": 1_000_000,
    },
    # ── GPT-4 Turbo ───────────────────────────────────────────────────────────
    "gpt-4-turbo": {
        "input": 10.00,
        "output": 30.00,
        "token_unit": 1_000_000,
    },
    # ── GPT-4 ─────────────────────────────────────────────────────────────────
    "gpt-4": {
        "input": 30.00,
        "output": 60.00,
        "token_unit": 1_000_000,
    },
    # ── GPT-3.5 ───────────────────────────────────────────────────────────────
    "gpt-3.5-turbo": {
        "input": 0.50,
        "output": 1.50,
        "token_unit": 1_000_000,
    },
    # ── Embeddings ────────────────────────────────────────────────────────────
    "text-embedding-3-large": {
        "input": 0.13,
        "output": 0,
        "token_unit": 1_000_000,
    },
    "text-embedding-3-small": {
        "input": 0.02,
        "output": 0,
        "token_unit": 1_000_000,
    },
    "text-embedding-ada-002": {
        "input": 0.10,
        "output": 0,
        "token_unit": 1_000_000,
    },
}
