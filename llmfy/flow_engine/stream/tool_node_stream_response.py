from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ToolNodeStreamType(str, Enum):
    """ToolNodeStreamType"""
    EXECUTING = "executing"
    RESULT = "result"

class ToolNodeStreamResponse(BaseModel):
    """ToolNodeStreamResponse"""
    type: str | None = Field(default=None)
    name: str | None = Field(default=None)
    arguments: dict | None = Field(default=None)
    result: Any | None = Field(default=None)