from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class NodeStreamType(str, Enum):
    """NodeStreamType"""
    STREAM = "stream"
    RESULT = "result"

class NodeStreamResponse(BaseModel):
    """NodeStreamResponse"""
    type: str | None = Field(default=None)
    content: Any | None = Field(default=None)
    state: dict | None = Field(default=None)