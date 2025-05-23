from typing import Optional

from pydantic import BaseModel


class OpenAIConfig(BaseModel):
	"""Configuration for OpenAIModel."""
	temperature: float = 0.7
	max_tokens: Optional[int] = None
	top_p: float = 1.0
	frequency_penalty: float = 0.0
	presence_penalty: float = 0.0
