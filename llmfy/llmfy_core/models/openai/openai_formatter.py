import json
import inspect
import re

from typing import Any, Dict, List, Union
from llmfy.exception.llmfy_exception import LLMfyException
from llmfy.llmfy_core.messages.content_type import ContentType
from llmfy.llmfy_core.messages.message import Message
from llmfy.llmfy_core.messages.role import Role
from llmfy.llmfy_core.models.model_formatter import ModelFormatter


class OpenAIFormatter(ModelFormatter):
    """OpenAIFormatter

    BasicRequest:
    ```
    {
        role: "developer | user | assistant",
        content: "Write a haiku about recursion in programming.",
    }
    ```

    ToolRequest:
    ```
    [{
        "id": "call_12345xyz",
        "type": "function",
        "function": {
            "name": "get_weather",
            "arguments": "{\"location\":\"Paris, France\"}"
        }
    }]
    ```

    ImageRequest:
    {
        "role": "user",
        "content": [
            {"type": "text", "text": "What's in this image?"},
            {
                "type": "image_url",
                "image_url": {
                    "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/dd/Gfp-wisconsin-madison-the-nature-boardwalk.jpg/2560px-Gfp-wisconsin-madison-the-nature-boardwalk.jpg",
                }
            },
        ],
    }

    # or

    {
        "role": "user",
        "content": [
            {"type": "text", "text": "What's in this image?"},
            {
                "type": "image_url",
                "image_url": {
                    "url": "base64 encoded image...",
                }
            },
        ],
    }
    ```
    """

    def format_message(self, message: Message) -> dict:
        message_dict: Dict[str, Any] = {
            "role": message.role.value,
        }

        if message.content and not message.tool_results and not message.tool_calls:
            if isinstance(message.content, str):
                # content is absolute text
                message_dict["content"] = message.content
            if isinstance(message.content, List):
                # content can be text or image
                message_dict["content"] = []
                for c in message.content:

                    if c.type == ContentType.TEXT:
                        # Content.value value is str.
                        message_dict["content"].append(
                            {
                                "type": "text",
                                "text": c.value,
                            }
                        )

                    if c.type == ContentType.IMAGE:
                        # Content.value value is str url or base64.
                        message_dict["content"].append(
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": c.value,
                                },
                            }
                        )

                    if c.type == ContentType.DOCUMENT:
                        # check filename
                        if not c.filename:
                            raise LLMfyException(
                                "`filename` is required for content type DOCUMENT"
                            )

                        # Content.value value is base64.
                        message_dict["content"].append(
                            {
                                "type": "file",
                                "file": {
                                    "filename": c.filename,
                                    "file_data": c.value,
                                },
                            },
                        )

                    if c.type == ContentType.VIDEO:
                        raise LLMfyException(
                            "OpenAI `ContentType.VIDEO` input is not supported yet"
                        )

        if message.tool_results:
            # in openai tool results only one then use first item.
            message_dict["content"] = message.tool_results[0]

        if message.tool_calls:
            message_dict["tool_calls"] = [
                {
                    "id": tool_call.tool_call_id,
                    "type": "function",
                    "function": {
                        "name": tool_call.name,
                        "arguments": json.dumps(tool_call.arguments),
                    },
                }
                for tool_call in message.tool_calls
            ]

        if message.tool_call_id:
            message_dict["tool_call_id"] = message.tool_call_id

        if message.name:
            message_dict["name"] = message.name

        return message_dict

    def format_tool_function(
        self, func_metadata: Dict, type_mapping: dict[Any, str]
    ) -> Dict:
        """Formats a function into OpenAI's tool format.

        ```
        [{
            "type": "function",
            "function": {
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
            }
        }]
        ```

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
            param_description = ""
            param_patterns = [
                f"{param_name} (",  # Google style
                f"{param_name}:",  # Sphinx style
                f":param {param_name}:",  # reST style
            ]

            for pattern in param_patterns:
                if pattern in metadata["docstring"]:
                    start = metadata["docstring"].find(pattern) + len(pattern)
                    end = metadata["docstring"].find("\n", start)
                    param_description = metadata["docstring"][start:end].strip()
                    if "):" in param_description:
                        match = re.search(r"\):\s*(.*)", param_description)
                        if match:
                            param_description = match.group(1)
                    break

            # Extract default value
            param_default = (
                f" (default: {param.default})"
                if param.default != inspect.Parameter.empty
                else ""
            )

            # Add parameter details
            tool_def["parameters"]["properties"][param_name] = {
                "type": param_type,
                "description": param_description
                + (" " if param_description else "")
                + param_default,
            }

            # Add required params
            if strict or param.default == inspect.Parameter.empty:
                tool_def["parameters"]["required"].append(param_name)

        return tool_def

    def format_tool_message(
        self,
        messages: List[Message],
        id: str,
        tool_call_id: str,
        name: str,
        result: str,
        request_call_id: str | None = None,
    ) -> List[Message]:
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
