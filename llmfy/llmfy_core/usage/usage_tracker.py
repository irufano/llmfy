from contextlib import contextmanager
from contextvars import ContextVar
import functools
from typing import Any, Dict, Optional

from llmfy.llmfy_core.models.model_provider import ModelProvider
from llmfy.llmfy_core.usage.llmfy_usage import LLMfyUsage

# Thread-safe storage for token usage per request
LLMFY_USAGE_TRACKER_VAR = ContextVar("LLMFY_USAGE_TRACKER", default=LLMfyUsage())


@contextmanager
def llmfy_usage_tracker(
    openai_pricing: Optional[Dict[str, Any]] = None,
    bedrock_pricing: Optional[Dict[str, Any]] = None,
):
    """OpenAI usage tracker.

    Use this to track token usage all provider.

    Example:
    ```python
    with usage_tracker() as usage:
            result = llm.generate(messages)
            ...
            print(usage)
    ```

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


def track_openai_usage(func):
    """Decorator to wrap `__call_openai` calls on `OpenAIModel`."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        response = func(*args, **kwargs)
        model = args[0][
            "model"
        ]  # args is tuple[OpenAIModel, params] and params contain `model`
        if response.usage:
            usage = response.usage
            usage_tracker = LLMFY_USAGE_TRACKER_VAR.get()
            usage_tracker.update(
                provider=ModelProvider.OPENAI,
                model=model,
                usage=usage,
            )
        return response

    return wrapper


def track_bedrock_usage(func):
    """Decorator to wrap `__call_bedrock` calls on `BedrockModel`."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        response = func(*args, **kwargs)
        model = args[0][
            "modelId"
        ]  # args is tuple[BedrockModel, params] and params contain `modelId`
        if response["usage"]:
            usage = response["usage"]
            usage_tracker = LLMFY_USAGE_TRACKER_VAR.get()
            usage_tracker.update(
                provider=ModelProvider.BEDROCK,
                model=model,
                usage=usage,
            )
        return response

    return wrapper
