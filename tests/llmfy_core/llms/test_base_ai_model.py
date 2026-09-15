"""Unit tests for llmfy/llmfy_core/llms/base_ai_model.py."""

import pytest

from llmfy.llmfy_core.llms.base_ai_model import BaseAIModel, sync_gen_to_async


def test_base_ai_model_cannot_be_instantiated_directly():
    with pytest.raises(TypeError):
        BaseAIModel()  # type: ignore[abstract]


def test_subclass_missing_an_abstract_method_cannot_be_instantiated():
    class Incomplete(BaseAIModel):
        def generate(self, messages, tools=None, **kwargs):
            return None

        def generate_stream(self, messages, tools=None, **kwargs):
            return iter([])

        async def agenerate(self, messages, tools=None, **kwargs):
            return None

        # agenerate_stream intentionally omitted

    with pytest.raises(TypeError):
        Incomplete()  # type: ignore[abstract]


@pytest.mark.asyncio
async def test_sync_gen_to_async_yields_items_in_order():
    def gen():
        yield 1
        yield 2
        yield 3

    results = [item async for item in sync_gen_to_async(gen())]
    assert results == [1, 2, 3]


@pytest.mark.asyncio
async def test_sync_gen_to_async_handles_empty_generator():
    def empty_gen():
        return
        yield  # pragma: no cover - unreachable, makes this a generator function

    results = [item async for item in sync_gen_to_async(empty_gen())]
    assert results == []


@pytest.mark.asyncio
async def test_sync_gen_to_async_propagates_exception_raised_inside_generator():
    def failing_gen():
        yield 1
        raise ValueError("boom")

    results = []
    with pytest.raises(ValueError, match="boom"):
        async for item in sync_gen_to_async(failing_gen()):
            results.append(item)
    assert results == [1]
