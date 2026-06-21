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

    # Safety
    safety_settings: Optional[List[Any]] = None
    """List of google.genai.types.SafetySetting instances."""

    # Thinking — unified fields
    enable_thinking: bool = False
    """Enable extended thinking. Supported models:

    Gemini 2.5 series (use thinking_budget_tokens for token-based control):
      - gemini-2.5-pro
      - gemini-2.5-flash
      - gemini-2.5-flash-lite

    Gemini 3 series (use thinking_level for named effort control):
      - gemini-3-flash
      - gemini-3.1-pro
      - gemini-3.1-flash-lite
      - gemini-3.5-flash

    And latest
    """
    thinking_budget_tokens: Optional[int] = None
    """Token budget for thinking. -1 = dynamic (model decides), 0 = disable explicit budget.
    Maps to thinking_budget in ThinkingConfig."""
    thinking_level: Optional[str] = None
    """Named effort level: 'MINIMAL', 'LOW', 'MEDIUM', 'HIGH'.
    Alternative to thinking_budget_tokens — use one or the other."""
    thinking_include_thoughts: Optional[bool] = None
    """Whether to include thinking steps in the response content parts."""

    # Raw thinking override (backward compat — takes priority over unified fields above)
    thinking_config: Optional[Any] = None
    """google.genai.types.ThinkingConfig instance. When set, takes priority over
    enable_thinking / thinking_budget_tokens / thinking_level / thinking_include_thoughts."""
