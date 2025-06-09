import inspect
import re
from typing import Any, Dict, List, Union
from llmfy.exception.llmfy_exception import LLMfyException
from llmfy.llmfy_core.messages.content_type import ContentType
from llmfy.llmfy_core.messages.message import Message
from llmfy.llmfy_core.messages.role import Role
from llmfy.llmfy_core.models.model_formatter import ModelFormatter


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

        TextRequest:
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

        ImageRequest:
        ```
        {
            "role": "user",
            "content": [
                {
                    "image": {
                        "format": "png",
                        "source": {
                            "bytes": "image in bytes"
                        }
                    }
                }
            ]
        }
        # or
        {
            "role": "user",
            "content": [
                {
                    "image": {
                        "format": "png",
                        "source": {
                            "s3Location": {
                                "uri": "s3://amzn-s3-demo-bucket/myImage",
                                "bucketOwner": "111122223333"
                            }
                        }
                    }
                }
            ]
        }
        ```

        ToolRequest:
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
            if isinstance(message.content, str):
                # content is absolute text
                message_dict["content"] = [{"text": message.content}]
            if isinstance(message.content, List):
                # content can be text, image, document or video
                message_dict["content"] = []
                for c in message.content:
                    if c.type == ContentType.TEXT:
                        #  Content.value value is str.
                        message_dict["content"].append({"text": c.value})

                    if c.type == ContentType.IMAGE:
                        supported_formats = ["gif", "jpeg", "png", "webp"]
                        # check format
                        if not c.format:
                            raise LLMfyException("`format` is required for bedrock.")
                        if c.format not in supported_formats:
                            raise LLMfyException(
                                f"`format` must in {supported_formats}."
                            )

                        # check is use s3
                        if c.use_s3:
                            # Use s3
                            # check bwner if use s3
                            if not c.bucket_owner:
                                raise LLMfyException(
                                    "`bucket_owner` is required if use s3."
                                )

                            # use s3
                            # Content.value value is url to s3 image.
                            message_dict["content"].append(
                                {
                                    "image": {
                                        "format": c.format,
                                        "source": {
                                            "s3Location": {
                                                "uri": c.value,
                                                "bucketOwner": c.bucket_owner,
                                            }
                                        },
                                    }
                                }
                            )
                        else:
                            # Use bytes
                            #  Content.value value is str image bytes.
                            message_dict["content"].append(
                                {
                                    "image": {
                                        "format": c.format,
                                        "source": {"bytes": c.value},
                                    },
                                }
                            )

                    if c.type == ContentType.DOCUMENT:
                        # check filename
                        if not c.filename:
                            raise LLMfyException(
                                "`filename` is required for content type DOCUMENT"
                            )

                        # check is use s3
                        if c.use_s3:
                            # Use s3
                            # check bwner if use s3
                            if not c.bucket_owner:
                                raise LLMfyException(
                                    "`bucket_owner` is required if use s3."
                                )

                            # use s3
                            # Content.value value is url to s3 image.
                            message_dict["content"].append(
                                {
                                    "document": {
                                        "format": "pdf",
                                        "name": c.filename,
                                        "source": {
                                            "s3Location": {
                                                "uri": c.value,
                                                "bucketOwner": c.bucket_owner,
                                            }
                                        },
                                    }
                                }
                            )
                        else:
                            # Use bytes
                            # Content.value value is str pdf bytes.
                            message_dict["content"].append(
                                {
                                    "document": {
                                        "format": "pdf",
                                        "name": c.filename,
                                        "source": {"bytes": c.value},
                                    },
                                }
                            )

                    if c.type == ContentType.VIDEO:
                        supported_formats = [
                            "wmv",
                            "mpg",
                            "mpeg",
                            "three_gp",
                            "flv",
                            "mp4",
                            "mov",
                            "mkv",
                            "webm",
                        ]
                        # check format
                        if not c.format:
                            raise LLMfyException("`format` is required for bedrock.")
                        if c.format not in supported_formats:
                            raise LLMfyException(
                                f"`format` must in {supported_formats}."
                            )

                        # check is use s3
                        if c.use_s3:
                            # Use s3
                            # check bwner if use s3
                            if not c.bucket_owner:
                                raise LLMfyException(
                                    "`bucket_owner` is required if use s3."
                                )

                            # use s3
                            # Content.value value is url to s3 video.
                            message_dict["content"].append(
                                {
                                    "video": {
                                        "format": c.format,
                                        "source": {
                                            "s3Location": {
                                                "uri": c.value,
                                                "bucketOwner": c.bucket_owner,
                                            }
                                        },
                                    }
                                }
                            )
                        else:
                            # Use bytes
                            #  Content.value value is str video bytes.
                            message_dict["content"].append(
                                {
                                    "video": {
                                        "format": c.format,
                                        "source": {"bytes": c.value},
                                    },
                                }
                            )

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
                    ucket_o                    "type": "string",
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
        """
        There are 2 kind tool message provided in bedrock,
        - if all tool request in one item list, the tool message also must in one item list, see sample : `app/llmfy/messages/sample_v1_bedrock_messages.json`
        - if tool request is separated one by one, the tool message also must provided one by one, see sample : `app/llmfy/messages/sample_v2_bedrock_messages.json`
        """

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
            # V1
            # update
            if bedrock_message.tool_results:
                bedrock_message.tool_results.append(tool_result)
        else:
            # V2
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
