
from pydantic import BaseModel, ConfigDict

from llmfy.llmfy_core.messages.tool_call import ToolCall


class AIResponse(BaseModel):
    """AIResponse Class"""

    model_config = ConfigDict(extra="forbid")
    content: str | None = None
    thinking: str | None = None
    """Reasoning/thinking trace, when the provider returns one and the model's
    thinking config requests it. Not persisted back into conversation
    history — only surfaced on the response you get back from generate()."""
    tool_calls: list[ToolCall] | None = None
