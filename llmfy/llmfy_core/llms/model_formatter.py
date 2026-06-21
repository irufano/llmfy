from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from llmfy.llmfy_core.messages.message import Message


class ModelFormatter(ABC):
    """ModelFormatter.

    Register all derivated intances from this class to:
        - `MessageTemp` class at `llmfy/chat/messages/message_temp.py`
        - `Tool` class at `llmfy/chat/tools/tool.py`

    Args:
        ABC (_type_): _description_
    """

    @abstractmethod
    def format_message(self, message: Message) -> dict:
        pass

    @abstractmethod
    def format_tool_function(
        self, func_metadata: Dict, type_mapping: dict[Any, str]
    ) -> dict:
        pass

    @abstractmethod
    def format_tool_message(
        self,
        messages: List[Message],
        id: str,
        tool_call_id: str,
        name: str,
        result: str,
        request_call_id: Optional[str] = None,
    ) -> List[Message]:
        pass
