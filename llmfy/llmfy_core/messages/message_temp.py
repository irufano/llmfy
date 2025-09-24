from typing import Any, Dict, List, Optional

from llmfy.exception.llmfy_exception import LLMfyException
from llmfy.llmfy_core.messages.content import Content
from llmfy.llmfy_core.messages.message import Message
from llmfy.llmfy_core.messages.role import Role
from llmfy.llmfy_core.messages.tool_call import ToolCall
from llmfy.llmfy_core.models.bedrock.bedrock_formatter import BedrockFormatter
from llmfy.llmfy_core.models.model_formatter import ModelFormatter
from llmfy.llmfy_core.models.openai.openai_formatter import OpenAIFormatter
from llmfy.llmfy_core.service_provider import ServiceProvider


class MessageTemp:
    """MessageTemp class. History only per request, not saved to memory."""

    # Register formatter
    _formatters: Dict[ServiceProvider, ModelFormatter] = {
        ServiceProvider.OPENAI: OpenAIFormatter(),
        ServiceProvider.BEDROCK: BedrockFormatter(),
    }

    def __init__(self):
        self.messages: List[Message] = []

    def add_system_message(self, content: str) -> None:
        self.messages.insert(0, Message(role=Role.SYSTEM, content=content))

    def add_user_message(
        self, id: str, content: Optional[str] | Optional[List[Content]]
    ) -> None:
        self.messages.append(Message(id=id, role=Role.USER, content=content))

    def add_assistant_message(
        self,
        id: str,
        content: Optional[str] | Optional[List[Content]] = None,
        tool_calls: Optional[List[ToolCall]] = None,
    ) -> None:
        # Update request call id by parent
        if tool_calls:
            for tool_call in tool_calls:
                tool_call.request_call_id = id

        self.messages.append(
            Message(id=id, role=Role.ASSISTANT, content=content, tool_calls=tool_calls)
        )

    def add_tool_message(
        self,
        id: str,
        tool_call_id: str,
        name: str,
        result: str,
        provider: ServiceProvider,
        request_call_id: Optional[str] = None,
    ) -> None:
        formatter = self._formatters.get(provider)
        if not formatter:
            raise LLMfyException(f"Unsupported model provider: {provider}")

        formatter.format_tool_message(
            messages=self.messages,
            id=id,
            tool_call_id=tool_call_id,
            name=name,
            request_call_id=request_call_id,
            result=result,
        )

    def get_messages(self, provider: ServiceProvider) -> List[Dict[str, Any]]:
        formatter = self._formatters.get(provider)
        if not formatter:
            raise LLMfyException(f"Unsupported model provider: {provider}")
        return [formatter.format_message(msg) for msg in self.messages]

    def get_instance_messages(self) -> List[Message]:
        # return [msg for msg in self.messages if msg.role != Role.SYSTEM]
        return self.messages

    def clear(self) -> None:
        system_message = next(
            (msg for msg in self.messages if msg.role == Role.SYSTEM), None
        )
        self.messages.clear()
        if system_message:
            self.messages.append(system_message)
