"""Unit tests for llmfy/llmfy_core/llms/google/generate/googleai_generate_formatter.py."""

import base64

import pytest

from llmfy.exception.llmfy_exception import LLMfyException
from llmfy.llmfy_core.llms.google.generate.googleai_generate_formatter import (
    GoogleAIGenerateFormatter,
)
from llmfy.llmfy_core.messages.content import Content
from llmfy.llmfy_core.messages.content_type import ContentType
from llmfy.llmfy_core.messages.message import Message
from llmfy.llmfy_core.messages.role import Role
from llmfy.llmfy_core.messages.tool_call import ToolCall


@pytest.fixture
def formatter() -> GoogleAIGenerateFormatter:
    return GoogleAIGenerateFormatter()


class TestFormatMessage:
    def test_assistant_role_maps_to_model(self, formatter):
        msg = Message(role=Role.ASSISTANT, content="hi")
        result = formatter.format_message(msg)
        assert result["role"] == "model"

    def test_tool_role_maps_to_user_via_tool_results_branch(self, formatter):
        msg = Message(
            role=Role.TOOL, tool_call_id="c1", tool_results=[{"pre": "formatted"}]
        )
        result = formatter.format_message(msg)
        assert result == {"role": "user", "parts": [{"pre": "formatted"}]}

    def test_text_content(self, formatter):
        msg = Message(
            role=Role.USER, content=[Content(type=ContentType.TEXT, value="hi")]
        )
        result = formatter.format_message(msg)
        assert result["parts"] == [{"text": "hi"}]

    def test_image_bytes_base64_encoded_inline(self, formatter):
        raw = b"fake-bytes"
        msg = Message(
            role=Role.USER, content=[Content(type=ContentType.IMAGE, value=raw)]
        )
        result = formatter.format_message(msg)
        part = result["parts"][0]
        assert part["inline_data"]["mime_type"] == "image/jpeg"
        assert part["inline_data"]["data"] == base64.b64encode(raw).decode("utf-8")

    def test_image_data_uri_parses_mime_type_from_header(self, formatter):
        data_uri = "data:image/png;base64,QUJD"
        msg = Message(
            role=Role.USER, content=[Content(type=ContentType.IMAGE, value=data_uri)]
        )
        result = formatter.format_message(msg)
        part = result["parts"][0]
        assert part["inline_data"]["mime_type"] == "image/png"
        assert part["inline_data"]["data"] == "QUJD"

    def test_image_http_url_uses_file_data(self, formatter):
        msg = Message(
            role=Role.USER,
            content=[Content(type=ContentType.IMAGE, value="https://x/i.jpg")],
        )
        result = formatter.format_message(msg)
        assert result["parts"][0]["file_data"]["file_uri"] == "https://x/i.jpg"

    def test_image_invalid_value_raises(self, formatter):
        msg = Message(
            role=Role.USER,
            content=[Content(type=ContentType.IMAGE, value="ftp://nope")],
        )
        with pytest.raises(LLMfyException, match="bytes, a data URI"):
            formatter.format_message(msg)

    def test_document_requires_filename(self, formatter):
        msg = Message(
            role=Role.USER, content=[Content(type=ContentType.DOCUMENT, value=b"...")]
        )
        with pytest.raises(LLMfyException, match="filename"):
            formatter.format_message(msg)

    def test_document_data_uri_does_not_reparse_mime_type_from_header(self, formatter):
        # Documented inconsistency: unlike IMAGE, DOCUMENT hardcodes
        # application/pdf even for a data URI with a different declared type.
        data_uri = "data:text/plain;base64,QUJD"
        msg = Message(
            role=Role.USER,
            content=[
                Content(type=ContentType.DOCUMENT, value=data_uri, filename="x.pdf")
            ],
        )
        result = formatter.format_message(msg)
        assert result["parts"][0]["inline_data"]["mime_type"] == "application/pdf"

    def test_video_defaults_format_to_mp4_when_unset(self, formatter):
        msg = Message(
            role=Role.USER, content=[Content(type=ContentType.VIDEO, value=b"...")]
        )
        result = formatter.format_message(msg)
        assert result["parts"][0]["inline_data"]["mime_type"] == "video/mp4"

    def test_video_rejects_unsupported_format(self, formatter):
        msg = Message(
            role=Role.USER,
            content=[Content(type=ContentType.VIDEO, value=b"...", format="mkv")],
        )
        with pytest.raises(LLMfyException, match="must in"):
            formatter.format_message(msg)

    def test_video_http_url_hardcodes_mp4_mime_regardless_of_format(self, formatter):
        msg = Message(
            role=Role.USER,
            content=[
                Content(type=ContentType.VIDEO, value="https://x/v.webm", format="webm")
            ],
        )
        result = formatter.format_message(msg)
        assert result["parts"][0]["file_data"]["mime_type"] == "video/mp4"

    def test_tool_calls_formatted_as_function_call_parts(self, formatter):
        tool_call = ToolCall(
            tool_call_id="c1", request_call_id="r1", name="fn", arguments={"a": 1}
        )
        msg = Message(role=Role.ASSISTANT, tool_calls=[tool_call])
        result = formatter.format_message(msg)
        assert result == {
            "role": "model",
            "parts": [{"function_call": {"id": "c1", "name": "fn", "args": {"a": 1}}}],
        }


class TestFormatToolFunction:
    def test_default_params_are_not_required_unlike_openai_anthropic_bedrock(
        self, formatter
    ):
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
        assert tool_def["parameters"]["required"] == ["location"]


class TestFormatToolMessage:
    def test_stores_pre_formatted_function_response_part(self, formatter):
        messages: list[Message] = []
        formatter.format_tool_message(
            messages, id="t1", tool_call_id="c1", name="fn", result="sunny"
        )
        assert messages[0].tool_results[0] == {  # type: ignore
            "function_response": {
                "id": "c1",
                "name": "fn",
                "response": {"result": "sunny"},
            }
        }

    def test_never_merges_always_new_message(self, formatter):
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
        assert len(messages) == 2
