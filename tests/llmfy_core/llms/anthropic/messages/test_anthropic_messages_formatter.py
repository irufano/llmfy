"""Unit tests for llmfy/llmfy_core/llms/anthropic/messages/anthropic_messages_formatter.py."""

import base64

import pytest

from llmfy.exception.llmfy_exception import LLMfyException
from llmfy.llmfy_core.llms.anthropic.messages.anthropic_messages_formatter import (
    AnthropicMessagesFormatter,
)
from llmfy.llmfy_core.messages.content import Content
from llmfy.llmfy_core.messages.content_type import ContentType
from llmfy.llmfy_core.messages.message import Message
from llmfy.llmfy_core.messages.role import Role
from llmfy.llmfy_core.messages.tool_call import ToolCall


@pytest.fixture
def formatter() -> AnthropicMessagesFormatter:
    return AnthropicMessagesFormatter()


class TestFormatMessage:
    def test_tool_role_maps_to_user(self, formatter):
        msg = Message(role=Role.TOOL, tool_call_id="c1", tool_results=["r"])
        result = formatter.format_message(msg)
        assert result["role"] == "user"

    def test_system_role_kept_as_system_placeholder(self, formatter):
        # The native API has no system role in `messages`; the model layer
        # strips this out before calling the SDK — the formatter alone still
        # emits it.
        msg = Message(role=Role.SYSTEM, content="be nice")
        result = formatter.format_message(msg)
        assert result["role"] == "system"

    def test_text_content_wrapped_in_block(self, formatter):
        msg = Message(role=Role.USER, content="hello")
        result = formatter.format_message(msg)
        assert result["content"] == [{"type": "text", "text": "hello"}]

    def test_image_requires_format(self, formatter):
        msg = Message(
            role=Role.USER, content=[Content(type=ContentType.IMAGE, value=b"...")]
        )
        with pytest.raises(LLMfyException, match="format"):
            formatter.format_message(msg)

    def test_image_rejects_unsupported_format(self, formatter):
        msg = Message(
            role=Role.USER,
            content=[Content(type=ContentType.IMAGE, value=b"...", format="bmp")],
        )
        with pytest.raises(LLMfyException, match="must be in"):
            formatter.format_message(msg)

    def test_image_use_s3_rejected(self, formatter):
        msg = Message(
            role=Role.USER,
            content=[
                Content(
                    type=ContentType.IMAGE, value="s3://x", format="png", use_s3=True
                )
            ],
        )
        with pytest.raises(LLMfyException, match="Bedrock-only"):
            formatter.format_message(msg)

    def test_image_bytes_are_base64_encoded(self, formatter):
        raw = b"fake-image-bytes"
        msg = Message(
            role=Role.USER,
            content=[Content(type=ContentType.IMAGE, value=raw, format="png")],
        )
        result = formatter.format_message(msg)
        block = result["content"][0]
        assert block["source"]["data"] == base64.b64encode(raw).decode("utf-8")
        assert block["source"]["media_type"] == "image/png"

    def test_document_requires_filename(self, formatter):
        msg = Message(
            role=Role.USER, content=[Content(type=ContentType.DOCUMENT, value=b"...")]
        )
        with pytest.raises(LLMfyException, match="filename"):
            formatter.format_message(msg)

    def test_video_always_raises(self, formatter):
        msg = Message(
            role=Role.USER, content=[Content(type=ContentType.VIDEO, value=b"...")]
        )
        with pytest.raises(LLMfyException, match="does not support video"):
            formatter.format_message(msg)

    def test_tool_calls_formatted_as_tool_use_blocks(self, formatter):
        tool_call = ToolCall(
            tool_call_id="c1", request_call_id="r1", name="fn", arguments={"a": 1}
        )
        msg = Message(role=Role.ASSISTANT, tool_calls=[tool_call])
        result = formatter.format_message(msg)
        assert result["content"] == [
            {"type": "tool_use", "id": "c1", "name": "fn", "input": {"a": 1}}
        ]

    def test_name_field_never_emitted(self, formatter):
        msg = Message(role=Role.USER, content="hi", name="ignored")
        result = formatter.format_message(msg)
        assert "name" not in result


class TestFormatToolFunction:
    def test_every_param_unconditionally_required_even_with_default(self, formatter):
        # Unlike OpenAI/Google, Anthropic's formatter never checks
        # param.default — every param always ends up in `required`.
        from llmfy.llmfy_core.tools.function_parser import FunctionParser
        from llmfy.llmfy_core.tools.function_type_mapping import FUNCTION_TYPE_MAPPING

        def get_weather(location: str, unit: str = "celsius") -> str:
            """Get weather.

            Args:
                location (str): The city.
                unit (str): Temperature unit.
            """
            return "sunny"

        metadata = FunctionParser.get_function_metadata(get_weather)
        tool_def = formatter.format_tool_function(metadata, FUNCTION_TYPE_MAPPING)
        assert set(tool_def["input_schema"]["required"]) == {"location", "unit"}

    def test_description_falls_back_to_name_when_empty(self, formatter):
        from llmfy.llmfy_core.tools.function_parser import FunctionParser
        from llmfy.llmfy_core.tools.function_type_mapping import FUNCTION_TYPE_MAPPING

        def undocumented() -> str:
            return "x"

        metadata = FunctionParser.get_function_metadata(undocumented)
        tool_def = formatter.format_tool_function(metadata, FUNCTION_TYPE_MAPPING)
        assert tool_def["description"] == "undocumented"


class TestFormatToolMessage:
    def test_merges_parallel_tool_results_into_one_message(self, formatter):
        messages: list[Message] = []
        formatter.format_tool_message(
            messages,
            id="t1",
            tool_call_id="c1",
            name="fn1",
            result="r1",
            request_call_id="req_A",
        )
        formatter.format_tool_message(
            messages,
            id="t2",
            tool_call_id="c2",
            name="fn2",
            result="r2",
            request_call_id="req_A",
        )
        # Same request_call_id -> merged into a single TOOL-role message.
        assert len(messages) == 1
        assert len(messages[0].tool_results) == 2  # type: ignore

    def test_different_request_call_id_creates_a_new_message(self, formatter):
        messages: list[Message] = []
        formatter.format_tool_message(
            messages,
            id="t1",
            tool_call_id="c1",
            name="fn1",
            result="r1",
            request_call_id="req_A",
        )
        formatter.format_tool_message(
            messages,
            id="t2",
            tool_call_id="c2",
            name="fn2",
            result="r2",
            request_call_id="req_B",
        )
        assert len(messages) == 2

    def test_tool_result_uses_tool_use_id_field_name(self, formatter):
        messages: list[Message] = []
        formatter.format_tool_message(
            messages, id="t1", tool_call_id="c1", name="fn", result="r1"
        )
        assert messages[0].tool_results[0] == {  # type: ignore
            "type": "tool_result",
            "tool_use_id": "c1",
            "content": "r1",
        }
