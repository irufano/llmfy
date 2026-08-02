# Usage

LLMfy has a built-in usage tracker. Usage tracker is used to track token usage, request and cost. You can use `llmfy_usage_tracker` that imported from:

---

## Use as context manager

`llmfy_usage_tracker` can be used to all supported providers on llmfy.

```python linenums="1"
with llmfy_usage_tracker() as usage:
    # Use chat or invoke
    # (chat use messages)
    response_a = agent.chat(messages, info=info)
    # (invoke use contents)
    response_b = agent.invoke(contents, info=info)

print(f"\n>> {response_a.result.content}\n")
print(f"\n>> {response_b.result.content}\n")
print(f"Usage:\n{usage}\n")
```

The output should be like this:

```shell
>> Maaf.


>> Maaf.

Usage:

------------------
USAGE: 

Total Tokens: 173
        Input Tokens: 167
        Output Tokens: 6
Total Requests: 2
Total Cost (USD): $2.865e-05
Total Cost (USD formatted): $0.00002865

Request Details:
1. gpt-4o-mini 
        provider: OPENAI 
        input_tokens: 60 
        output_tokens: 3 
        total_tokens: 63 
        input_price: 0.15 
        output_price: 0.6 
        token_unit: 1000000 
        total_cost (USD): 1.08e-05 
        total_cost (USD formatted): 0.0000108

2. gpt-4o-mini 
        provider: OPENAI 
        input_tokens: 107 
        output_tokens: 3 
        total_tokens: 110 
        input_price: 0.15 
        output_price: 0.6 
        token_unit: 1000000 
        total_cost (USD): 1.785e-05 
        total_cost (USD formatted): 0.00001785

------------------
```

## Customize Prices Data
If the model is not found in the lmfy usage tracker, you can customize the model price source list based on the provider.

### Anthropic
Anthropic (native Messages API) Pricing dictionary source. Flat structure, like OpenAI's — native Anthropic pricing has no region dimension, unlike Bedrock.

Example pricing structure:
```json linenums="1"
{
    "claude-sonnet-5": {
        "input": 3.30,
        "output": 16.50,
        "token_unit": 1000000
    },
    "claude-opus-5": {
        "input": 5.50,
        "output": 27.50,
        "token_unit": 1000000
    },
    "claude-haiku-4-5": {
        "input": 1.10,
        "output": 5.50,
        "token_unit": 1000000
    }
}
```

!!! info "Optional `cache_read` / `cache_write` fields"
    Add `cache_read` and/or `cache_write` to a model entry to set its **explicit** per-token cache price (same unit as `input`/`output`, not a ratio). If omitted, llmfy falls back to the default ratio — 10% of input for cache reads, 125% of input for cache writes (5-minute TTL) — the same defaults used by Bedrock's Claude pricing. The 1-hour cache TTL uses a ~200% write premium instead of ~125%; set `cache_write` explicitly if you need that modeled precisely, since `ModelPricing` has no TTL dimension to distinguish the two automatically.

    ```json linenums="1"
    {
        "claude-sonnet-5": {
            "input": 3.30,
            "output": 16.50,
            "cache_read": 0.33,
            "cache_write": 6.60,
            "token_unit": 1000000
        }
    }
    ```

### OpenAI
OpenAI Pricing dictionary source. 

Example pricing structure:
```json linenums="1"
{
    "gpt-4o": {
        "input": 2.50,
        "output": 10.00,
        "token_unit": 1000000
    },
    "gpt-4o-mini": {
        "input": 0.15,
        "output": 0.60,
        "token_unit": 1000000
    },
    "gpt-3.5-turbo": {
        "input": 0.50,
        "output": 1.50,
        "token_unit": 1000000
    }
}
```

!!! info "Optional `cache_read` / `cache_write` fields"
    Add `cache_read` and/or `cache_write` to a model entry to set its **explicit** per-token cache price (same unit as `input`/`output`, not a ratio). This matters because the cache-read discount is not the same across generations — 50% of input for `gpt-4o`/`gpt-4.1`/o-series vs. 10% for the GPT-5.6 family, which also bills cache writes at 125% of input (reported in `cache_write_tokens`). If a model entry omits these fields, llmfy falls back to the 50%-read / no-write-fee default, so existing custom pricing dicts keep working unchanged.

    ```json linenums="1"
    {
        "gpt-5.6-sol": {
            "input": 5.00,
            "output": 30.00,
            "cache_read": 0.50,
            "cache_write": 6.25,
            "token_unit": 1000000
        },
        "gpt-4o": {
            "input": 2.50,
            "output": 10.00,
            "cache_read": 1.25,
            "token_unit": 1000000
        }
    }
    ```

### Bedrock
Bedrock Pricing dictionary source.

!!! note "Exact model ID matching"
    The model ID key must exactly match the model ID passed to the API.
    Default base model IDs use the format `provider.model-name`
    (e.g. `anthropic.claude-sonnet-4-6`).

    If you use **cross-region inference profile IDs**
    (e.g. `us.anthropic.claude-sonnet-4-6`, `eu.anthropic.claude-sonnet-4-6`),
    you must add those prefixed IDs as separate entries in the custom pricing dict.
    Built-in pricing only covers base model IDs and applies to both
    **Geo** and **In-region Cross-region Inference** profiles at the same rate.

Example pricing structure:
```json linenums="1"
{
    "anthropic.claude-3-5-sonnet-20241022-v2:0": {
        "us-east-1": {
            "region": "US East (N. Virginia)",
            "input": 3.00,
            "output": 15.00,
            "token_unit": 1000000
        },
        "us-west-2": {
            "region": "US West (Oregon)",
            "input": 3.00,
            "output": 15.00,
            "token_unit": 1000000
        }
    },
    "us.anthropic.claude-3-5-sonnet-20241022-v2:0": {
        "us-east-1": {
            "region": "US East (N. Virginia)",
            "input": 3.00,
            "output": 15.00,
            "token_unit": 1000000
        },
        "us-west-2": {
            "region": "US West (Oregon)",
            "input": 3.00,
            "output": 15.00,
            "token_unit": 1000000
        }
    }
}
```

!!! info "Optional `cache_read` / `cache_write` fields"
    Add `cache_read` and/or `cache_write` inside a region entry to set its **explicit** per-token cache price (same unit as `input`/`output`, not a ratio). If omitted, llmfy falls back to the default ratio — 10% of input for cache reads, 125% of input for cache writes — which is constant across current Claude models on Bedrock. Only set these explicitly if a model/tier deviates from that default (e.g. the extended 1-hour cache TTL, which uses a 2x write premium instead of 1.25x).

    ```json linenums="1"
    {
        "anthropic.claude-sonnet-4-6": {
            "us-east-1": {
                "region": "US East (N. Virginia)",
                "input": 3.30,
                "output": 16.50,
                "cache_read": 0.33,
                "cache_write": 6.60,
                "token_unit": 1000000
            }
        }
    }
    ```

### Google AI

Google AI supports four pricing structures (all prices are per 1M tokens in USD):

**Flat pricing** — same price for all input types:
```python linenums="1"
{
    "gemini-2.0-flash": {
        "input": 0.10,
        "output": 0.40,
        "token_unit": 1_000_000,
    }
}
```

**Per-type input pricing** — different price per modality:
```python linenums="1"
{
    "gemini-3-flash-preview": {
        "input": {
            "default": 0.50,
            "text": 0.50,
            "image": 0.50,
            "video": 0.50,
            "audio": 1.00,
        },
        "output": 3.00,
        "token_unit": 1_000_000,
    }
}
```

**Tiered pricing** — different price above a token count threshold:
```python linenums="1"
{
    "gemini-2.5-pro": {
        "input": 1.25,        # price when prompt <= threshold
        "input_high": 2.50,   # price when prompt > threshold
        "output": 10.00,
        "output_high": 15.00,
        "threshold": 200000,
        "token_unit": 1_000_000,
    }
}
```

**Tiered + per-type pricing** — combines both tiered and per-modality pricing:
```python linenums="1"
{
    "model-id": {
        "input": {
            "default": 0.25,
            "text": 0.25,
            "image": 0.25,
            "video": 0.25,
            "audio": 0.50,
        },
        "input_high": {
            "default": 0.50,
            "text": 0.50,
            "image": 0.50,
            "video": 0.50,
            "audio": 1.00,
        },
        "output": 1.50,
        "output_high": 3.00,
        "threshold": 200000,
        "token_unit": 1_000_000,
    }
}
```

!!! info "Optional `cache_read` field"
    Add `cache_read` to a model entry to set its **explicit** per-token cache price (same unit as `input`/`output`, not a ratio). If omitted, llmfy falls back to the default 25%-of-input rate (a 75% discount on cached tokens), which is constant across current Gemini models. There is no `cache_write` for Google AI — explicit-cache creation is billed separately as a `CachedContent` storage resource, not as part of a `generateContent` request.

    ```json linenums="1"
    {
        "gemini-2.5-flash": {
            "input": 0.30,
            "output": 2.50,
            "cache_read": 0.075,
            "token_unit": 1_000_000
        }
    }
    ```

### Example

```python linenums="1"
anthropic_prices = {
    "claude-sonnet-5": {
        "input": 3.30,
        "output": 16.50,
        "token_unit": 1_000_000,
    },
    "claude-opus-5": {
        "input": 5.50,
        "output": 27.50,
        "token_unit": 1_000_000,
    },
}

openai_prices = {
    "gpt-4o": {
        "input": 2.50,
        "output": 10.00,
        "token_unit": 1_000_000,
    },
    "gpt-4o-mini": {
        "input": 0.15,
        "output": 0.60,
        "token_unit": 1_000_000,
    },
}

bedrock_prices = {
    # Base model ID
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
    # Cross-region inference profile ID — must be added separately
    "us.anthropic.claude-3-5-sonnet-20241022-v2:0": {
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
}

googleai_prices = {
    "gemini-2.0-flash": {
        "input": 0.10,
        "output": 0.40,
        "token_unit": 1_000_000,
    },
    "gemini-2.5-pro": {
        "input": 1.25,
        "input_high": 2.50,
        "output": 10.00,
        "output_high": 15.00,
        "threshold": 200000,
        "token_unit": 1_000_000,
    },
}

with llmfy_usage_tracker(
    anthropic_pricing=anthropic_prices,
    openai_pricing=openai_prices,
    bedrock_pricing=bedrock_prices,
    googleai_pricing=googleai_prices,
) as usage:
    # invoke llmfy
```


## Breaking Changes

### v0.5.4 → v0.6.0 or Latest


#### Custom pricing — `token_unit` field required

All custom pricing dicts for **all providers** (OpenAI, Bedrock, Google AI) now
require a `token_unit` field in each entry. Previously this field was optional
and defaulted silently inside the pricing model. It is now an explicit required
field to ensure cost calculations are always correct.

**Migration:** add `"token_unit": 1_000_000` to every entry in your custom
pricing dicts.

```python linenums="1"
# Before (v0.5.4) — token_unit not required
openai_prices = {
    "my-custom-model": {
        "input": 5.00,
        "output": 20.00,
    }
}

# After (v0.6.0) — token_unit must be present
openai_prices = {
    "my-custom-model": {
        "input": 5.00,
        "output": 20.00,
        "token_unit": 1_000_000,  # required
    }
}
```

#### Bedrock — exact model ID matching required

The usage tracker previously stripped cross-region inference profile prefixes
(`us.`, `eu.`, `ap.`) before looking up pricing, so a model ID like
`us.anthropic.claude-sonnet-4-6` would automatically resolve to
`anthropic.claude-sonnet-4-6` in the pricing table.

**This automatic stripping has been removed.** The model ID passed to the API is
now used as-is for the pricing lookup. This means:

- **Base model IDs** (e.g. `anthropic.claude-sonnet-4-6`) continue to work with no changes.
- **Cross-region inference profile IDs** (e.g. `us.anthropic.claude-sonnet-4-6`) will no longer find a built-in price and will log a warning instead.

**Migration:** if you use cross-region inference profile IDs, add them as separate
entries in a custom pricing dict and pass it via `llmfy_usage_tracker(bedrock_pricing=prices)`.

```python linenums="1"
# Before (v0.5.4) — worked automatically
with llmfy_usage_tracker() as usage:
    agent.invoke(...)  # model="us.anthropic.claude-sonnet-4-6" resolved fine

# After (v0.6.0) — must supply custom pricing for prefixed IDs
bedrock_prices = {
    "us.anthropic.claude-sonnet-4-6": {
        "us-east-1": {
            "region": "US East (N. Virginia)",
            "input": 3.00,
            "output": 15.00,
            "token_unit": 1_000_000,
        },
    }
}
with llmfy_usage_tracker(bedrock_pricing=bedrock_prices) as usage:
    agent.invoke(...)
```

---

```python
from llmfy import llmfy_usage_tracker
```