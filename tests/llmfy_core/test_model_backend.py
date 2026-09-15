"""Unit tests for llmfy/llmfy_core/model_backend.py."""

import pytest

from llmfy.llmfy_core.model_backend import ModelBackend


@pytest.mark.parametrize(
    "member, value",
    [
        (ModelBackend.OPENAI_CHAT, "openai_chat"),
        (ModelBackend.OPENAI_RESPONSES, "openai_responses"),
        (ModelBackend.BEDROCK_CONVERSE, "bedrock_converse"),
        (ModelBackend.GOOGLE_GENERATE, "google_generate"),
        (ModelBackend.ANTHROPIC_MESSAGES, "anthropic_messages"),
    ],
)
def test_values(member, value):
    assert member.value == value
    assert member == value


def test_naming_convention_vendor_apivariant():
    # Every member follows "VENDOR_APIVARIANT" = "vendor_apivariant"
    for member in ModelBackend:
        assert member.name.lower() == member.value


def test_str_and_repr():
    assert str(ModelBackend.OPENAI_CHAT) == "openai_chat"
    assert repr(ModelBackend.OPENAI_CHAT) == "'openai_chat'"


def test_invalid_value_raises():
    with pytest.raises(ValueError):
        ModelBackend("not-a-real-backend")


def test_exactly_five_members():
    assert len(list(ModelBackend)) == 5
