"""Unit tests for llmfy/llmfy_core/messages/message.py."""

import pytest
from pydantic import ValidationError

from llmfy.llmfy_core.messages.message import Message
from llmfy.llmfy_core.messages.role import Role
from llmfy.llmfy_core.messages.tool_call import ToolCall


def make_tool_call(**overrides):
    defaults = dict(
        tool_call_id="call_1", request_call_id="req_1", name="get_weather", arguments={}
    )
    defaults.update(overrides)
    return ToolCall(**defaults)  # type: ignore


class TestValidRoleContentCombinations:
    def test_user_message_with_string_content(self):
        msg = Message(role=Role.USER, content="hello")
        assert msg.content == "hello"

    def test_system_message(self):
        msg = Message(role=Role.SYSTEM, content="you are a helpful assistant")
        assert msg.role == Role.SYSTEM

    def test_assistant_message_with_tool_calls(self):
        msg = Message(role=Role.ASSISTANT, tool_calls=[make_tool_call()])
        assert len(msg.tool_calls) == 1  # type: ignore

    def test_tool_message_with_tool_results(self):
        msg = Message(role=Role.TOOL, tool_call_id="call_1", tool_results=["sunny"])
        assert msg.tool_results == ["sunny"]

    def test_content_none_is_allowed_for_non_tool_roles(self):
        msg = Message(role=Role.USER, content=None)
        assert msg.content is None


class TestCrossFieldValidation:
    """Message.model_post_init enforces 4 invariants, checked in this order."""

    def test_tool_results_on_non_tool_role_raises(self):
        with pytest.raises(
            ValueError, match="tool_results can only be set when role is 'tool'"
        ):
            Message(role=Role.USER, tool_results=["x"])

    def test_tool_role_without_tool_results_raises(self):
        with pytest.raises(
            ValueError, match="Expected tool_results when role is 'tool'"
        ):
            Message(role=Role.TOOL, tool_call_id="call_1")

    def test_tool_role_with_empty_tool_results_list_also_raises(self):
        # Empty list is falsy -> treated the same as missing.
        with pytest.raises(
            ValueError, match="Expected tool_results when role is 'tool'"
        ):
            Message(role=Role.TOOL, tool_call_id="call_1", tool_results=[])

    def test_tool_call_id_on_non_tool_role_raises(self):
        with pytest.raises(
            ValueError, match="tool_call_id can only be set when role is 'tool'"
        ):
            Message(role=Role.USER, tool_call_id="call_1")

    def test_tool_calls_on_non_assistant_role_raises(self):
        with pytest.raises(
            ValueError, match="tool_calls can only be set when role is 'assistant'"
        ):
            Message(role=Role.USER, tool_calls=[make_tool_call()])

    def test_validation_errors_are_wrapped_in_pydantic_validation_error(self):
        # model_post_init raises a bare ValueError, but pydantic v2 wraps any
        # exception raised there into its own ValidationError (which is
        # itself a ValueError subclass) — the original message survives
        # inside its formatted output.
        with pytest.raises(ValidationError) as exc_info:
            Message(role=Role.USER, tool_results=["x"])
        assert "tool_results can only be set when role is 'tool'" in str(exc_info.value)

    def test_first_matching_rule_wins_when_multiple_violated(self):
        # tool_results-on-wrong-role (rule 1) is checked before
        # tool_call_id-on-wrong-role (rule 3).
        with pytest.raises(ValueError, match="tool_results can only be set"):
            Message(role=Role.USER, tool_results=["x"], tool_call_id="call_1")


class TestDefaults:
    def test_id_defaults_to_unique_uuid_per_instance(self):
        msg1 = Message(role=Role.USER, content="a")
        msg2 = Message(role=Role.USER, content="b")
        assert msg1.id != msg2.id

    def test_timestamp_defaults_to_iso8601_string(self):
        msg = Message(role=Role.USER, content="a")
        assert isinstance(msg.timestamp, str)
        # Should be parseable back as ISO 8601
        from datetime import datetime

        datetime.fromisoformat(msg.timestamp)

    def test_explicit_id_is_respected(self):
        msg = Message(id="custom-id", role=Role.USER, content="a")
        assert msg.id == "custom-id"


class TestStrictSchema:
    def test_extra_field_rejected(self):
        with pytest.raises(ValidationError):
            Message(role=Role.USER, content="a", made_up_field="x") # type: ignore

    def test_invalid_role_string_rejected(self):
        with pytest.raises(ValidationError):
            Message(role="not-a-real-role", content="a") # type: ignore

    def test_role_string_coercion(self):
        msg = Message(role="user", content="a") # type: ignore
        assert msg.role == Role.USER
