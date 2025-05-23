import inspect
import re
from typing import Any, Dict, List, Union
from app.llmfy.messages.message import Message
from app.llmfy.messages.role import Role
from app.llmfy.models.model_formatter import ModelFormatter


class BedrockFormatter(ModelFormatter):
    """BedrockFormatter.

    Args:
        id (str): _description_
        role (Role): _description_
        content (Optional[str], optional): _description_. Defaults to None.
        tool_calls (Optional[List[ToolCall]], optional): _description_. Defaults to None.
        tool_call_id (Optional[str], optional): _description_. Defaults to None.
        name (Optional[str], optional): _description_. Defaults to None.

    Returns:
        dict: _description_
    """

    def format_message(self, message: Message) -> dict:
        """Formats message into Bedrock's message format.

        BasicResponse:
        ```
        {
            "role": "user | assistant",
            "content": [
                {
                    "text": "string"
                }
            ]
        }
        ```

        ToolRequestResponse:
        ```
        {
            "role": "assistant",
            "content": [
                {
                    "toolUse": {
                        "toolUseId": "tooluse_kZJMlvQmRJ6eAyJE5GIl7Q",
                        "name": "top_song",
                        "input": {
                            "sign": "WZPZ"
                        }
                    }
                }
            ]
        }
        ```

        ToolResultRequest:
        ```
        {
            "role": "user",
            "content": [
                {
                    "toolResult": {
                        "toolUseId": "tooluse_kZJMlvQmRJ6eAyJE5GIl7Q",
                        "content": [
                            {
                                "json": {
                                    "song": "Elemental Hotel",
                                    "artist": "8 Storey Hike"
                                }
                            }
                        ]
                    }
                }
            ]
        }
        ```
        """
        # for tool result (tool message) in bedrock role become `user`
        role = message.role.value if message.role.value != "tool" else "user"
        message_dict: Dict[str, Any] = {
            "role": role,
        }

        if message.content and not message.tool_results and not message.tool_calls:
            message_dict["content"] = [{"text": message.content}]

        if message.tool_results:
            message_dict["content"] = message.tool_results

        if message.tool_calls:
            message_dict["content"] = [
                {
                    "toolUse": {
                        "toolUseId": tool_call.tool_call_id,
                        "name": tool_call.name,
                        "input": tool_call.arguments,
                    }
                }
                for tool_call in message.tool_calls
            ]

        if message.name and not message.role.value == "tool":
            message_dict["name"] = message.name

        return message_dict

    def format_tool_function(
        self, func_metadata: Dict, type_mapping: dict[Any, str]
    ) -> Dict:
        """Formats a function into Bedrock's tool format.

        ```
        {
            "tools": [
                {
                    "toolSpec": {
                        "name": "get_current_weather",
                        "description": "",
                        "inputSchema": {
                            "json": {
                                "type": "object",
                                "properties": {
                                    "location": {
                                        "type": "string",
                                        "description": ""
                                    },
                                    "unit": {
                                        "type": "string",
                                        "description": " (default: celsius)"
                                    }
                                },
                                "required": [
                                    "location",
                                    "unit"
                                ]
                            }
                        }
                    }
                }
            ]
        }
        ```
        """
        metadata = func_metadata

        tool_def = {
            "name": metadata["name"],
            "description": metadata["description"] or metadata["name"],
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {},
                    "required": [],
                }
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
                f"(default: {param.default})"
                if param.default != inspect.Parameter.empty
                else ""
            )

            # Add parameter details
            tool_def["inputSchema"]["json"]["properties"][param_name] = {
                "type": param_type,
                "description": param_description
                + (" " if param_description else "")
                + param_default,
            }

            # Add required params
            tool_def["inputSchema"]["json"]["required"].append(param_name)

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
        tool_result = {
            "toolResult": {
                "toolUseId": tool_call_id,
                "content": [{"json": {"result": result}}],
            }
        }

        # Find existing Bedrock tool response message
        bedrock_message = next(
            (
                msg
                for msg in messages
                if msg.role == Role.TOOL
                and msg.tool_results
                and msg.request_call_id == request_call_id
            ),
            None,
        )

        if bedrock_message:
            # update
            if bedrock_message.tool_results:
                bedrock_message.tool_results.append(tool_result)
        else:
            # add new
            messages.append(
                Message(
                    id=id,
                    role=Role.TOOL,
                    tool_results=[tool_result],
                    request_call_id=request_call_id,
                )
            )
        return messages
