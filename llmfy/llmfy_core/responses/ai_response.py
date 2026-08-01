
from pydantic import BaseModel, ConfigDict

from llmfy.llmfy_core.messages.tool_call import ToolCall


class AIResponse(BaseModel):
    """AIResponse Class"""

    model_config = ConfigDict(extra="forbid")
    content: str | None = None
    tool_calls: list[ToolCall] | None = None
