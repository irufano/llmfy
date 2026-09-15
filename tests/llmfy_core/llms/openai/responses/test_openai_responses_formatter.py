"""Unit tests for llmfy/llmfy_core/llms/openai/responses/openai_responses_formatter.py."""

import pytest

from llmfy.exception.llmfy_exception import LLMfyException
from llmfy.llmfy_core.llms.openai.responses.openai_responses_formatter import (
    OpenAIResponsesFormatter,
)
from llmfy.llmfy_core.messages.content import Content
from llmfy.llmfy_core.messages.content_type import ContentType
from llmfy.llmfy_core.messages.message import Message
from llmfy.llmfy_core.messages.role import Role
from llmfy.llmfy_core.messages.tool_call import ToolCall


@pytest.fixture
def formatter() -> OpenAIResponsesFormatter:
    return OpenAIResponsesFormatter()


class TestFormatMessage:
    def test_user_text_is_input_text(self, formatter):
        msg = Message(role=Role.USER, content="hi")
        result = formatter.format_message(msg)
        assert result == {
            "type": "message",
            "role": "user",
            "content": [{"type": "input_text", "text": "hi"}],
        }

    def test_assistant_replay_uses_output_text(self, formatter):
        # Prior assistant turns are replayed as "output_text", not "input_text".
        msg = Message(role=Role.ASSISTANT, content="previous answer")
        result = formatter.format_message(msg)
        assert result["content"][0]["type"] == "output_text"

    def test_image_content(self, formatter):
        msg = Message(
            role=Role.USER,
            content=[Content(type=ContentType.IMAGE, value="https://x/i.jpg")],
        )
        result = formatter.format_message(msg)
        assert result["content"] == [
            {"type": "input_image", "image_url": "https://x/i.jpg"}
        ]

    def test_document_content_raises_not_supported(self, formatter):
        msg = Message(
            role=Role.USER,
            content=[Content(type=ContentType.DOCUMENT, value="b64", filename="x.pdf")],
        )
        with pytest.raises(LLMfyException, match="DOCUMENT"):
            formatter.format_message(msg)

    def test_video_content_raises_not_supported(self, formatter):
        msg = Message(
            role=Role.USER, content=[Content(type=ContentType.VIDEO, value=b"...")]
        )
        with pytest.raises(LLMfyException, match="VIDEO"):
            formatter.format_message(msg)

    def test_tool_result_message_returns_function_call_output_item(self, formatter):
        msg = Message(role=Role.TOOL, tool_call_id="call_1", tool_results=["sunny"])
        result = formatter.format_message(msg)
        assert result == {
            "type": "function_call_output",
            "call_id": "call_1",
            "output": "sunny",
        }

    def test_single_tool_call_wrapped_in_private_items_list(self, formatter):
        tool_call = ToolCall(
            tool_call_id="call_1",
            request_call_id="req_1",
            name="get_weather",
            arguments={"c": "Paris"},
        )
        msg = Message(role=Role.ASSISTANT, tool_calls=[tool_call])
        result = formatter.format_message(msg)
        assert "__items__" in result
        assert len(result["__items__"]) == 1
        assert result["__items__"][0]["type"] == "function_call"
        assert result["__items__"][0]["call_id"] == "call_1"

    def test_multiple_parallel_tool_calls_produce_multiple_items(self, formatter):
        tool_calls = [
            ToolCall(tool_call_id="c1", request_call_id="r1", name="fn1", arguments={}),
            ToolCall(tool_call_id="c2", request_call_id="r1", name="fn2", arguments={}),
        ]
        msg = Message(role=Role.ASSISTANT, tool_calls=tool_calls)
        result = formatter.format_message(msg)
        assert len(result["__items__"]) == 2


class TestFormatToolFunction:
    def test_omits_type_function_wrapper(self, formatter):
        from llmfy.llmfy_core.tools.function_parser import FunctionParser
        from llmfy.llmfy_core.tools.function_type_mapping import FUNCTION_TYPE_MAPPING

        def get_weather(location: str) -> str:
            """Get weather.

            Args:
                location (str): The city.
            """
            return "sunny"

        metadata = FunctionParser.get_function_metadata(get_weather)
        tool_def = formatter.format_tool_function(metadata, FUNCTION_TYPE_MAPPING)
        assert "type" not in tool_def
        assert tool_def["strict"] is True


class TestFormatToolMessage:
    def test_always_appends_never_merges(self, formatter):
        messages: list[Message] = []
        formatter.format_tool_message(
            messages, id="t1", tool_call_id="c1", name="fn", result="r1"
        )
        formatter.format_tool_message(
            messages, id="t2", tool_call_id="c2", name="fn2", result="r2"
        )
        assert len(messages) == 2
