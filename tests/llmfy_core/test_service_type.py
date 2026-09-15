"""Unit tests for llmfy/llmfy_core/service_type.py."""

import pytest

from llmfy.llmfy_core.service_type import ServiceType


def test_values():
    assert ServiceType.LLM.value == "llm"
    assert ServiceType.EMBEDDING.value == "embedding"


def test_str_and_repr():
    assert str(ServiceType.LLM) == "llm"
    assert repr(ServiceType.LLM) == "'llm'"


def test_invalid_value_raises():
    with pytest.raises(ValueError):
        ServiceType("not-a-real-type")
