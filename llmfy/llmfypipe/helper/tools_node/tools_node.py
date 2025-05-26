from typing import List

from llmfy.llmfy_core.messages.message import Message
from llmfy.llmfy_core.messages.role import Role
from llmfy.llmfy_core.tools.tool_registry import ToolRegistry


def tools_node(messages: List[Message], registry: ToolRegistry):
    new_messages = messages
    last_message = new_messages[-1]
    if last_message.tool_calls:
        for tool_call in last_message.tool_calls:
            result = registry.execute_tool(
                name=tool_call.name, arguments=tool_call.arguments
            )
            new_messages.append(
                Message(
                    role=Role.TOOL,
                    request_call_id=tool_call.request_call_id,
                    tool_call_id=tool_call.tool_call_id,
                    tool_results=[str(result)],
                    name=tool_call.name,
                )
            )
    return new_messages
