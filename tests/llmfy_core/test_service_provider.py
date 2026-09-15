"""Unit tests for llmfy/llmfy_core/service_provider.py."""

import pytest

from llmfy.llmfy_core.service_provider import ServiceProvider


@pytest.mark.parametrize(
    "member, value",
    [
        (ServiceProvider.OPENAI, "openai"),
        (ServiceProvider.BEDROCK, "bedrock"),
        (ServiceProvider.GOOGLE, "google"),
        (ServiceProvider.ANTHROPIC, "anthropic"),
    ],
)
def test_values(member, value):
    assert member.value == value
    assert member == value


def test_str_and_repr():
    assert str(ServiceProvider.BEDROCK) == "bedrock"
    assert repr(ServiceProvider.BEDROCK) == "'bedrock'"


def test_invalid_value_raises():
    with pytest.raises(ValueError):
        ServiceProvider("not-a-real-provider")


def test_exactly_four_members():
    assert len(list(ServiceProvider)) == 4
