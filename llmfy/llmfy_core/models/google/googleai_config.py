from typing import Any, List, Optional

from pydantic import BaseModel


class GoogleAIConfig(BaseModel):
    """Configuration for GoogleAIModel.

    Maps to `google.genai.types.GenerateContentConfig` parameters.

    Example:
    ```python
    config = GoogleAIConfig(temperature=0.7)
    ```
    """

    # Core generation params
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    """Maps to max_output_tokens in GenerateContentConfig."""
    top_p: Optional[float] = None
    top_k: Optional[int] = None
    stop_sequences: Optional[List[str]] = None
    candidate_count: Optional[int] = None
    seed: Optional[int] = None

    # Penalty params
    presence_penalty: Optional[float] = None
    frequency_penalty: Optional[float] = None

    # Response format
    response_mime_type: Optional[str] = None
    """e.g. 'application/json' for structured output."""
    response_schema: Optional[Any] = None
    """Schema for structured output. Used with response_mime_type='application/json'."""

    # Safety / thinking
    safety_settings: Optional[List[Any]] = None
    """List of google.genai.types.SafetySetting instances."""
    thinking_config: Optional[Any] = None
    """google.genai.types.ThinkingConfig instance."""
