"""Unit tests for llmfy/llmfy_core/llms/bedrock/converse/bedrock_converse_formatter.py."""

import pytest

from llmfy.exception.llmfy_exception import LLMfyException
from llmfy.llmfy_core.llms.bedrock.converse.bedrock_converse_formatter import (
    BedrockConverseFormatter,
)
from llmfy.llmfy_core.messages.content import Content
from llmfy.llmfy_core.messages.content_type import ContentType
from llmfy.llmfy_core.messages.message import Message
from llmfy.llmfy_core.messages.role import Role
from llmfy.llmfy_core.messages.tool_call import ToolCall


@pytest.fixture
def formatter() -> BedrockConverseFormatter:
    return BedrockConverseFormatter()


class TestFormatMessage:
    def test_tool_role_maps_to_user(self, formatter):
        msg = Message(role=Role.TOOL, tool_call_id="c1", tool_results=["r"])
        result = formatter.format_message(msg)
        assert result["role"] == "user"

    def test_text_content_block(self, formatter):
        msg = Message(role=Role.USER, content="hi")
        result = formatter.format_message(msg)
        assert result["content"] == [{"text": "hi"}]

    def test_image_bytes_source(self, formatter):
        msg = Message(
            role=Role.USER,
            content=[Content(type=ContentType.IMAGE, value=b"...", format="png")],
        )
        result = formatter.format_message(msg)
        assert result["content"] == [
            {"image": {"format": "png", "source": {"bytes": b"..."}}}
        ]

    def test_image_requires_bucket_owner_when_use_s3(self, formatter):
        msg = Message(
            role=Role.USER,
            content=[
                Content(
                    type=ContentType.IMAGE, value="s3://x", format="png", use_s3=True
                )
            ],
        )
        with pytest.raises(LLMfyException, match="bucket_owner"):
            formatter.format_message(msg)

    def test_image_s3_source(self, formatter):
        msg = Message(
            role=Role.USER,
            content=[
                Content(
                    type=ContentType.IMAGE,
                    value="s3://bucket/key",
                    format="png",
                    use_s3=True,
                    bucket_owner="111122223333",
                )
            ],
        )
        result = formatter.format_message(msg)
        assert result["content"][0]["image"]["source"]["s3Location"] == {
            "uri": "s3://bucket/key",
            "bucketOwner": "111122223333",
        }

    def test_image_rejects_unsupported_format(self, formatter):
        msg = Message(
            role=Role.USER,
            content=[Content(type=ContentType.IMAGE, value=b"...", format="tiff")],
        )
        with pytest.raises(LLMfyException, match="must in"):
            formatter.format_message(msg)

    def test_video_supports_bedrock_specific_formats(self, formatter):
        msg = Message(
            role=Role.USER,
            content=[Content(type=ContentType.VIDEO, value=b"...", format="mkv")],
        )
        result = formatter.format_message(msg)
        assert result["content"] == [
            {"video": {"format": "mkv", "source": {"bytes": b"..."}}}
        ]

    def test_document_bytes_source(self, formatter):
        msg = Message(
            role=Role.USER,
            content=[
                Content(
                    type=ContentType.DOCUMENT, value=b"pdf-bytes", filename="doc.pdf"
                )
            ],
        )
        result = formatter.format_message(msg)
        assert result["content"][0]["document"]["format"] == "pdf"
        assert result["content"][0]["document"]["name"] == "doc.pdf"

    def test_tool_calls_formatted_as_tool_use(self, formatter):
        tool_call = ToolCall(
            tool_call_id="c1", request_call_id="r1", name="fn", arguments={"a": 1}
        )
        msg = Message(role=Role.ASSISTANT, tool_calls=[tool_call])
        result = formatter.format_message(msg)
        assert result["content"] == [
            {"toolUse": {"toolUseId": "c1", "name": "fn", "input": {"a": 1}}}
        ]

    def test_name_field_dropped_for_tool_role(self, formatter):
        msg = Message(
            role=Role.TOOL, tool_call_id="c1", tool_results=["r"], name="ignored"
        )
        result = formatter.format_message(msg)
        assert "name" not in result

    def test_name_field_kept_for_non_tool_role(self, formatter):
        msg = Message(role=Role.USER, content="hi", name="kept")
        result = formatter.format_message(msg)
        assert result["name"] == "kept"


class TestFormatToolFunction:
    def test_every_param_unconditionally_required(self, formatter):
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
        assert set(tool_def["inputSchema"]["json"]["required"]) == {"location", "unit"}


class TestFormatToolMessage:
    def test_merges_parallel_tool_results_v1_style(self, formatter):
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
        assert len(messages) == 1
        assert len(messages[0].tool_results) == 2  # type: ignore

    def test_result_shape_uses_tool_use_id_and_json_content(self, formatter):
        messages: list[Message] = []
        formatter.format_tool_message(
            messages, id="t1", tool_call_id="c1", name="fn", result="sunny"
        )
        assert messages[0].tool_results[0] == {  # type: ignore
            "toolResult": {
                "toolUseId": "c1",
                "content": [{"json": {"result": "sunny"}}],
            }
        }
