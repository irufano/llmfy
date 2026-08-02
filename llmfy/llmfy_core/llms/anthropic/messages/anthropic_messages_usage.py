import functools
import itertools

from llmfy.llmfy_core.model_backend import ModelBackend
from llmfy.llmfy_core.service_type import ServiceType
from llmfy.llmfy_core.usage.usage_tracker import LLMFY_USAGE_TRACKER_VAR


def track_anthropic_messages_usage(func):
    """Decorator to wrap `__call_anthropic` calls on `AnthropicMessagesModel`.

    Extracts the `usage` object from the Messages API response and forwards
    it to the usage tracker. Fields (per Anthropic Messages API `Usage`):
      - input_tokens
      - output_tokens
      - cache_creation_input_tokens
      - cache_read_input_tokens

    Reference: https://platform.claude.com/docs/en/build-with-claude/prompt-caching
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        response = func(*args, **kwargs)
        usage_tracker = LLMFY_USAGE_TRACKER_VAR.get()
        if usage_tracker is None:
            return response
        model = args[0]["model"]  # args is tuple[params]; params contain `model`
        if response.usage:
            usage_tracker.update(
                backend=ModelBackend.ANTHROPIC_MESSAGES,
                type=ServiceType.LLM,
                model=model,
                usage=response.usage,
            )
        return response

    return wrapper


def track_anthropic_messages_stream_usage(func):
    """Decorator to wrap `__call_stream_anthropic` calls on
    `AnthropicMessagesModel`.

    Unlike Bedrock/OpenAI, which carry the complete usage dict in a single
    terminal stream event, Anthropic SPLITS usage across two SSE events:
      - message_start.message.usage: input_tokens, cache_creation_input_tokens,
        cache_read_input_tokens (output_tokens here is a placeholder, not final)
      - message_delta.usage: output_tokens (the FINAL cumulative value)

    This decorator tees the stream and walks the ENTIRE copy (it cannot break
    early the way Bedrock/OpenAI's decorators do, since output_tokens only
    becomes authoritative near the end of the stream), merging fields from
    both events before reporting to the usage tracker.
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        stream_origin = func(*args, **kwargs)
        usage_tracker = LLMFY_USAGE_TRACKER_VAR.get()
        if usage_tracker is None:
            return stream_origin
        model = args[0]["model"]

        merged_usage: dict[str, int] = {}

        if stream_origin:
            stream, stream_copy = itertools.tee(stream_origin)
            stream_origin = stream

            for event in stream_copy:
                event_type = getattr(event, "type", None)
                if event_type == "message_start":
                    start_usage = event.message.usage
                    merged_usage["input_tokens"] = getattr(start_usage, "input_tokens", 0) or 0
                    merged_usage["cache_creation_input_tokens"] = (
                        getattr(start_usage, "cache_creation_input_tokens", 0) or 0
                    )
                    merged_usage["cache_read_input_tokens"] = (
                        getattr(start_usage, "cache_read_input_tokens", 0) or 0
                    )
                elif event_type == "message_delta":
                    delta_usage = event.usage
                    merged_usage["output_tokens"] = getattr(delta_usage, "output_tokens", 0) or 0

        if merged_usage:
            usage_tracker.update(
                backend=ModelBackend.ANTHROPIC_MESSAGES,
                type=ServiceType.LLM,
                model=model,
                usage=merged_usage,
            )

        return stream_origin

    return wrapper
