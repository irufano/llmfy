"""Unit tests for llmfy/llmfy_core/messages/content.py."""

import pytest
from pydantic import ValidationError

from llmfy.llmfy_core.messages.content import Content
from llmfy.llmfy_core.messages.content_type import ContentType


def test_default_type_is_text():
    c = Content(value="hello")
    assert c.type == ContentType.TEXT


def test_value_is_required():
    with pytest.raises(ValidationError):
        Content()  # type: ignore[call-arg]


def test_value_accepts_str():
    c = Content(value="a string")
    assert c.value == "a string"


def test_value_accepts_bytes():
    c = Content(value=b"raw bytes")
    assert c.value == b"raw bytes"


def test_optional_fields_default_to_none_or_false():
    c = Content(value="x")
    assert c.filename is None
    assert c.format is None
    assert c.use_s3 is False
    assert c.bucket_owner is None


def test_extra_field_rejected():
    with pytest.raises(ValidationError):
        Content(value="x", unknown_field="y")  # type: ignore[call-arg]


def test_no_provider_specific_format_validation_at_model_level():
    # Content itself performs no cross-field validation (documented lenient
    # behavior) — an unsupported image format string is accepted here; the
    # provider-specific formatter is what rejects it (see formatter tests).
    c = Content(type=ContentType.IMAGE, value=b"...", format="not-a-real-format")
    assert c.format == "not-a-real-format"
