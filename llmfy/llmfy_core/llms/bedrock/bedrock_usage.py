import functools
import itertools

from llmfy.llmfy_core.service_provider import ServiceProvider
from llmfy.llmfy_core.service_type import ServiceType
from llmfy.llmfy_core.usage.usage_tracker import LLMFY_USAGE_TRACKER_VAR


def track_bedrock_usage(func):
    """Decorator to wrap `__call_bedrock` calls on `BedrockModel`.

    Extracts the `usage` dict from the Converse API response and forwards it
    to the usage tracker. The dict contains:
      - inputTokens:             total input tokens (includes cache-read tokens)
      - outputTokens:            total output tokens
      - cacheReadInputTokens:    tokens served from cache (~10% input price)
                                 present only when enable_prompt_caching=True
      - cacheWriteInputTokens:   tokens written to cache (~125% input price)
                                 present only when enable_prompt_caching=True

    Reference: https://docs.aws.amazon.com/bedrock/latest/userguide/prompt-caching.html
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        response = func(*args, **kwargs)
        usage_tracker = LLMFY_USAGE_TRACKER_VAR.get()
        if usage_tracker is None:
            return response
        model = args[0][
            "modelId"
        ]  # args is tuple[BedrockModel, params] and params contain `modelId`
        if response["usage"]:
            usage_tracker.update(
                provider=ServiceProvider.BEDROCK,
                type=ServiceType.LLM,
                model=model,
                usage=response["usage"],
            )
        return response

    return wrapper


def track_bedrock_stream_usage(func):
    """Decorator to wrap `__call_stream_bedrock` calls on `BedrockModel`.

    Tees the event stream to extract the `metadata.usage` dict without
    consuming it. The usage dict contains the same fields as the non-stream
    response: inputTokens, outputTokens, and — when enable_prompt_caching=True
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
                provider=ServiceProvider.BEDROCK,
                type=ServiceType.LLM,
                model=model,
                usage=stream_usage,
            )

        return response

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
