import uuid
from typing import Any, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from llmfy.llmfy_core.messages.content import Content
from llmfy.llmfy_core.messages.role import Role
from llmfy.llmfy_core.messages.tool_call import ToolCall


class Message(BaseModel):
    """Message class for input to the LLM models.

    Args:
        id (str): Id message default UUIDv4.
        role (Role): Message role.
        content (Optional[str] | Optional[List[Content]]): Use str if only using text, but if use image and text use List[Content].
        name (Optional[str]): Message name.
        tool_calls (Optional[List[ToolCall]]): [`assistant` role ONLY] Tool call list.
        tool_call_id (Optional[str]): [`tool` role ONLY] Tool call id.
        tool_results (Optional[List[Any]]): [`tool` role ONLY] Tool call results.
        request_call_id (Optional[str]): [`tool` role ONLY] Tool call id request.
    """

    model_config = ConfigDict(extra="forbid")

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))

    role: Role
    """Message role [SYSTEM, USER, ASSISTANT, TOOL]"""

    content: Optional[str] | Optional[List[Content]] = None
    """Use str if only using text, but if use image and text use List[Content]."""

    name: Optional[str] = None
    """Message name"""

    tool_calls: Optional[List[ToolCall]] = None  # For Message with `assistant` role
    """[`assistant` role ONLY] Tool call list."""

    tool_call_id: Optional[str] = None  # For Message with `tool` role
    """[`tool` role ONLY] Tool call id."""

    tool_results: Optional[List[Any]] = None  # For Message with `tool` role
    """[`tool` role ONLY] Tool call results."""

    request_call_id: Optional[str] = None  # For Message with `tool` role
    """[`tool` role ONLY] Tool call id request."""

    # def __init__(self, **kwargs):
    def model_post_init(self, __context) -> None:

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
