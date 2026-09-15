"""Unit tests for llmfy/llmfy_core/responses/ai_response.py."""

import pytest
from pydantic import ValidationError

from llmfy.llmfy_core.messages.tool_call import ToolCall
from llmfy.llmfy_core.responses.ai_response import AIResponse


def test_all_fields_optional():
    response = AIResponse()
    assert response.content is None
    assert response.thinking is None
    assert response.tool_calls is None


def test_construct_with_content():
    response = AIResponse(content="hello")
    assert response.content == "hello"


def test_construct_with_tool_calls():
    tool_call = ToolCall(tool_call_id="c1", request_call_id="r1", name="fn", arguments={})
    response = AIResponse(tool_calls=[tool_call])
    assert response.tool_calls[0].name == "fn" # type: ignore


def test_extra_field_rejected():
    with pytest.raises(ValidationError):
        AIResponse(unexpected="x")  # type: ignore[call-arg]
