import base64
import inspect
from typing import Any, Dict, List, Optional, Union

from llmfy.exception.llmfy_exception import LLMfyException
from llmfy.llmfy_core.messages.content_type import ContentType
from llmfy.llmfy_core.messages.message import Message
from llmfy.llmfy_core.messages.role import Role
from llmfy.llmfy_core.models.model_formatter import ModelFormatter


class GoogleAIFormatter(ModelFormatter):
    """GoogleAIFormatter.

    Formats messages to Google AI (Gemini) API format using dict-based
    representation compatible with the google-genai SDK.

    TextRequest:
    ```
    {
        "role": "user",
        "parts": [{"text": "Hello"}]
    }
    ```

    ToolCallRequest (assistant):
    ```
    {
        "role": "model",
        "parts": [
            {
                "function_call": {
                    "id": "fc_id",
                    "name": "get_weather",
                    "args": {"city": "Paris"}
                }
            }
        ]
    }
    ```

    ToolResultRequest:
    ```
    {
        "role": "user",
        "parts": [
            {
                "function_response": {
                    "id": "fc_id",
                    "name": "get_weather",
                    "response": {"result": "sunny"}
                }
            }
        ]
    }
    ```
    """

    def format_message(self, message: Message) -> dict:
        # Map llmfy roles to Google AI roles
        if message.role == Role.SYSTEM:
            # System messages are filtered out in the model and passed as system_instruction.
            # Return a placeholder that the model will strip from contents.
            role = "system"
        elif message.role == Role.ASSISTANT:
            role = "model"
        elif message.role == Role.TOOL:
            role = "user"
        else:
            role = message.role.value  # "user"

        # Tool result message (TOOL role)
        if message.tool_results:
            # tool_results contains pre-formatted function_response dicts
            # stored by format_tool_message
            return {"role": "user", "parts": message.tool_results}

        # Assistant message with tool calls
        if message.tool_calls:
            parts = [
                {
                    "function_call": {
                        "id": tool_call.tool_call_id,
                        "name": tool_call.name,
                        "args": tool_call.arguments,
                    }
                }
                for tool_call in message.tool_calls
            ]
            return {"role": "model", "parts": parts}

        # Text or multimodal content
        parts = []
        if isinstance(message.content, str):
            parts.append({"text": message.content})
        elif isinstance(message.content, list):
            for c in message.content:
                if c.type == ContentType.TEXT:
                    parts.append({"text": c.value})

                elif c.type == ContentType.IMAGE:
                    # Detect format: data URI, URL, or bytes
                    if isinstance(c.value, bytes):
                        parts.append(
                            {
                                "inline_data": {
                                    "mime_type": "image/jpeg",
                                    "data": base64.b64encode(c.value).decode("utf-8"),
                                }
                            }
                        )
                    elif isinstance(c.value, str) and c.value.startswith("data:"):
                        # data:<mime_type>;base64,<data>
                        header, b64data = c.value.split(",", 1)
                        mime_type = header.split(";")[0].split(":")[1]
                        parts.append(
                            {
                                "inline_data": {
                                    "mime_type": mime_type,
                                    "data": b64data,
                                }
                            }
                        )
                    elif isinstance(c.value, str) and c.value.startswith("http"):
                        parts.append(
                            {
                                "file_data": {
                                    "mime_type": "image/jpeg",
                                    "file_uri": c.value,
                                }
                            }
                        )
                    else:
                        raise LLMfyException(
                            "GoogleAI ContentType.IMAGE value must be bytes, a data URI string, or an http URL."
                        )

                elif c.type == ContentType.DOCUMENT:
                    if not c.filename:
                        raise LLMfyException(
                            "`filename` is required for content type DOCUMENT"
                        )
                    if isinstance(c.value, bytes):
                        parts.append(
                            {
                                "inline_data": {
                                    "mime_type": "application/pdf",
                                    "data": base64.b64encode(c.value).decode("utf-8"),
                                }
                            }
                        )
                    elif isinstance(c.value, str) and c.value.startswith("data:"):
                        header, b64data = c.value.split(",", 1)
                        parts.append(
                            {
                                "inline_data": {
                                    "mime_type": "application/pdf",
                                    "data": b64data,
                                }
                            }
                        )
                    elif isinstance(c.value, str) and c.value.startswith("http"):
                        parts.append(
                            {
                                "file_data": {
                                    "mime_type": "application/pdf",
                                    "file_uri": c.value,
                                }
                            }
                        )
                    else:
                        raise LLMfyException(
                            "GoogleAI ContentType.DOCUMENT value must be bytes, a data URI string, or an http URL."
                        )

                elif c.type == ContentType.VIDEO:
                    supported_formats = [
                        "mp4",
                        "mpeg",
                        "mov",
                        "avi",
                        "x-flv",
                        "mpg",
                        "webm",
                        "wmv",
                        "3gpp",
                    ]
                    # check format
                    if not c.format:
                        c.format = "mp4"  # default
                    if c.format not in supported_formats:
                        raise LLMfyException(f"`format` must in {supported_formats}.")

                    if isinstance(c.value, bytes):
                        # Inline video bytes — recommended for files < 20 MB.
                        # mime_type defaults to "video/mp4"; set `format` on
                        # the Content object to override (e.g. "video/webm").
                        mime_type = f"video/{c.format}"
                        parts.append(
                            {
                                "inline_data": {
                                    "mime_type": mime_type,
                                    "data": base64.b64encode(c.value).decode("utf-8"),
                                }
                            }
                        )
                    elif isinstance(c.value, str) and c.value.startswith("http"):
                        # HTTP URL or YouTube URL — use file_data (no size limit).
                        parts.append(
                            {
                                "file_data": {
                                    "mime_type": "video/mp4",
                                    "file_uri": c.value,
                                }
                            }
                        )
                    else:
                        raise LLMfyException(
                            "GoogleAI ContentType.VIDEO value must be bytes (< 20 MB) "
                            "or an http/YouTube URL."
                        )

        return {"role": role, "parts": parts}

    def format_tool_function(
        self, func_metadata: Dict, type_mapping: dict[Any, str]
    ) -> Dict:
        """Formats a function into Google AI FunctionDeclaration-compatible format.

        ```
        {
            "name": "get_weather",
            "description": "Get current temperature for a given location.",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "City and country"
                    }
                },
                "required": ["location"]
            }
        }
        ```
        The model wraps this in types.Tool(function_declarations=[...]).
        """
        metadata = func_metadata

        tool_def = {
            "name": metadata["name"],
            "description": metadata["description"],
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        }

        for param_name, param in metadata["parameters"].items():
            if param_name == "self":
                continue

            python_type = metadata["type_hints"].get(param_name, param.annotation)
            if hasattr(python_type, "__origin__") and python_type.__origin__ is Union:
                types = [t for t in python_type.__args__ if t is not type(None)]
                python_type = types[0] if len(types) == 1 else str

            param_type = type_mapping.get(python_type, "string")

            from llmfy.llmfy_core.tools.function_param_desc_extractor import (
                extract_param_desc,
            )

            docstring = metadata["docstring"]
            param_description = extract_param_desc(param_name, docstring)

            param_default = (
                f"(default: {param.default})"
                if param.default != inspect.Parameter.empty
                else ""
            )

            tool_def["parameters"]["properties"][param_name] = {
                "type": param_type,
                "description": param_description
                + (" " if param_default else "")
                + param_default,
            }

            if param.default == inspect.Parameter.empty:
                tool_def["parameters"]["required"].append(param_name)

        return tool_def

    def format_tool_message(
        self,
        messages: List[Message],
        id: str,
        tool_call_id: str,
        name: str,
        result: str,
        request_call_id: Optional[str] = None,
    ) -> List[Message]:
        """Stores a pre-formatted function_response part in tool_results.

        Google AI tool results must be role="user" with function_response parts.
        format_message() reads tool_results and outputs the correct structure.
        """
        function_response_part = {
            "function_response": {
                "id": tool_call_id,
                "name": name,
                "response": {"result": result},
            }
        }
        messages.append(
            Message(
                id=id,
                role=Role.TOOL,
                tool_results=[function_response_part],
                request_call_id=request_call_id,
            )
        )
        return messages
