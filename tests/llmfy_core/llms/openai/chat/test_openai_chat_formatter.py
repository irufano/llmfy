"""Unit tests for llmfy/llmfy_core/llms/openai/chat/openai_chat_formatter.py."""

import pytest

from llmfy.exception.llmfy_exception import LLMfyException
from llmfy.llmfy_core.llms.openai.chat.openai_chat_formatter import OpenAIChatFormatter
from llmfy.llmfy_core.messages.content import Content
from llmfy.llmfy_core.messages.content_type import ContentType
from llmfy.llmfy_core.messages.message import Message
from llmfy.llmfy_core.messages.role import Role
from llmfy.llmfy_core.messages.tool_call import ToolCall
from llmfy.llmfy_core.tools.function_parser import FunctionParser


@pytest.fixture
def formatter() -> OpenAIChatFormatter:
    return OpenAIChatFormatter()


class TestFormatMessageBasic:
    def test_plain_text_message(self, formatter):
        msg = Message(role=Role.USER, content="hello")
        result = formatter.format_message(msg)
        assert result == {"role": "user", "content": "hello"}

    def test_system_role_passed_through_as_is(self, formatter):
        # No "developer" remapping — OpenAIChatModel/OpenAI SDK handles that,
        # the formatter just passes role.value straight through.
        msg = Message(role=Role.SYSTEM, content="be nice")
        result = formatter.format_message(msg)
        assert result["role"] == "system"

    def test_none_content_produces_no_content_key(self, formatter):
        msg = Message(role=Role.ASSISTANT, content=None)
        result = formatter.format_message(msg)
        assert "content" not in result


class TestFormatMessageContentTypes:
    def test_text_content_block(self, formatter):
        msg = Message(role=Role.USER, content=[Content(type=ContentType.TEXT, value="hi")])
        result = formatter.format_message(msg)
        assert result["content"] == [{"type": "text", "text": "hi"}]

    def test_image_content_block(self, formatter):
        msg = Message(
            role=Role.USER,
            content=[Content(type=ContentType.IMAGE, value="https://x/img.jpg")],
        )
        result = formatter.format_message(msg)
        assert result["content"] == [
            {"type": "image_url", "image_url": {"url": "https://x/img.jpg"}}
        ]

    def test_document_requires_filename(self, formatter):
        msg = Message(role=Role.USER, content=[Content(type=ContentType.DOCUMENT, value="b64")])
        with pytest.raises(LLMfyException, match="filename"):
            formatter.format_message(msg)

    def test_document_content_block(self, formatter):
        msg = Message(
            role=Role.USER,
            content=[Content(type=ContentType.DOCUMENT, value="b64data", filename="doc.pdf")],
        )
        result = formatter.format_message(msg)
        assert result["content"] == [
            {"type": "file", "file": {"filename": "doc.pdf", "file_data": "b64data"}}
        ]

    def test_video_always_raises(self, formatter):
        msg = Message(role=Role.USER, content=[Content(type=ContentType.VIDEO, value=b"...")])
        with pytest.raises(LLMfyException, match="VIDEO"):
            formatter.format_message(msg)


class TestFormatMessageToolCallsAndResults:
    def test_tool_calls_formatted_as_function_entries(self, formatter):
        tool_call = ToolCall(
            tool_call_id="call_1", request_call_id="req_1", name="get_weather", arguments={"c": "Paris"}
        )
        msg = Message(role=Role.ASSISTANT, tool_calls=[tool_call])
        result = formatter.format_message(msg)
        assert result["tool_calls"] == [
            {
                "id": "call_1",
                "type": "function",
                "function": {"name": "get_weather", "arguments": '{"c": "Paris"}'},
            }
        ]
        assert "content" not in result

    def test_tool_results_only_use_first_item(self, formatter):
        msg = Message(role=Role.TOOL, tool_call_id="call_1", tool_results=["first", "second"])
        result = formatter.format_message(msg)
        assert result["content"] == "first"

    def test_tool_call_id_and_name_included_when_set(self, formatter):
        msg = Message(
            role=Role.TOOL, tool_call_id="call_1", name="get_weather", tool_results=["sunny"]
        )
        result = formatter.format_message(msg)
        assert result["tool_call_id"] == "call_1"
        assert result["name"] == "get_weather"


def sample_tool(location: str, unit: str = "celsius") -> str:
    """Get the weather.

    Args:
        location (str): The city.
        unit (str): Temperature unit.
    """
    return "sunny"


def sample_tool_optional(location: str | None = None) -> str:
    """Get the weather, location optional.

    Args:
        location (str): Optional city.
    """
    return "sunny"


class TestFormatToolFunction:
    def test_basic_shape(self, formatter):
        metadata = FunctionParser.get_function_metadata(sample_tool)
        from llmfy.llmfy_core.tools.function_type_mapping import FUNCTION_TYPE_MAPPING

        tool_def = formatter.format_tool_function(metadata, FUNCTION_TYPE_MAPPING)
        assert tool_def["name"] == "sample_tool"
        assert tool_def["strict"] is True
        assert tool_def["parameters"]["additionalProperties"] is False
        assert "location" in tool_def["parameters"]["properties"]
        assert tool_def["parameters"]["properties"]["location"]["type"] == "string"

    def test_strict_true_makes_every_param_required_even_with_default(self, formatter):
        # OpenAI's strict=True forces ALL params required, unlike Google
        # which respects Python defaults.
        metadata = FunctionParser.get_function_metadata(sample_tool)
        from llmfy.llmfy_core.tools.function_type_mapping import FUNCTION_TYPE_MAPPING

        tool_def = formatter.format_tool_function(metadata, FUNCTION_TYPE_MAPPING)
        assert set(tool_def["parameters"]["required"]) == {"location", "unit"}

    def test_default_value_appended_to_description(self, formatter):
        metadata = FunctionParser.get_function_metadata(sample_tool)
        from llmfy.llmfy_core.tools.function_type_mapping import FUNCTION_TYPE_MAPPING

        tool_def = formatter.format_tool_function(metadata, FUNCTION_TYPE_MAPPING)
        assert "(default: celsius)" in tool_def["parameters"]["properties"]["unit"]["description"]

    def test_optional_union_type_unwrapped_to_inner_type(self, formatter):
        metadata = FunctionParser.get_function_metadata(sample_tool_optional)
        from llmfy.llmfy_core.tools.function_type_mapping import FUNCTION_TYPE_MAPPING

        tool_def = formatter.format_tool_function(metadata, FUNCTION_TYPE_MAPPING)
        # str | None unwraps to "string", not falling back to the generic default.
        assert tool_def["parameters"]["properties"]["location"]["type"] == "string"

    def test_self_parameter_is_skipped(self, formatter):
        class Foo:
            def bar(self, x: int) -> int:
                """Do a thing.

                Args:
                    x (int): a number.
                """
                return x

        metadata = FunctionParser.get_function_metadata(Foo.bar)
        from llmfy.llmfy_core.tools.function_type_mapping import FUNCTION_TYPE_MAPPING

        tool_def = formatter.format_tool_function(metadata, FUNCTION_TYPE_MAPPING)
        assert "self" not in tool_def["parameters"]["properties"]
        assert "self" not in tool_def["parameters"]["required"]

    def test_unmapped_type_falls_back_to_string(self, formatter):
        def weird_tool(items: set) -> str:
            """Weird tool.

            Args:
                items (set): a set of items.
            """
            return "ok"

        metadata = FunctionParser.get_function_metadata(weird_tool)
        from llmfy.llmfy_core.tools.function_type_mapping import FUNCTION_TYPE_MAPPING

        tool_def = formatter.format_tool_function(metadata, FUNCTION_TYPE_MAPPING)
        assert tool_def["parameters"]["properties"]["items"]["type"] == "string"


class TestFormatToolMessage:
    def test_always_appends_a_new_message_never_merges(self, formatter):
        messages: list[Message] = []
        formatter.format_tool_message(
            messages, id="t1", tool_call_id="c1", name="fn", result="r1", request_call_id="req_1"
        )
        formatter.format_tool_message(
            messages, id="t2", tool_call_id="c2", name="fn2", result="r2", request_call_id="req_1"
        )
        # Same request_call_id, but OpenAI never merges (unlike Anthropic/Bedrock).
        assert len(messages) == 2
        assert messages[0].tool_results == ["r1"]
        assert messages[1].tool_results == ["r2"]

    def test_returns_the_same_list_object(self, formatter):
        messages: list[Message] = []
        result = formatter.format_tool_message(
            messages, id="t1", tool_call_id="c1", name="fn", result="r1"
        )
        assert result is messages
