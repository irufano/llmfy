import functools
import inspect
import itertools

from llmfy.llmfy_core.model_backend import ModelBackend
from llmfy.llmfy_core.service_provider import ServiceProvider
from llmfy.llmfy_core.service_type import ServiceType
from llmfy.llmfy_core.usage.usage_tracker import LLMFY_USAGE_TRACKER_VAR


def _report_openai_usage(args, response) -> None:
    usage_tracker = LLMFY_USAGE_TRACKER_VAR.get()
    if usage_tracker is None or not response.usage:
        return
    model = args[0]["model"]  # args is tuple[params, ...] and params contain `model`
    usage_tracker.update(
        backend=ModelBackend.OPENAI_CHAT,
        type=ServiceType.LLM,
        model=model,
        usage=response.usage,
    )


def track_openai_usage(func):
    """Decorator to wrap `__call_openai`/`__call_openai_async` calls on
    `OpenAIChatModel`. Works on both a sync and an async `func` (checked via
    `asyncio.iscoroutinefunction`) so the same decorator covers `generate`
    and `agenerate`.

    Passes the raw CompletionUsage object from the API response directly to the
    usage tracker. The object contains:
      - prompt_tokens:           total input tokens (includes cached tokens)
      - completion_tokens:       output tokens
      - prompt_tokens_details.cached_tokens:
                                 tokens served from OpenAI's automatic cache
                                 (present when prefix > 1,024 tokens and a cache
                                 hit occurs; extracted as cache_read_tokens in
                                 llmfy_usage.py)

    OpenAI caches automatically — no markers needed. Caching has no additional
    fee; savings are reflected in the effective per-token cost on cache hits.

    Reference: https://platform.openai.com/docs/guides/prompt-caching
    """
    if inspect.iscoroutinefunction(func):

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            response = await func(*args, **kwargs)
            _report_openai_usage(args, response)
            return response

        return async_wrapper

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        response = func(*args, **kwargs)
        _report_openai_usage(args, response)
        return response

    return wrapper


def track_openai_stream_usage(func):
    """Decorator to wrap `__call_stream_openai` calls on `OpenAIChatModel`.

    Tees the stream (enabled by stream_options={"include_usage": True}) to
    extract the final chunk's CompletionUsage without consuming the stream.
    Carries the same prompt_tokens_details.cached_tokens field as the non-stream
    response when a prompt cache hit occurs.

    Reference: https://platform.openai.com/docs/guides/prompt-caching
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        stream_origin = func(*args, **kwargs)
        usage_tracker = LLMFY_USAGE_TRACKER_VAR.get()
        if usage_tracker is None:
            return stream_origin
        # args is tuple[params] and params contain `model`
        model = args[0]["model"]

        stream_usage = None

        if stream_origin:
            stream, stream_copy = itertools.tee(
                stream_origin
            )  # Duplicate the generator
            stream_origin = stream  # Replace original stream

            for chunk in stream_copy:  # Iterate over the copy
                if chunk.usage:
                    stream_usage = chunk.usage
                    break  # No need to iterate further

        if stream_usage:
            usage_tracker.update(
                backend=ModelBackend.OPENAI_CHAT,
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
        usage_tracker = LLMFY_USAGE_TRACKER_VAR.get()
        if usage_tracker is None:
            return response
        model = args[0]
        usage = {
            "prompt_tokens": response.usage.prompt_tokens or 0,
            "total_tokens": response.usage.total_tokens or 0,
        }
        usage_tracker.update(
            provider=ServiceProvider.OPENAI,
            type=ServiceType.EMBEDDING,
            model=model,
            usage=usage,
        )
        return response

    return wrapper
