"""
Price per 1M tokens for different models (USD).

References:
- [https://aws.amazon.com/bedrock/pricing/](https://aws.amazon.com/bedrock/pricing/)
- [https://docs.aws.amazon.com/general/latest/gr/bedrock.html](https://docs.aws.amazon.com/general/latest/gr/bedrock.html)

Note: Prices are per 1M tokens (token_unit = 1_000_000).
Verify current prices at the AWS Bedrock pricing page as they may change.

Completeness:
- This list does not cover all available Bedrock models. If your model is missing or has
  different pricing, define a custom pricing dict and pass it via
  `llmfy_usage_tracker(bedrock_pricing=prices)`.

Inference type:
- Prices listed here apply to both Geo and In-region Cross-region Inference profiles.
  AWS charges the same per-token rate regardless of which inference type is used.
- For inference types outside of Geo and In-region Cross-region Inference profiles
  (e.g. Provisioned Throughput, other custom deployments), define a custom pricing dict
  and pass it via `llmfy_usage_tracker(bedrock_pricing=prices)`.
- Reference: https://aws.amazon.com/bedrock/pricing/ (see "Cross-region inference" section)

Model ID matching:
- Keys here must exactly match the model ID passed to the API.
- Default base model IDs use the format: "provider.model-name" (e.g. "anthropic.claude-sonnet-4-6").
- If you use cross-region inference profile IDs (e.g. "us.anthropic.claude-sonnet-4-6",
  "eu.anthropic.claude-sonnet-4-6", "ap.anthropic.claude-sonnet-4-6"), add those prefixed
  IDs as separate entries in a custom pricing dict passed via
  `llmfy_usage_tracker(bedrock_pricing=prices)`.
"""

BEDROCK_PRICING = {
    # ── Anthropic Claude ──────────────────────────────────────────────────────
    # Add entries here once AWS publishes the official Bedrock model IDs and prices.
    "anthropic.claude-opus-4-8": {
        "us-east-1": {
            "region": "US East (N. Virginia)",
            "input": 5.50,
            "output": 27.50,
            "token_unit": 1_000_000,
        },
        "us-west-2": {
            "region": "US West (Oregon)",
            "input": 5.50,
            "output": 27.50,
            "token_unit": 1_000_000,
        },
    },
    "anthropic.claude-opus-4-7": {
        "us-east-1": {
            "region": "US East (N. Virginia)",
            "input": 5.50,
            "output": 27.50,
            "token_unit": 1_000_000,
        },
        "us-west-2": {
            "region": "US West (Oregon)",
            "input": 5.50,
            "output": 27.50,
            "token_unit": 1_000_000,
        },
    },
    "anthropic.claude-opus-4-6-v1": {
        "us-east-1": {
            "region": "US East (N. Virginia)",
            "input": 5.50,
            "output": 27.50,
            "token_unit": 1_000_000,
        },
        "us-west-2": {
            "region": "US West (Oregon)",
            "input": 5.50,
            "output": 27.50,
            "token_unit": 1_000_000,
        },
    },
    "anthropic.claude-sonnet-4-6": {
        "us-east-1": {
            "region": "US East (N. Virginia)",
            "input": 3.30,
            "output": 16.50,
            "token_unit": 1_000_000,
        },
        "us-west-2": {
            "region": "US West (Oregon)",
            "input": 3.30,
            "output": 16.50,
            "token_unit": 1_000_000,
        },
    },
    "anthropic.claude-opus-4-5-20251101-v1:0": {
        "us-east-1": {
            "region": "US East (N. Virginia)",
            "input": 5.50,
            "output": 27.50,
            "token_unit": 1_000_000,
        },
        "us-west-2": {
            "region": "US West (Oregon)",
            "input": 5.50,
            "output": 27.50,
            "token_unit": 1_000_000,
        },
    },
    "anthropic.claude-haiku-4-5-20251001-v1:0": {
        "us-east-1": {
            "region": "US East (N. Virginia)",
            "input": 1.10,
            "output": 5.50,
            "token_unit": 1_000_000,
        },
        "us-west-2": {
            "region": "US West (Oregon)",
            "input": 1.10,
            "output": 5.50,
            "token_unit": 1_000_000,
        },
    },
    "anthropic.claude-sonnet-4-5-20250929-v1:0": {
        "us-east-1": {
            "region": "US East (N. Virginia)",
            "input": 3.30,
            "output": 16.50,
            "token_unit": 1_000_000,
        },
        "us-west-2": {
            "region": "US West (Oregon)",
            "input": 3.30,
            "output": 16.50,
            "token_unit": 1_000_000,
        },
    },
    "anthropic.claude-sonnet-4-20250514-v1:0": {
        "us-east-1": {
            "region": "US East (N. Virginia)",
            "input": 3.00,
            "output": 15.00,
            "token_unit": 1_000_000,
        },
        "us-west-2": {
            "region": "US West (Oregon)",
            "input": 3.00,
            "output": 15.00,
            "token_unit": 1_000_000,
        },
    },
    "anthropic.claude-3-7-sonnet-20250219-v1:0": {
        "us-east-1": {
            "region": "US East (N. Virginia)",
            "input": 3.00,
            "output": 15.00,
            "token_unit": 1_000_000,
        },
        "us-west-2": {
            "region": "US West (Oregon)",
            "input": 3.00,
            "output": 15.00,
            "token_unit": 1_000_000,
        },
    },
    "anthropic.claude-3-5-sonnet-20241022-v2:0": {
        "us-east-1": {
            "region": "US East (N. Virginia)",
            "input": 3.00,
            "output": 15.00,
            "token_unit": 1_000_000,
        },
        "us-west-2": {
            "region": "US West (Oregon)",
            "input": 3.00,
            "output": 15.00,
            "token_unit": 1_000_000,
        },
    },
    "anthropic.claude-3-5-sonnet-20240620-v1:0": {
        "us-east-1": {
            "region": "US East (N. Virginia)",
            "input": 3.00,
            "output": 15.00,
            "token_unit": 1_000_000,
        },
        "us-west-2": {
            "region": "US West (Oregon)",
            "input": 3.00,
            "output": 15.00,
            "token_unit": 1_000_000,
        },
    },
    "anthropic.claude-3-5-haiku-20241022-v1:0": {
        "us-east-1": {
            "region": "US East (N. Virginia)",
            "input": 0.80,
            "output": 4.00,
            "token_unit": 1_000_000,
        },
        "us-west-2": {
            "region": "US West (Oregon)",
            "input": 0.80,
            "output": 4.00,
            "token_unit": 1_000_000,
        },
    },
    "anthropic.claude-3-opus-20240229-v1:0": {
        "us-east-1": {
            "region": "US East (N. Virginia)",
            "input": 15.00,
            "output": 75.00,
            "token_unit": 1_000_000,
        },
        "us-west-2": {
            "region": "US West (Oregon)",
            "input": 15.00,
            "output": 75.00,
            "token_unit": 1_000_000,
        },
    },
    "anthropic.claude-3-sonnet-20240229-v1:0": {
        "us-east-1": {
            "region": "US East (N. Virginia)",
            "input": 3.00,
            "output": 15.00,
            "token_unit": 1_000_000,
        },
        "us-west-2": {
            "region": "US West (Oregon)",
            "input": 3.00,
            "output": 15.00,
            "token_unit": 1_000_000,
        },
    },
    "anthropic.claude-3-haiku-20240307-v1:0": {
        "us-east-1": {
            "region": "US East (N. Virginia)",
            "input": 0.25,
            "output": 1.25,
            "token_unit": 1_000_000,
        },
        "us-west-2": {
            "region": "US West (Oregon)",
            "input": 0.25,
            "output": 1.25,
            "token_unit": 1_000_000,
        },
    },
    # ── Amazon Nova ───────────────────────────────────────────────────────────
    "amazon.nova-2-lite-v1:0": {
        "us-east-1": {
            "region": "US East (N. Virginia)",
            "input": 0.33,
            "output": 2.75,
            "token_unit": 1_000_000,
        },
        "us-west-2": {
            "region": "US West (Oregon)",
            "input": 0.33,
            "output": 2.75,
            "token_unit": 1_000_000,
        },
    },
    "amazon.nova-micro-v1:0": {
        "us-east-1": {
            "region": "US East (N. Virginia)",
            "input": 0.035,
            "output": 0.14,
            "token_unit": 1_000_000,
        },
        "us-west-2": {
            "region": "US West (Oregon)",
            "input": 0.035,
            "output": 0.14,
            "token_unit": 1_000_000,
        },
    },
    "amazon.nova-lite-v1:0": {
        "us-east-1": {
            "region": "US East (N. Virginia)",
            "input": 0.06,
            "output": 0.24,
            "token_unit": 1_000_000,
        },
        "us-west-2": {
            "region": "US West (Oregon)",
            "input": 0.06,
            "output": 0.24,
            "token_unit": 1_000_000,
        },
    },
    "amazon.nova-pro-v1:0": {
        "us-east-1": {
            "region": "US East (N. Virginia)",
            "input": 0.80,
            "output": 3.20,
            "token_unit": 1_000_000,
        },
        "us-west-2": {
            "region": "US West (Oregon)",
            "input": 0.80,
            "output": 3.20,
            "token_unit": 1_000_000,
        },
    },
    "amazon.nova-premier-v1:0": {
        "us-east-1": {
            "region": "US East (N. Virginia)",
            "input": 2.50,
            "output": 12.50,
            "token_unit": 1_000_000,
        },
        "us-west-2": {
            "region": "US West (Oregon)",
            "input": 2.50,
            "output": 12.50,
            "token_unit": 1_000_000,
        },
    },  
    # ── Amazon Titan Embeddings ──────────────────────────────────────────────────────────
    "amazon.titan-embed-text-v1": {
        "us-east-1": {
            "region": "US East (N. Virginia)",
            "input": 0.10,
            "output": 0,
            "token_unit": 1_000_000,
        },
        "us-west-2": {
            "region": "US West (Oregon)",
            "input": 0.10,
            "output": 0,
            "token_unit": 1_000_000,
        },
    },
    "amazon.titan-embed-text-v2:0": {
        "us-east-1": {
            "region": "US East (N. Virginia)",
            "input": 0.02,
            "output": 0,
            "token_unit": 1_000_000,
        },
        "us-west-2": {
            "region": "US West (Oregon)",
            "input": 0.02,
            "output": 0,
            "token_unit": 1_000_000,
        },
    },
    # ── Meta Llama 3 ──────────────────────────────────────────────────────────
    "meta.llama3-8b-instruct-v1:0": {
        "us-east-1": {
            "region": "US East (N. Virginia)",
            "input": 0.30,
            "output": 0.60,
            "token_unit": 1_000_000,
        },
        "us-west-2": {
            "region": "US West (Oregon)",
            "input": 0.30,
            "output": 0.60,
            "token_unit": 1_000_000,
        },
    },
    "meta.llama3-70b-instruct-v1:0": {
        "us-east-1": {
            "region": "US East (N. Virginia)",
            "input": 2.65,
            "output": 3.50,
            "token_unit": 1_000_000,
        },
        "us-west-2": {
            "region": "US West (Oregon)",
            "input": 2.65,
            "output": 3.50,
            "token_unit": 1_000_000,
        },
    },
    # ── Meta Llama 3.1 ────────────────────────────────────────────────────────
    "meta.llama3-1-8b-instruct-v1:0": {
        "us-east-1": {
            "region": "US East (N. Virginia)",
            "input": 0.22,
            "output": 0.22,
            "token_unit": 1_000_000,
        },
        "us-west-2": {
            "region": "US West (Oregon)",
            "input": 0.22,
            "output": 0.22,
            "token_unit": 1_000_000,
        },
    },
    "meta.llama3-1-70b-instruct-v1:0": {
        "us-east-1": {
            "region": "US East (N. Virginia)",
            "input": 0.72,
            "output": 0.72,
            "token_unit": 1_000_000,
        },
        "us-west-2": {
            "region": "US West (Oregon)",
            "input": 0.72,
            "output": 0.72,
            "token_unit": 1_000_000,
        },
    },
    "meta.llama3-1-405b-instruct-v1:0": {
        "us-east-1": {
            "region": "US East (N. Virginia)",
            "input": 2.40,
            "output": 2.40,
            "token_unit": 1_000_000,
        },
        "us-west-2": {
            "region": "US West (Oregon)",
            "input": 2.40,
            "output": 2.40,
            "token_unit": 1_000_000,
        },
    },
    # ── Meta Llama 3.2 ────────────────────────────────────────────────────────
    "meta.llama3-2-1b-instruct-v1:0": {
        "us-east-1": {
            "region": "US East (N. Virginia)",
            "input": 0.10,
            "output": 0.10,
            "token_unit": 1_000_000,
        },
        "us-west-2": {
            "region": "US West (Oregon)",
            "input": 0.10,
            "output": 0.10,
            "token_unit": 1_000_000,
        },
    },
    "meta.llama3-2-3b-instruct-v1:0": {
        "us-east-1": {
            "region": "US East (N. Virginia)",
            "input": 0.15,
            "output": 0.15,
            "token_unit": 1_000_000,
        },
        "us-west-2": {
            "region": "US West (Oregon)",
            "input": 0.15,
            "output": 0.15,
            "token_unit": 1_000_000,
        },
    },
    "meta.llama3-2-11b-instruct-v1:0": {
        "us-east-1": {
            "region": "US East (N. Virginia)",
            "input": 0.16,
            "output": 0.16,
            "token_unit": 1_000_000,
        },
        "us-west-2": {
            "region": "US West (Oregon)",
            "input": 0.16,
            "output": 0.16,
            "token_unit": 1_000_000,
        },
    },
    "meta.llama3-2-90b-instruct-v1:0": {
        "us-east-1": {
            "region": "US East (N. Virginia)",
            "input": 0.72,
            "output": 0.72,
            "token_unit": 1_000_000,
        },
        "us-west-2": {
            "region": "US West (Oregon)",
            "input": 0.72,
            "output": 0.72,
            "token_unit": 1_000_000,
        },
    },
    # ── Meta Llama 3.3 ────────────────────────────────────────────────────────
    "meta.llama3-3-70b-instruct-v1:0": {
        "us-east-1": {
            "region": "US East (N. Virginia)",
            "input": 0.72,
            "output": 0.72,
            "token_unit": 1_000_000,
        },
        "us-west-2": {
            "region": "US West (Oregon)",
            "input": 0.72,
            "output": 0.72,
            "token_unit": 1_000_000,
        },
    },
    # ── Meta Llama 4 ──────────────────────────────────────────────────────────
    "meta.llama4-scout-17b-instruct-v1:0": {
        "us-east-1": {
            "region": "US East (N. Virginia)",
            "input": 0.17,
            "output": 0.17,
            "token_unit": 1_000_000,
        },
        "us-west-2": {
            "region": "US West (Oregon)",
            "input": 0.17,
            "output": 0.17,
            "token_unit": 1_000_000,
        },
    },
    "meta.llama4-maverick-17b-instruct-v1:0": {
        "us-east-1": {
            "region": "US East (N. Virginia)",
            "input": 0.24,
            "output": 0.97,
            "token_unit": 1_000_000,
        },
        "us-west-2": {
            "region": "US West (Oregon)",
            "input": 0.24,
            "output": 0.97,
            "token_unit": 1_000_000,
        },
    },
    # ── DeepSeek ──────────────────────────────────────────────────────────────
    "deepseek.r1-v1:0": {
        "us-east-1": {
            "region": "US East (N. Virginia)",
            "input": 1.35,
            "output": 5.40,
            "token_unit": 1_000_000,
        },
        "us-west-2": {
            "region": "US West (Oregon)",
            "input": 1.35,
            "output": 5.40,
            "token_unit": 1_000_000,
        },
    },
    "deepseek.v3.2": {
        "us-east-1": {
            "region": "US East (N. Virginia)",
            "input": 0.62,
            "output": 1.85,
            "token_unit": 1_000_000,
        },
        "us-west-2": {
            "region": "US West (Oregon)",
            "input": 0.62,
            "output": 1.85,
            "token_unit": 1_000_000,
        },
    },
}
