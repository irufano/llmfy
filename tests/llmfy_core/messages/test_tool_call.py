"""Unit tests for llmfy/llmfy_core/messages/tool_call.py."""

import pytest
from pydantic import ValidationError

from llmfy.llmfy_core.messages.tool_call import ToolCall


def test_all_fields_required():
    tool_call = ToolCall(
        tool_call_id="call_1",
        request_call_id="req_1",
        name="get_weather",
        arguments={"city": "Paris"},
    )
    assert tool_call.tool_call_id == "call_1"
    assert tool_call.request_call_id == "req_1"
    assert tool_call.name == "get_weather"
    assert tool_call.arguments == {"city": "Paris"}


@pytest.mark.parametrize(
    "missing_field", ["tool_call_id", "request_call_id", "name", "arguments"]
)
def test_missing_required_field_raises(missing_field):
    fields = dict(
        tool_call_id="call_1", request_call_id="req_1", name="fn", arguments={}
    )
    del fields[missing_field]
    with pytest.raises(ValidationError):
        ToolCall(**fields) # type: ignore


def test_extra_field_is_silently_ignored_unlike_message_and_content():
    # ToolCall has no ConfigDict(extra="forbid") — a deliberate contrast with
    # Message/Content/AIResponse/GenerationResponse, which do forbid extras.
    tool_call = ToolCall(
        tool_call_id="call_1",
        request_call_id="req_1",
        name="fn",
        arguments={},
        unexpected_field="ignored", # type: ignore
    )
    assert not hasattr(tool_call, "unexpected_field")


def test_arguments_accepts_nested_structures():
    tool_call = ToolCall(
        tool_call_id="c1",
        request_call_id="r1",
        name="fn",
        arguments={"nested": {"a": [1, 2, 3]}},
    )
    assert tool_call.arguments["nested"]["a"] == [1, 2, 3]
