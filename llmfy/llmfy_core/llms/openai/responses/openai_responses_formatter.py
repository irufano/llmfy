import inspect
import json
from typing import Any, Union

from llmfy.exception.llmfy_exception import LLMfyException
from llmfy.llmfy_core.llms.model_formatter import ModelFormatter
from llmfy.llmfy_core.messages.content_type import ContentType
from llmfy.llmfy_core.messages.message import Message
from llmfy.llmfy_core.messages.role import Role


class OpenAIResponsesFormatter(ModelFormatter):
    """OpenAIResponsesFormatter — formats messages/tools for OpenAI's Responses API.

    Reference: https://developers.openai.com/api/reference/responses/overview

    The Responses API's `input` array is flat — a tool call and its result are
    each their own top-level item (`function_call` / `function_call_output`),
    not nested inside a chat-style message the way Chat Completions nests
    `tool_calls` inside one assistant message. `format_message` must still
    return a single `dict` per the `ModelFormatter` contract, so a `Message`
    carrying N tool calls returns `{"__items__": [...]}`, a private convention
    that `OpenAIResponsesModel` unwraps into N separate flat `input` items when
    building the request (see its `__to_responses_input` helper). Everything
    else returns a single ready-to-use `input` item directly.

    MessageRequest:
    ```
    {
        "type": "message",
        "role": "user | assistant | system",
        "content": [{"type": "input_text", "text": "..."}],
    }
    ```

    ToolCallRequest (one item per call):
    ```
    {
        "type": "function_call",
        "call_id": "call_12345xyz",
        "name": "get_weather",
        "arguments": "{\"location\":\"Paris, France\"}"
    }
    ```

    ToolResultRequest:
    ```
    {
        "type": "function_call_output",
        "call_id": "call_12345xyz",
        "output": "..."
    }
    ```
    """

    def format_message(self, message: Message) -> dict:
        if message.tool_results:
            # in openai tool results only one then use first item.
            return {
                "type": "function_call_output",
                "call_id": message.tool_call_id,
                "output": message.tool_results[0],
            }

        if message.tool_calls:
            items = [
                {
                    "type": "function_call",
                    "call_id": tool_call.tool_call_id,
                    "name": tool_call.name,
                    "arguments": json.dumps(tool_call.arguments),
                }
                for tool_call in message.tool_calls
            ]
            return {"__items__": items}

        content_items: list[dict[str, Any]] = []
        # Prior assistant turns are replayed back as "output_text"; everything
        # else (system/user/developer) is sent as "input_text".
        text_type = "output_text" if message.role == Role.ASSISTANT else "input_text"

        if isinstance(message.content, str):
            content_items.append({"type": text_type, "text": message.content})
        elif isinstance(message.content, list):
            for c in message.content:
                if c.type == ContentType.TEXT:
                    content_items.append({"type": text_type, "text": c.value})

                elif c.type == ContentType.IMAGE:
                    content_items.append({"type": "input_image", "image_url": c.value})

                elif c.type == ContentType.DOCUMENT:
                    raise LLMfyException(
                        "OpenAI Responses `ContentType.DOCUMENT` input is not supported yet"
                    )

                elif c.type == ContentType.VIDEO:
                    raise LLMfyException(
                        "OpenAI Responses `ContentType.VIDEO` input is not supported yet"
                    )

        return {
            "type": "message",
            "role": message.role.value,
            "content": content_items,
        }

    def format_tool_function(
        self, func_metadata: dict, type_mapping: dict[Any, str]
    ) -> dict:
        """Formats a function into the Responses API's flat tool format.

        ```
        [{
            "type": "function",
            "name": "get_weather",
            "description": "Get current temperature for a given location.",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "City and country e.g. Bogotá, Colombia"
                    }
                },
                "required": [
                    "location"
                ],
                "additionalProperties": False
            },
            "strict": True
        }]
        ```

        Returned dict omits `"type": "function"` — `OpenAIResponsesModel` adds
        it (flat merge) when building the `tools` param, since this same shape
        is also handed to `Tool._get_tool_definition` for other uses.
        """
        metadata = func_metadata
        strict = True

        tool_def = {
            "name": metadata["name"],
            "description": metadata["description"],
            "strict": strict,
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
                "additionalProperties": False,
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
            tool_def["parameters"]["properties"][param_name] = {
                "type": param_type,
                "description": param_description
                + (" " if param_default else "")
                + param_default,
            }

            # Add required params
            if strict or param.default == inspect.Parameter.empty:
                tool_def["parameters"]["required"].append(param_name)

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
        messages.append(
            Message(
                id=id,
                role=Role.TOOL,
                tool_call_id=tool_call_id,
                name=name,
                request_call_id=request_call_id,
                tool_results=[result],
            )
        )
        return messages
