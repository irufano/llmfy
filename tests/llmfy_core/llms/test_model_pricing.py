"""Unit tests for llmfy/llmfy_core/llms/model_pricing.py."""

import pytest
from pydantic import ValidationError

from llmfy.llmfy_core.llms.model_pricing import ModelPricing


def test_required_fields():
    pricing = ModelPricing(token_input=1.0, token_output=2.0)
    assert pricing.token_input == 1.0
    assert pricing.token_output == 2.0


def test_defaults():
    pricing = ModelPricing(token_input=1.0, token_output=2.0)
    assert pricing.token_unit == 1_000_000
    assert pricing.cache_read is None
    assert pricing.cache_write is None


def test_missing_required_field_raises():
    with pytest.raises(ValidationError):
        ModelPricing(token_input=1.0)  # type: ignore[call-arg]


def test_repr_is_dict_dump():
    pricing = ModelPricing(token_input=1.0, token_output=2.0, token_unit=1000)
    assert repr(pricing) == str(pricing.model_dump())
    assert "token_input" in repr(pricing)
