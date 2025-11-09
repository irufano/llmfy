import uuid
from typing import Any, Dict

from pydantic import BaseModel, Field


class BaseChunkResult(BaseModel):
    """Base interface for chunk result."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
