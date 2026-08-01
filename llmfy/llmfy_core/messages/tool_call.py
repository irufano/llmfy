from typing import Any

from pydantic import BaseModel


class ToolCall(BaseModel):
    """ToolCall Class."""

    tool_call_id: str
    request_call_id: str
    name: str
    arguments: dict[str, Any]
