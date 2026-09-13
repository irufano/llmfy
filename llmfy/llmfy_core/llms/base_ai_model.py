import asyncio
from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator, Generator
from typing import Any

from llmfy.llmfy_core.model_backend import ModelBackend
from llmfy.llmfy_core.responses.ai_response import AIResponse
from llmfy.llmfy_core.service_provider import ServiceProvider


async def sync_gen_to_async(sync_gen: Generator) -> AsyncGenerator[Any, None]:
    """Bridge a blocking sync generator into an async generator.

    Pulls one item at a time via `next()` in a worker thread, so each
    blocking step (e.g. waiting on the next network chunk) doesn't block the
    event loop, while still yielding items as they arrive rather than
    buffering the whole stream before returning anything.

    Shared by `BaseAIModel.agenerate_stream`'s default and `LLMfy`'s
    streaming async wrappers.
    """
    _exhausted = object()
    it = iter(sync_gen)
    while True:
        # `next(it, default)` rather than a bare `next(it)` + catching
        # StopIteration: a StopIteration raised inside the worker thread
        # propagates back via the Future's exception slot, and asyncio
        # forbids StopIteration there (PEP 479) — it'd surface as an opaque
        # RuntimeError instead of ending the loop.
        item = await asyncio.to_thread(next, it, _exhausted)
        if item is _exhausted:
            break
        yield item


class BaseAIModel(ABC):
    """BaseAIModel Abstract"""

    def __init__(self):
        """Model provider."""
        self.backend: ModelBackend
        self.provider: ServiceProvider

    @abstractmethod
    def generate(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        **kwargs,
    ) -> AIResponse:
        pass

    @abstractmethod
    def generate_stream(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        **kwargs,
    ) -> Any:
        pass

    @abstractmethod
    async def agenerate(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        **kwargs,
    ) -> AIResponse:
        """Async version of `generate`.

        Every backend must implement this explicitly (no inherited default)
        so the choice between a real non-blocking call and a thread-offloaded
        one is visible per backend rather than silently inherited:
          - `OpenAIChatModel`, `OpenAIResponsesModel`, `AnthropicMessagesModel`,
            `GoogleAIGenerateModel`: native async client — no `asyncio.to_thread`
            thread-pool ceiling (default ~32 workers) on concurrent fan-out.
          - `BedrockConverseModel`: native async via the optional `aioboto3`
            dependency (boto3 itself has no async mode); raises `LLMfyException`
            if `aioboto3` isn't installed.

        A backend with no native async path of its own can still opt into the
        thread-offload behavior with one line:
        `return await asyncio.to_thread(self.generate, messages, tools, **kwargs)`.
        """

    @abstractmethod
    def agenerate_stream(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        **kwargs,
    ) -> AsyncGenerator[AIResponse, Any]:
        """Async version of `generate_stream`.

        Every backend must implement this explicitly — see `agenerate` for
        why there's no inherited default. A backend without a native async
        streaming path can opt into the thread-offload behavior with one
        line: `return sync_gen_to_async(self.generate_stream(messages, tools, **kwargs))`
        (pulls one chunk at a time via `next()` in a worker thread, so it's
        still non-blocking to the event loop even though it isn't a true
        async network call).
        """
