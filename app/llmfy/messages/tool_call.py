from typing import Any, Dict
from pydantic import BaseModel


class ToolCall(BaseModel):
    """ToolCall Class."""

    tool_call_id: str
    request_call_id: str
    name: str
    arguments: Dict[str, Any]
