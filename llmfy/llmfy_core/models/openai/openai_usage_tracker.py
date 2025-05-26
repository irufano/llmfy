from contextlib import contextmanager
from contextvars import ContextVar
import functools
from typing import Any, Dict, Optional

from llmfy.llmfy_core.models.openai.openai_usage import OpenAIUsage
from llmfy.llmfy_core.tools.deprecated import deprecated


# Thread-safe storage for token usage per request
OPENAI_USAGE_TRACKER_VAR = ContextVar("OPENAI_USAGE_TRACKER", default=OpenAIUsage())


@deprecated(
    reason="inefficient algorithm",
    version="0.2.1",
    alternative="llmfy_usage_tracker()",
)
@contextmanager
def openai_usage_tracker(pricing: Optional[Dict[str, Any]] = None):
    """
    OpenAI usage tracker.

    @deprecated Use llmfy_usage_tracker() instead.

    Use this to track token usage on openai.

    Example:
    ```python
    with openai_usage_tracker() as usage:
            result = llm.generate(messages)
            ...
            print(usage)
    ```

    Args:
        pricing (Optional[Dict[str, Any]], optional): Pricing dictionary source. Defaults to None.
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

    Yields:
            OpenAIUsage: OpenAI usage accumulation.
    """
    usage_tracker = OpenAIUsage(pricing=pricing)
    OPENAI_USAGE_TRACKER_VAR.set(usage_tracker)  # Store usage_tracker it in the context
    try:
        yield usage_tracker  # Expose tracker to the context
    finally:
        print("")


def track_openai_usage(func):
    """Decorator to wrap `__call_openai` calls on `OpenAIModel`."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        response = func(*args, **kwargs)
        model = args[1][
            "model"
        ]  # args is tuple[OpenAIModel, params] and params contain `model`
        if response.usage:
            usage = response.usage
            usage_tracker = OPENAI_USAGE_TRACKER_VAR.get()
            usage_tracker.update(model=model, usage=usage)
        return response

    return wrapper
