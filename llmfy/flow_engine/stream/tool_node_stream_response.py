from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class ToolNodeStreamType(str, Enum):
    """ToolNodeStreamType"""
    EXECUTING = "executing"
    RESULT = "result"

class ToolNodeStreamResponse(BaseModel):
    """ToolNodeStreamResponse"""
    type: Optional[str] = Field(default=None)
    name: Optional[str] = Field(default=None)
    arguments: Optional[Dict] = Field(default=None)
    result: Optional[Any] = Field(default=None)