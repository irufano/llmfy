"""Unit tests for llmfy/llmfy_core/usage/usage_tracker.py."""

import pytest

from llmfy.exception.llmfy_exception import LLMfyException
from llmfy.llmfy_core.usage.llmfy_usage import LLMfyUsage
from llmfy.llmfy_core.usage.usage_tracker import (
    LLMFY_USAGE_TRACKER_VAR,
    llmfy_usage_tracker,
)


def test_yields_an_llmfy_usage_instance():
    with llmfy_usage_tracker() as usage:
        assert isinstance(usage, LLMfyUsage)


def test_context_var_is_set_to_the_yielded_tracker_inside_the_block():
    with llmfy_usage_tracker() as usage:
        assert LLMFY_USAGE_TRACKER_VAR.get() is usage


def test_invalid_pricing_raises_before_the_block_body_runs():
    entered = False
    with pytest.raises(LLMfyException):
        with llmfy_usage_tracker(openai_pricing={"m": {"input": "not-a-number"}}):
            entered = True
    assert entered is False


def test_exception_inside_the_block_propagates():
    with pytest.raises(ValueError):
        with llmfy_usage_tracker():
            raise ValueError("boom")


def test_context_var_retains_stale_value_after_exit():
    # Documents current behavior: the `finally` clause does nothing, so the
    # ContextVar is NOT reset to None (or restored to any prior value) once
    # the `with` block exits.
    with llmfy_usage_tracker() as usage:
        pass
    assert LLMFY_USAGE_TRACKER_VAR.get() is usage


def test_sequential_trackers_each_get_a_fresh_instance():
    with llmfy_usage_tracker() as first:
        pass
    with llmfy_usage_tracker() as second:
        pass
    assert first is not second
    assert LLMFY_USAGE_TRACKER_VAR.get() is second
