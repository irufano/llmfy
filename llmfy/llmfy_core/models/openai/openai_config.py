from typing import Optional

from pydantic import BaseModel


class OpenAIConfig(BaseModel):
    """Configuration for OpenAIModel."""

    temperature: float = 0.7
    max_tokens: Optional[int] = None
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0

    # Thinking / reasoning
    enable_thinking: bool = False
    """Enable reasoning mode via the Chat Completions API. Supported models:
      - o1
      - o1-mini
      - o3
      - o3-mini
      - o4-mini
      (and any future o-series reasoning models)
    """
    reasoning_effort: Optional[str] = None
    """'low', 'medium', or 'high'. Used with o1/o3/o4-mini reasoning models via
    the Chat Completions API. Defaults to 'medium' when enable_thinking=True and not set."""
