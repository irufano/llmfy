import functools

from llmfy.llmfy_core.model_backend import ModelBackend
from llmfy.llmfy_core.service_type import ServiceType
from llmfy.llmfy_core.usage.usage_tracker import LLMFY_USAGE_TRACKER_VAR


def track_openai_responses_usage(func):
    """Decorator to wrap `__call_openai_responses` calls on `OpenAIResponsesModel`.

    Passes the raw ResponseUsage object from the API response directly to the
    usage tracker. The object contains:
      - input_tokens:                     total input tokens (includes cached tokens)
      - output_tokens:                    output tokens
      - input_tokens_details.cached_tokens:
                                           tokens served from OpenAI's automatic cache
      - input_tokens_details.cache_write_tokens:
                                           tokens written to cache this request
      - output_tokens_details.reasoning_tokens:
                                           reasoning tokens included in output_tokens

    Field names differ from Chat Completions' `prompt_tokens`/`completion_tokens`
    (see `openai_usage.py`), so this is tracked separately in `LLMfyUsage`.

    Reference: https://developers.openai.com/api/reference/responses/overview
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        response = func(*args, **kwargs)
        usage_tracker = LLMFY_USAGE_TRACKER_VAR.get()
        if usage_tracker is None:
            return response
        model = args[0][
            "model"
        ]  # args is tuple[OpenAIResponsesModel, params] and params contain `model`
        if response.usage:
            usage_tracker.update(
                backend=ModelBackend.OPENAI_RESPONSES,
                type=ServiceType.LLM,
                model=model,
                usage=response.usage,
            )
        return response

    return wrapper


def track_openai_responses_stream_usage(func):
    """Decorator to wrap `__call_stream_openai_responses` calls on `OpenAIResponsesModel`.

    Unlike Chat Completions, the Responses API's final streaming event
    (`response.completed`) already carries the full `response` object
    (including `usage`) — no need to tee the stream and scan for a usage-bearing
    chunk.
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        stream = func(*args, **kwargs)
        usage_tracker = LLMFY_USAGE_TRACKER_VAR.get()
        model = args[0]["model"]

        for event in stream:
            if usage_tracker is not None and getattr(event, "type", None) == "response.completed":
                usage = getattr(event.response, "usage", None)
                if usage:
                    usage_tracker.update(
                        backend=ModelBackend.OPENAI_RESPONSES,
                        type=ServiceType.LLM,
                        model=model,
                        usage=usage,
                    )
            yield event

    return wrapper
