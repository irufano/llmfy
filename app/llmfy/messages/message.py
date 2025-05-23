import uuid
from typing import Any, List, Optional

from pydantic import BaseModel, ConfigDict, Field


from app.llmfy.messages.role import Role
from app.llmfy.messages.tool_call import ToolCall


class Message(BaseModel):
    """Message class for input to the LLM models."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    role: Role
    content: Optional[str] = None
    name: Optional[str] = None
    tool_calls: Optional[List[ToolCall]] = None  # For Message with `assistant` role
    tool_call_id: Optional[str] = None  # For Message with `tool` role
    tool_results: Optional[List[Any]] = None  # For Message with `tool` role
    request_call_id: Optional[str] = None  # For Message with `tool` role

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Ensure tool_results is only used when role is "tool"
        if self.tool_results is not None and self.role != Role.TOOL:
            raise ValueError("tool_results can only be set when role is 'tool'.")

        # Ensure expect tool_results used when role is "tool"
        if not self.tool_results and self.role == Role.TOOL:
            raise ValueError("Expected tool_results when role is 'tool'.")

        # Ensure tool_call_id is only used when role is "tool"
        if self.tool_call_id is not None and self.role != Role.TOOL:
            raise ValueError("tool_call_id can only be set when role is 'tool'.")

        # Ensure tool_calls is only used when role is "assistant"
        if self.tool_calls is not None and self.role != Role.ASSISTANT:
            raise ValueError("tool_calls can only be set when role is 'assistant'.")
