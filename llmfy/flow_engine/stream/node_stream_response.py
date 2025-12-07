from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class NodeStreamType(str, Enum):
    """NodeStreamType"""
    STREAM = "stream"
    RESULT = "result"

class NodeStreamResponse(BaseModel):
    """NodeStreamResponse"""
    type: Optional[str] = Field(default=None)
    content: Optional[Any] = Field(default=None)
    state: Optional[Dict] = Field(default=None)