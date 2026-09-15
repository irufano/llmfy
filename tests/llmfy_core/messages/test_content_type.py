"""Unit tests for llmfy/llmfy_core/messages/content_type.py."""

import pytest

from llmfy.llmfy_core.messages.content_type import ContentType


@pytest.mark.parametrize(
    "member, value",
    [
        (ContentType.TEXT, "text"),
        (ContentType.IMAGE, "image"),
        (ContentType.DOCUMENT, "document"),
        (ContentType.VIDEO, "video"),
    ],
)
def test_values(member, value):
    assert member.value == value
    assert member == value  # StrEnum compares equal to the plain string


def test_str_returns_plain_value():
    assert str(ContentType.TEXT) == "text"


def test_repr_is_quoted_value():
    assert repr(ContentType.IMAGE) == "'image'"


def test_construct_from_string():
    assert ContentType("document") is ContentType.DOCUMENT


def test_invalid_value_raises_value_error():
    with pytest.raises(ValueError):
        ContentType("not-a-real-type")
