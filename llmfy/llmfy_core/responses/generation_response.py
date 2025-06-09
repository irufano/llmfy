from typing import List
from pydantic import BaseModel, ConfigDict, Field

from llmfy.llmfy_core.messages.message import Message
from llmfy.llmfy_core.responses.ai_response import AIResponse


class GenerationResponse(BaseModel):
    """GenerationResponse Class"""

    model_config = ConfigDict(extra="forbid")
    result: AIResponse
    messages: List[Message] = Field(default_factory=list)
