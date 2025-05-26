from typing import List
from pydantic import BaseModel, ConfigDict, Field

from llmfy.llmfy.messages.message import Message
from llmfy.llmfy.responses.ai_response import AIResponse


class ChatResponse(BaseModel):
    """ChatResponse Class"""

    model_config = ConfigDict(extra="forbid")
    result: AIResponse
    messages: List[Message] = Field(default_factory=list)
