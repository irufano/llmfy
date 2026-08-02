import base64
import inspect
from typing import Any, Union

from llmfy.exception.llmfy_exception import LLMfyException
from llmfy.llmfy_core.llms.model_formatter import ModelFormatter
from llmfy.llmfy_core.messages.content_type import ContentType
from llmfy.llmfy_core.messages.message import Message
from llmfy.llmfy_core.messages.role import Role


class AnthropicMessagesFormatter(ModelFormatter):
    """AnthropicMessagesFormatter — formats internal Message objects into the
    native Anthropic Messages API wire shape.

    Note: the native Messages API has no top-level `system` role in the
    `messages` array (system is a separate request parameter) and no
    per-message `name` field (unlike Bedrock/OpenAI). This formatter still
    emits a `{"role": "system", ...}` entry for SYSTEM-role messages — exactly
    like BedrockConverseFormatter does — because `AnthropicMessagesModel.generate()` /
    `generate_stream()` strip it out of `messages` and pass it as the
    top-level `system` param before calling the SDK.
    """

    def format_message(self, message: Message) -> dict:
        # Tool-result messages map to Anthropic's "user" role, matching how
        # Bedrock's Converse API treats tool results.
        role = message.role.value if message.role.value != "tool" else "user"
        message_dict: dict[str, Any] = {"role": role}

        if message.content and not message.tool_results and not message.tool_calls:
            if isinstance(message.content, str):
                message_dict["content"] = [{"type": "text", "text": message.content}]
            if isinstance(message.content, list):
                message_dict["content"] = []
                for c in message.content:
                    if c.type == ContentType.TEXT:
                        message_dict["content"].append({"type": "text", "text": c.value})

                    elif c.type == ContentType.IMAGE:
                        supported_formats = ["jpeg", "png", "gif", "webp"]
                        if not c.format:
                            raise LLMfyException(
                                "`format` is required for anthropic image content."
                            )
                        if c.format not in supported_formats:
                            raise LLMfyException(f"`format` must be in {supported_formats}.")
                        if c.use_s3:
                            raise LLMfyException(
                                "`use_s3` is a Bedrock-only field and is not supported by "
                                "the native Anthropic provider. Use a base64 `Content.value` "
                                "instead."
                            )
                        data = c.value
                        if isinstance(data, bytes):
                            data = base64.b64encode(data).decode("utf-8")
                        message_dict["content"].append(
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": f"image/{c.format}",
                                    "data": data,
                                },
                            }
                        )

                    elif c.type == ContentType.DOCUMENT:
                        if not c.filename:
                            raise LLMfyException(
                                "`filename` is required for content type DOCUMENT"
                            )
                        if c.use_s3:
                            raise LLMfyException(
                                "`use_s3` is a Bedrock-only field and is not supported by "
                                "the native Anthropic provider."
                            )
                        data = c.value
                        if isinstance(data, bytes):
                            data = base64.b64encode(data).decode("utf-8")
                        message_dict["content"].append(
                            {
                                "type": "document",
                                "source": {
                                    "type": "base64",
                                    "media_type": "application/pdf",
                                    "data": data,
                                },
                                "title": c.filename,
                            }
                        )

                    elif c.type == ContentType.VIDEO:
                        raise LLMfyException(
                            "The Anthropic Messages API does not support video content."
                        )

        if message.tool_results:
            message_dict["content"] = message.tool_results

        if message.tool_calls:
            message_dict["content"] = [
                {
                    "type": "tool_use",
                    "id": tool_call.tool_call_id,
                    "name": tool_call.name,
                    "input": tool_call.arguments,
                }
                for tool_call in message.tool_calls
            ]

        # Note: no `name` field — the native Messages API has no per-message
        # `name` (unlike Bedrock/OpenAI). message.name is intentionally
        # dropped here.

        return message_dict

    def format_tool_function(
        self, func_metadata: dict, type_mapping: dict[Any, str]
    ) -> dict:
        """Formats a function into Anthropic's tool format.

        ```
        {
            "name": "get_current_weather",
            "description": "...",
            "input_schema": {
                "type": "object",
                "properties": {
                    "location": {"type": "string", "description": "..."},
                    "unit": {"type": "string", "description": "... (default: celsius)"}
                },
                "required": ["location", "unit"]
            }
        }
        ```
        """
        metadata = func_metadata

        tool_def: dict[str, Any] = {
            "name": metadata["name"],
            "description": metadata["description"] or metadata["name"],
            "input_schema": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        }

        for param_name, param in metadata["parameters"].items():
            if param_name == "self":  # Skip 'self' for methods
                continue

            python_type = metadata["type_hints"].get(param_name, param.annotation)
            if hasattr(python_type, "__origin__") and python_type.__origin__ is Union:
                # Extract non-None types from Union
                types = [t for t in python_type.__args__ if t is not type(None)]
                python_type = types[0] if len(types) == 1 else str

            param_type = type_mapping.get(python_type, "string")

            # Extract parameter description
            from llmfy.llmfy_core.tools.function_param_desc_extractor import (
                extract_param_desc,
            )

            docstring = metadata["docstring"]
            param_description = extract_param_desc(param_name, docstring)

            # Extract default value
            param_default = (
                f"(default: {param.default})"
                if param.default != inspect.Parameter.empty
                else ""
            )

            # Add parameter details
            tool_def["input_schema"]["properties"][param_name] = {
                "type": param_type,
                "description": param_description
                + (" " if param_default else "")
                + param_default,
            }

            # Add required params
            tool_def["input_schema"]["required"].append(param_name)

        return tool_def

    def format_tool_message(
        self,
        messages: list[Message],
        id: str,
        tool_call_id: str,
        name: str,
        result: str,
        request_call_id: str | None = None,
    ) -> list[Message]:
        """Builds a native Anthropic `tool_result` content block.

        ```
        {
            "type": "tool_result",
            "tool_use_id": "toolu_01...",
            "content": "<result string>"
        }
        ```

        Note the field name is `tool_use_id` (NOT `id`). `is_error` is not
        supported in v1 — `ModelFormatter.format_tool_message`'s abstract
        signature has no such parameter, and none of the other formatters
        support it either.

        Batches multiple tool results from the same assistant turn into a
        single Message (role=TOOL), identically to BedrockConverseFormatter.
        """
        tool_result = {
            "type": "tool_result",
            "tool_use_id": tool_call_id,
            "content": result,
        }

        anthropic_message = next(
            (
                msg
                for msg in messages
                if msg.role == Role.TOOL
                and msg.tool_results
                and msg.request_call_id == request_call_id
            ),
            None,
        )

        if anthropic_message:
            if anthropic_message.tool_results:
                anthropic_message.tool_results.append(tool_result)
        else:
            messages.append(
                Message(
                    id=id,
                    role=Role.TOOL,
                    tool_results=[tool_result],
                    request_call_id=request_call_id,
                )
            )
        return messages
