import json
import inspect
import re

from typing import Any, Dict, List, Union
from app.llmfy.messages.message import Message
from app.llmfy.messages.role import Role
from app.llmfy.models.model_formatter import ModelFormatter


class OpenAIFormatter(ModelFormatter):
    """OpenAIFormatter

    BasicResponse:
    ```
    {
        role: "developer | user | assistant",
        content: "Write a haiku about recursion in programming.",
    }
    ```

    ToolRequestResponse:
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
    """

    def format_message(self, message: Message) -> dict:
        message_dict: Dict[str, Any] = {
            "role": message.role.value,
        }

        if message.content and not message.tool_results and not message.tool_calls:
            message_dict["content"] = message.content

        if message.tool_results:
            # in openai tool results only one then use first item.
            message_dict["content"] = message.tool_results[0]

        if message.content is not None:
            message_dict["content"] = message.content

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
