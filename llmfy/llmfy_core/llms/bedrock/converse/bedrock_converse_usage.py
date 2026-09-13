import functools
import inspect
import itertools

from llmfy.llmfy_core.model_backend import ModelBackend
from llmfy.llmfy_core.service_provider import ServiceProvider
from llmfy.llmfy_core.service_type import ServiceType
from llmfy.llmfy_core.usage.usage_tracker import LLMFY_USAGE_TRACKER_VAR


def _report_bedrock_converse_usage(args, response) -> None:
    usage_tracker = LLMFY_USAGE_TRACKER_VAR.get()
    if usage_tracker is None or not response["usage"]:
        return
    model = args[0]["modelId"]  # args is tuple[params, ...] and params contain `modelId`
    usage_tracker.update(
        backend=ModelBackend.BEDROCK_CONVERSE,
        type=ServiceType.LLM,
        model=model,
        usage=response["usage"],
    )


def track_bedrock_converse_usage(func):
    """Decorator to wrap `__call_bedrock`/`__call_bedrock_async` calls on
    `BedrockConverseModel`. Works on both a sync and an async `func` (checked
    via `asyncio.iscoroutinefunction`) so the same decorator covers
    `generate` and `agenerate`.

    Extracts the `usage` dict from the Converse API response and forwards it
    to the usage tracker. The dict contains:
      - inputTokens:             total input tokens (includes cache-read tokens)
      - outputTokens:            total output tokens
      - cacheReadInputTokens:    tokens served from cache (~10% input price)
                                 present only when prompt_caching.enabled=True
      - cacheWriteInputTokens:   tokens written to cache (~125% input price)
                                 present only when prompt_caching.enabled=True

    Reference: https://docs.aws.amazon.com/bedrock/latest/userguide/prompt-caching.html
    """
    if inspect.iscoroutinefunction(func):

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            response = await func(*args, **kwargs)
            _report_bedrock_converse_usage(args, response)
            return response

        return async_wrapper

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        response = func(*args, **kwargs)
        _report_bedrock_converse_usage(args, response)
        return response

    return wrapper


def track_bedrock_converse_stream_usage(func):
    """Decorator to wrap `__call_stream_bedrock` calls on `BedrockConverseModel`.

    Tees the event stream to extract the `metadata.usage` dict without
    consuming it. The usage dict contains the same fields as the non-stream
    response: inputTokens, outputTokens, and — when prompt_caching.enabled=True
    on supported Claude models — cacheReadInputTokens and cacheWriteInputTokens.

    Reference: https://docs.aws.amazon.com/bedrock/latest/userguide/prompt-caching.html
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        response = func(*args, **kwargs)
        usage_tracker = LLMFY_USAGE_TRACKER_VAR.get()
        if usage_tracker is None:
            return response
        # args is tuple[params] and params contain `modelId`
        model = args[0]["modelId"]
        stream = response.get("stream")
        stream_usage = None

        if stream:
            stream, stream_copy = itertools.tee(stream)  # Duplicate the generator
            response["stream"] = stream  # Replace original stream

            for event in stream_copy:  # Iterate over the copy
                if "metadata" in event:
                    metadata = event["metadata"]
                    if "usage" in metadata:
                        stream_usage = metadata["usage"]
                        break  # No need to iterate further

        if stream_usage:
            usage_tracker.update(
                backend=ModelBackend.BEDROCK_CONVERSE,
                type=ServiceType.LLM,
                model=model,
                usage=stream_usage,
            )

        return response

    return wrapper


def track_bedrock_converse_stream_usage_async(func):
    """Async-generator counterpart of `track_bedrock_converse_stream_usage`.

    `itertools.tee` (used by the sync decorator to duplicate the stream
    without consuming it) has no equivalent for async iterators in the
    stdlib, and aioboto3's stream must be consumed while its underlying
    client connection is still open — so `func` here is an async-generator
    function that yields raw Converse-stream events directly (not a response
    dict with a "stream" key, unlike the sync path), and this wraps it in a
    single pass: forward each event immediately, and report usage the moment
    the event carrying `metadata.usage` is seen.
    """

    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        usage_tracker = LLMFY_USAGE_TRACKER_VAR.get()
        model = args[0]["modelId"]  # args is tuple[params, ...] and params contain `modelId`
        # Sync version stops at the first usage-bearing event found (`break`
        # after tee-scanning) — this flag preserves "report at most once"
        # here too, in case more than one event ever carries metadata.usage.
        reported = False

        async for event in func(*args, **kwargs):
            if not reported and usage_tracker is not None and "metadata" in event:
                usage = event["metadata"].get("usage")
                if usage:
                    usage_tracker.update(
                        backend=ModelBackend.BEDROCK_CONVERSE,
                        type=ServiceType.LLM,
                        model=model,
                        usage=usage,
                    )
                    reported = True
            yield event

    return wrapper


def track_bedrock_embedding_usage(func):
    """Decorator to wrap `__call_bedrock_embedding` calls on `BedrockEmbedding`."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        response = func(*args, **kwargs)
        usage_tracker = LLMFY_USAGE_TRACKER_VAR.get()
        if usage_tracker is None:
            return response
        model = args[0]
        # Extract token usage from headers
        headers = response.get("ResponseMetadata", {}).get("HTTPHeaders", {})
        input_tokens = int(headers.get("x-amzn-bedrock-input-token-count", 0))
        usage = {"x-amzn-bedrock-input-token-count": input_tokens}
        usage_tracker.update(
            provider=ServiceProvider.BEDROCK,
            type=ServiceType.EMBEDDING,
            model=model,
            usage=usage,
        )
        return response

    return wrapper
