import functools
import itertools

from llmfy.llmfy_core.service_provider import ServiceProvider
from llmfy.llmfy_core.service_type import ServiceType
from llmfy.llmfy_core.usage.usage_tracker import LLMFY_USAGE_TRACKER_VAR


def _extract_usage(usage_metadata) -> dict:
    """Extract token counts from Google AI usage_metadata.

    Captures total counts plus per-type input counts (text, image, video, audio)
    when available in the SDK response.
    """
    return {
        "prompt_token_count": usage_metadata.prompt_token_count or 0,
        "candidates_token_count": usage_metadata.candidates_token_count or 0,
        # Per-type input token counts (available in newer SDK / model versions)
        "text_token_count": getattr(usage_metadata, "text_token_count", None) or 0,
        "image_token_count": getattr(usage_metadata, "image_token_count", None) or 0,
        "video_token_count": getattr(usage_metadata, "video_token_count", None) or 0,
        "audio_token_count": getattr(usage_metadata, "audio_token_count", None) or 0,
    }


def track_googleai_usage(func):
    """Decorator to wrap `__call_googleai` calls on `GoogleAIModel`."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        response = func(*args, **kwargs)
        model = args[0]["model"]  # args is tuple[params] and params contain `model`
        if response.usage_metadata:
            usage = _extract_usage(response.usage_metadata)
            usage_tracker = LLMFY_USAGE_TRACKER_VAR.get()
            usage_tracker.update(
                provider=ServiceProvider.GOOGLE,
                type=ServiceType.LLM,
                model=model,
                usage=usage,
            )
        return response

    return wrapper


def track_googleai_stream_usage(func):
    """Decorator to wrap `__call_stream_googleai` calls on `GoogleAIModel`."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        stream_origin = func(*args, **kwargs)
        model = args[0]["model"]  # args is tuple[params] and params contain `model`

        stream_usage = None

        if stream_origin:
            stream, stream_copy = itertools.tee(stream_origin)  # Duplicate the generator
            stream_origin = stream  # Replace original stream

            for chunk in stream_copy:  # Iterate over the copy
                if (
                    chunk.usage_metadata
                    and chunk.usage_metadata.prompt_token_count
                ):
                    stream_usage = _extract_usage(chunk.usage_metadata)
                    break  # No need to iterate further

        if stream_usage:
            usage_tracker = LLMFY_USAGE_TRACKER_VAR.get()
            usage_tracker.update(
                provider=ServiceProvider.GOOGLE,
                type=ServiceType.LLM,
                model=model,
                usage=stream_usage,
            )
        return stream_origin

    return wrapper


def track_googleai_embedding_usage(func):
    """Decorator to wrap `__call_googleai_embedding` calls on `GoogleAIEmbedding`.

    The wrapped function must accept (model, contents, client) so the decorator
    can call count_tokens before embedding, since EmbedContentResponse carries
    no usage metadata.
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        model = args[0]
        contents = args[1]
        client = args[2]

        token_count = 0
        try:
            count_response = client.models.count_tokens(
                model=model,
                contents=contents,
            )
            token_count = count_response.total_tokens or 0
        except Exception:
            pass

        response = func(*args, **kwargs)

        usage_tracker = LLMFY_USAGE_TRACKER_VAR.get()
        usage_tracker.update(
            provider=ServiceProvider.GOOGLE,
            type=ServiceType.EMBEDDING,
            model=model,
            usage={"prompt_token_count": token_count},
        )
        return response

    return wrapper
