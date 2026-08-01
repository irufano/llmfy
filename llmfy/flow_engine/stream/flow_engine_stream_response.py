from typing import Any

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
    type: str | None = Field(default=None)
    node: str | None = Field(default=None)
    content: Any | None = Field(default=None)
    state: dict | None = Field(default=None)
    error: Any | None = Field(default=None)
