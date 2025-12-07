from copy import deepcopy
from typing import Any, Generator, List

from llmfy.flow_engine.stream.tool_node_stream_response import (
    ToolNodeStreamResponse,
    ToolNodeStreamType,
)
from llmfy.llmfy_core.messages.message import Message
from llmfy.llmfy_core.messages.role import Role
from llmfy.llmfy_core.tools.tool_registry import ToolRegistry


def tools_node(messages: List[Message], registry: ToolRegistry) -> List[Message]:
    """Tools Node

    Args:
        messages (List[Message]): List message
        registry (ToolRegistry): Tool registry

    Returns:
        Tool results message
    """
    new_messages = deepcopy(messages)
    last_message = new_messages[-1]
    tool_results: List[Message] = []
    if last_message.tool_calls:
        for tool_call in last_message.tool_calls:
            result = registry.execute_tool(
                name=tool_call.name, arguments=tool_call.arguments
            )
            tool_results.append(
                Message(
                    role=Role.TOOL,
                    request_call_id=tool_call.request_call_id,
                    tool_call_id=tool_call.tool_call_id,
                    tool_results=[str(result)],
                    name=tool_call.name,
                )
            )
    return tool_results


def tools_stream_node(messages: List[Message], registry: ToolRegistry) -> Generator[ToolNodeStreamResponse, Any, None]:
    """Tools Stream Node

    Args:
        messages (List[Message]): List message
        registry (ToolRegistry): Tool registry

    Yields:
        Tool results message
    """
    new_messages = deepcopy(messages)
    last_message = new_messages[-1]
    response = ToolNodeStreamResponse()

    if last_message.tool_calls:
        for tool_call in last_message.tool_calls:
            # Executing
            response.type = ToolNodeStreamType.EXECUTING
            response.name = tool_call.name
            response.arguments = tool_call.arguments
            response.result = None
            yield response

            result = registry.execute_tool(
                name=tool_call.name, arguments=tool_call.arguments
            )
            tool_result = Message(
                role=Role.TOOL,
                request_call_id=tool_call.request_call_id,
                tool_call_id=tool_call.tool_call_id,
                tool_results=[str(result)],
                name=tool_call.name,
            )

            # Result
            response.type = ToolNodeStreamType.RESULT
            response.name = tool_call.name
            response.arguments = tool_call.arguments
            response.result = tool_result
            yield response
