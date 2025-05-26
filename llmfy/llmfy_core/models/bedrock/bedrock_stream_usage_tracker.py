from contextlib import contextmanager
from contextvars import ContextVar
import functools
import itertools

from llmfy.llmfy_core.models.bedrock.bedrock_usage import BedrockUsage

# Thread-safe storage for token usage per request
BEDROCK_STREAM_USAGE_TRACKER_VAR = ContextVar(
    "BEDROCK_STREAM_USAGE_TRACKER", default=BedrockUsage()
)


@contextmanager
def bedrock_stream_usage_tracker():
    """Bedrock stream usage tracker.

    Use this to track token usage on bedrock stream.

    Example:
    ```python
    with bedrock_usage_tracker() as usage:
            result = chat.generate(messages)
            ...
            print(usage)
    ```

    Yields:
            BedrockUsage: Bedrock usage accumulation.
    """
    usage_tracker = BedrockUsage()
    BEDROCK_STREAM_USAGE_TRACKER_VAR.set(
        usage_tracker
    )  # Store usage_tracker it in the context
    try:
        yield usage_tracker  # Expose tracker to the context
    finally:
        print("")


def track_bedrock_stream_usage(func):
    """Decorator to wrap `__call_bedrock` calls on `BedrockModel`."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        response = func(*args, **kwargs)
        # args is tuple[BedrockModel, params] and params contain `modelId`
        model = args[1]["modelId"]
        stream = response.get("stream")
        stream_usage = None

        if stream:
            stream, stream_copy = itertools.tee(stream)  # Duplicate the generator
            response["stream"] = stream  # Replace original stream

            stream_usage = None
            for event in stream_copy:  # Iterate over the copy
                if "metadata" in event:
                    metadata = event["metadata"]
                    if "usage" in metadata:
                        stream_usage = metadata["usage"]
                        break  # No need to iterate further

        if stream_usage:
            usage_tracker = BEDROCK_STREAM_USAGE_TRACKER_VAR.get()
            usage_tracker.update(model=model, usage=stream_usage)

        return response

    return wrapper
