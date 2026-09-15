"""Unit tests for llmfy/llmfy_core/responses/generation_response.py."""

import pytest
from pydantic import ValidationError

from llmfy.llmfy_core.messages.message import Message
from llmfy.llmfy_core.messages.role import Role
from llmfy.llmfy_core.responses.ai_response import AIResponse
from llmfy.llmfy_core.responses.generation_response import GenerationResponse


def test_result_is_required():
    with pytest.raises(ValidationError):
        GenerationResponse()  # type: ignore[call-arg]


def test_messages_defaults_to_empty_list():
    response = GenerationResponse(result=AIResponse(content="hi"))
    assert response.messages == []


def test_messages_default_is_not_a_shared_mutable_default():
    r1 = GenerationResponse(result=AIResponse())
    r2 = GenerationResponse(result=AIResponse())
    r1.messages.append(Message(role=Role.USER, content="x"))
    assert r2.messages == []


def test_construct_with_messages():
    msg = Message(role=Role.USER, content="hi")
    response = GenerationResponse(result=AIResponse(content="ok"), messages=[msg])
    assert response.messages[0].content == "hi"


def test_extra_field_rejected():
    with pytest.raises(ValidationError):
        GenerationResponse(result=AIResponse(), unexpected="x")  # type: ignore[call-arg]
