from typing import List, Optional

from pydantic import BaseModel


class BedrockConfig(BaseModel):
    """Configuration for BedrockModel."""

    temperature: float = 0.7
    max_tokens: Optional[int] = None
    top_p: float = 1.0
    top_k: Optional[int] = None
    stopSequences: Optional[List[str]] = None
