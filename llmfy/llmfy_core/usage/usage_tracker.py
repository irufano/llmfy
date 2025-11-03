from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any, Dict, Optional

from llmfy.llmfy_core.usage.llmfy_usage import LLMfyUsage

# Thread-safe storage for token usage per request
LLMFY_USAGE_TRACKER_VAR = ContextVar("LLMFY_USAGE_TRACKER", default=LLMfyUsage())


@contextmanager
def llmfy_usage_tracker(
    openai_pricing: Optional[Dict[str, Any]] = None,
    bedrock_pricing: Optional[Dict[str, Any]] = None,
):
    """LLMfy usage tracker.

    Use this to track token usage all provider.

    Example:
    ```python
    with llmfy_usage_tracker() as usage:
            result = llm.generate(messages)
            ...
            print(usage)
    ```

    [OPENAI] Price per 1M tokens for different models (USD):
        - https://platform.openai.com/docs/pricing

    [BEDROCK] Price per 1K tokens for different models (USD):
        - https://aws.amazon.com/bedrock/pricing/
        - https://aws.amazon.com/bedrock/pricing/
        - https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/Concepts.RegionsAndAvailabilityZones.html

    Args:
        openai_pricing (Optional[Dict[str, Any]], optional): OpenAI Pricing dictionary source. Defaults to None.
            If None then use default pricing from this dependency.

            Example pricing structure:
            ```
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

        bedrock_pricing (Optional[Dict[str, Any]], optional): Bedrock Pricing dictionary source. Defaults to None.
            If None then use default pricing from this dependency.

            Example pricing structure:
            ```
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

    Yields:
            OpenAIUsage: OpenAI usage accumulation.
    """

    usage_tracker = LLMfyUsage(
        openai_pricing=openai_pricing,
        bedrock_pricing=bedrock_pricing,
    )
    LLMFY_USAGE_TRACKER_VAR.set(usage_tracker)  # Store usage_tracker it in the context
    try:
        yield usage_tracker  # Expose tracker to the context
    finally:
        pass
