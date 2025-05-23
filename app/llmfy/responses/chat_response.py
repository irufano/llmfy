from typing import List
from pydantic import BaseModel, ConfigDict, Field

from app.llmfy.messages.message import Message
from app.llmfy.responses.ai_response import AIResponse


class ChatResponse(BaseModel):
    """ChatResponse Class"""

    model_config = ConfigDict(extra="forbid")
    result: AIResponse
    messages: List[Message] = Field(default_factory=list)
