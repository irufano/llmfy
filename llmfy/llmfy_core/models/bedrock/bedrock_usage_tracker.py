import functools
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any, Dict, Optional

from llmfy.llmfy_core.models.bedrock.bedrock_usage import BedrockUsage
from llmfy.llmfy_core.tools.deprecated import deprecated


# Thread-safe storage for token usage per request
BEDROCK_USAGE_TRACKER_VAR = ContextVar("BEDROCK_USAGE_TRACKER", default=BedrockUsage())


@deprecated(
    reason="inefficient algorithm",
    version="0.2.1",
    alternative="llmfy_usage_tracker()",
)
@contextmanager
def bedrock_usage_tracker(pricing: Optional[Dict[str, Any]] = None):
    """
    Bedrock usage tracker.

    @deprecated Use llmfy_usage_tracker() instead.

    Use this to track token usage on bedrock.

    Example:
    ```python
    with bedrock_usage_tracker() as usage:
            result = chat.generate(messages)
            ...
            print(usage)
    ```

    Args:
        pricing (Optional[Dict[str, Any]], optional): Pricing dictionary source. Defaults to None.
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
        BedrockUsage: Bedrock usage accumulation.
    """
    usage_tracker = BedrockUsage(pricing=pricing)
    BEDROCK_USAGE_TRACKER_VAR.set(
        usage_tracker
    )  # Store usage_tracker it in the context
    try:
        yield usage_tracker  # Expose tracker to the context
    finally:
        print("")


def track_bedrock_usage(func):
    """Decorator to wrap `__call_bedrock` calls on `BedrockModel`."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        response = func(*args, **kwargs)
        model = args[1][
            "modelId"
        ]  # args is tuple[BedrockModel, params] and params contain `modelId`
        if response["usage"]:
            usage = response["usage"]
            usage_tracker = BEDROCK_USAGE_TRACKER_VAR.get()
            usage_tracker.update(model=model, usage=usage)
        return response

    return wrapper
