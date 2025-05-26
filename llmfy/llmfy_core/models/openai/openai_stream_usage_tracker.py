from contextlib import contextmanager
from contextvars import ContextVar
import functools
import itertools
from typing import Any, Dict, Optional

from llmfy.llmfy_core.models.openai.openai_usage import OpenAIUsage

# Thread-safe storage for token usage per request
OPENAI_STREAM_USAGE_TRACKER_VAR = ContextVar(
    "OPENAI_STREAM_USAGE_TRACKER", default=OpenAIUsage()
)


@contextmanager
def openai_stream_usage_tracker(pricing: Optional[Dict[str, Any]] = None):
    """OpenAI usage tracker.

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
    OPENAI_STREAM_USAGE_TRACKER_VAR.set(
        usage_tracker
    )  # Store usage_tracker it in the context
    try:
        yield usage_tracker  # Expose tracker to the context
    finally:
        pass


def track_openai_stream_usage(func):
    """Decorator to wrap `__call_stream_openai` calls on `OpenAIModel`."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        stream_origin = func(*args, **kwargs)
        model = args[1]["model"]
        # args is tuple[OpenAIModel, params] and params contain `model`

        stream_usage = None

        if stream_origin:
            stream, stream_copy = itertools.tee(
                stream_origin
            )  # Duplicate the generator
            stream_origin = stream  # Replace original stream

            stream_usage = None
            for chunk in stream_copy:  # Iterate over the copy
                if chunk.usage:
                    stream_usage = chunk.usage
                    break  # No need to iterate further

        if stream_usage:
            usage_tracker = OPENAI_STREAM_USAGE_TRACKER_VAR.get()
            usage_tracker.update(model=model, usage=stream_usage)
        return stream_origin

    return wrapper
