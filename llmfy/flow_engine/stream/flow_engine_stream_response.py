from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

from llmfy.flow_engine.node.node import Enum


class FlowEngineStreamType(str, Enum):
    """FlowEngineStreamType"""
    START = "start"
    STREAM = "stream"
    RESULT = "result"
    ERROR = "error"


class FlowEngineStreamResponse(BaseModel):
    """FlowEngineStreamResponse"""
    type: Optional[str] = Field(default=None)
    node: Optional[str] = Field(default=None)
    content: Optional[Any] = Field(default=None)
    state: Optional[Dict] = Field(default=None)
    error: Optional[Any] = Field(default=None)
