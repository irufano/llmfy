
from pydantic import BaseModel


class ModelPricing(BaseModel):
    """ModelPricing Class"""
    token_input: float
    token_output: float
    token_unit: int = 1_000_000
    cache_read: float | None = None
    """Explicit price per token_unit for cache-read tokens. None -> use provider default ratio."""
    cache_write: float | None = None
    """Explicit price per token_unit for cache-write tokens. None -> use provider default (0 for OpenAI, ratio for Bedrock)."""

    def __repr__(self) -> str:
        return str(self.model_dump())