import uuid
from typing import List, Union

from pydantic import BaseModel, ConfigDict, Field, model_validator

from llmfy.guardrails.pii.pii_strategy import PIIStrategy
from llmfy.guardrails.pii.pii_type import PIIType


class PIIDetection(BaseModel):
    """A single PII finding within a text.

    Attributes:
        id: Unique identifier for this detection.
        pii_type: The category of PII detected.
        value: The original PII string found in the text.
        start: Start character index (inclusive) in the original text.
        end: End character index (exclusive) in the original text.
        placeholder: The string used to replace this PII in processed_text.
    """

    model_config = ConfigDict(extra="forbid")

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    pii_type: Union[PIIType, str]
    value: str
    start: int
    end: int
    placeholder: str


class PIIDetectionResult(BaseModel):
    """Overall result from a PII detection pass.

    Attributes:
        id: Unique identifier for this result.
        original_text: The input text, unchanged.
        processed_text: The text with all detected PII replaced.
        detections: List of individual PII findings.
        has_pii: True when at least one detection exists (computed).
        strategy: The PIIStrategy applied during processing.
    """

    model_config = ConfigDict(extra="forbid")

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    original_text: str
    processed_text: str
    detections: List[PIIDetection] = Field(default_factory=list)
    has_pii: bool = False
    strategy: PIIStrategy

    @model_validator(mode="after")
    def _compute_has_pii(self) -> "PIIDetectionResult":
        self.has_pii = len(self.detections) > 0
        return self
