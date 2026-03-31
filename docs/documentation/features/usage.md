# Usage

LLMfy has a built-in usage tracker. Usage tracker is used to track token usage, request and cost. You can use `llmfy_usage_tracker` that imported from:

```python
from llmfy import llmfy_usage_tracker
```

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
        price_per_tokens: 1000000 
        total_cost (USD): 1.08e-05 
        total_cost (USD formatted): 0.0000108

2. gpt-4o-mini 
        provider: OPENAI 
        input_tokens: 107 
        output_tokens: 3 
        total_tokens: 110 
        input_price: 0.15 
        output_price: 0.6 
        price_per_tokens: 1000000 
        total_cost (USD): 1.785e-05 
        total_cost (USD formatted): 0.00001785

------------------
```

## Customize Prices Data
If the model is not found in the lmfy usage tracker, you can customize the model price source list based on the provider.

### OpenAI
OpenAI Pricing dictionary source. 

Example pricing structure:
```json linenums="1"
{
    "gpt-4o": {
        "input": 2.50,
        "output": 10.00
    },
    "gpt-4o-mini": {
        "input": 0.15,
        "output": 0.60
    },
    "gpt-3.5-turbo": {
        "input": 0.05,
        "output": 1.50
    }
}
```

### Bedrock
Bedrock Pricing dictionary source.

Example pricing structure:
```json linenums="1"
{
    "anthropic.claude-3-5-sonnet-20240620-v1:0": {
        "us-east-1": {
            "region": "US East (N. Virginia)",
            "input": 0.003,
            "output": 0.015,
        },
        "us-west-2": {
            "region": "US West (Oregon)",
            "input": 0.003,
            "output": 0.015,
        },
    },
    "anthropic.claude-3-5-sonnet-20241022-v2:0": {
        "us-east-1": {
            "region": "US East (N. Virginia)",
            "input": 0.003,
            "output": 0.015,
        },
        "us-west-2": {
            "region": "US West (Oregon)",
            "input": 0.003,
            "output": 0.015,
        },
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
    }
}
```

### Example

```python linenums="1"
openai_prices = {
    "gpt-4o": {
        "input": 2.50,
        "output": 10.00
    },
    "gpt-4o-mini": {
        "input": 0.15,
        "output": 0.60
    },
    "gpt-3.5-turbo": {
        "input": 0.05,
        "output": 1.50
    }
}

bedrock_prices = {
    "anthropic.claude-3-5-sonnet-20240620-v1:0": {
        "us-east-1": {
            "region": "US East (N. Virginia)",
            "input": 0.003,
            "output": 0.015,
        },
        "us-west-2": {
            "region": "US West (Oregon)",
            "input": 0.003,
            "output": 0.015,
        },
    },
    "anthropic.claude-3-5-sonnet-20241022-v2:0": {
        "us-east-1": {
            "region": "US East (N. Virginia)",
            "input": 0.003,
            "output": 0.015,
        },
        "us-west-2": {
            "region": "US West (Oregon)",
            "input": 0.003,
            "output": 0.015,
        },
    }
}

googleai_prices = {
    "gemini-2.0-flash": {
        "input": 0.10,
        "output": 0.40,
    },
    "gemini-2.5-pro": {
        "input": 1.25,
        "input_high": 2.50,
        "output": 10.00,
        "output_high": 15.00,
        "threshold": 200000,
    }
}

with llmfy_usage_tracker(
    openai_pricing=openai_prices,
    bedrock_pricing=bedrock_prices,
    googleai_pricing=googleai_prices,
) as usage:
    # invoke llmfy
```