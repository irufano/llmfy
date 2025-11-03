import functools
import itertools

from llmfy.llmfy_core.service_provider import ServiceProvider
from llmfy.llmfy_core.service_type import ServiceType
from llmfy.llmfy_core.usage.usage_tracker import LLMFY_USAGE_TRACKER_VAR


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
                provider=ServiceProvider.OPENAI,
                type=ServiceType.LLM,
                model=model,
                usage=usage,
            )
        return response

    return wrapper


def track_openai_stream_usage(func):
    """Decorator to wrap `__call_stream_openai` calls on `OpenAIModel`."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        stream_origin = func(*args, **kwargs)
        # args is tuple[params] and params contain `model`
        model = args[0]["model"]

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
            usage_tracker = LLMFY_USAGE_TRACKER_VAR.get()
            usage_tracker.update(
                provider=ServiceProvider.OPENAI,
                type=ServiceType.LLM,
                model=model,
                usage=stream_usage,
            )
        return stream_origin

    return wrapper


def track_openai_embedding_usage(func):
    """Decorator to wrap `__call_openai_embedding` calls on `OpenAIEmbedding`."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        response = func(*args, **kwargs)
        model = args[0]
        # Extract token usage
        # input_tokens = response.usage.prompt_tokens if response.usage else 0
        # Usage(prompt_tokens=8, total_tokens=8)
        usage = {
            "prompt_tokens": response.usage.prompt_tokens or 0,
            "total_tokens": response.usage.total_tokens or 0,
        }
        print(usage)
        usage_tracker = LLMFY_USAGE_TRACKER_VAR.get()
        usage_tracker.update(
            provider=ServiceProvider.OPENAI,
            type=ServiceType.EMBEDDING,
            model=model,
            usage=usage,
        )

        return response

    return wrapper
