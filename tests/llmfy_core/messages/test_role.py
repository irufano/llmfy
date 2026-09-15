"""Unit tests for llmfy/llmfy_core/messages/role.py."""

import pytest

from llmfy.llmfy_core.messages.role import Role


@pytest.mark.parametrize(
    "member, value",
    [
        (Role.SYSTEM, "system"),
        (Role.USER, "user"),
        (Role.ASSISTANT, "assistant"),
        (Role.TOOL, "tool"),
    ],
)
def test_values(member, value):
    assert member.value == value
    assert member == value


def test_str_returns_plain_value():
    assert str(Role.ASSISTANT) == "assistant"


def test_repr_is_quoted_value():
    assert repr(Role.TOOL) == "'tool'"


def test_construct_from_string():
    assert Role("user") is Role.USER


def test_invalid_value_raises_value_error():
    with pytest.raises(ValueError):
        Role("not-a-real-role")
