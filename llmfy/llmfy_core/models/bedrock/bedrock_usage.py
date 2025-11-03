import functools
import itertools

from llmfy.llmfy_core.service_provider import ServiceProvider
from llmfy.llmfy_core.service_type import ServiceType
from llmfy.llmfy_core.usage.usage_tracker import LLMFY_USAGE_TRACKER_VAR


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
                provider=ServiceProvider.BEDROCK,
                type=ServiceType.LLM,
                model=model,
                usage=usage,
            )
        return response

    return wrapper


def track_bedrock_stream_usage(func):
    """Decorator to wrap `__call_stream_bedrock` calls on `BedrockModel`."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        response = func(*args, **kwargs)
        # args is tuple[params] and params contain `modelId`
        model = args[0]["modelId"]
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
            usage_tracker = LLMFY_USAGE_TRACKER_VAR.get()
            # usage_tracker.update(model=model, usage=stream_usage)
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
        model = args[0]
        # Extract token usage from headers
        headers = response.get("ResponseMetadata", {}).get("HTTPHeaders", {})
        input_tokens = int(headers.get("x-amzn-bedrock-input-token-count", 0))
        usage = {"x-amzn-bedrock-input-token-count": input_tokens}
        usage_tracker = LLMFY_USAGE_TRACKER_VAR.get()
        usage_tracker.update(
            provider=ServiceProvider.BEDROCK,
            type=ServiceType.EMBEDDING,
            model=model,
            usage=usage,
        )

        return response

    return wrapper
