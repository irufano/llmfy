from enum import Enum


class PIIStrategy(str, Enum):
    """Strategy for handling detected PII.

    - MASK: replaces each PII with a type-specific placeholder, e.g. [EMAIL], [SSN]
    - REDACT: replaces all PII with the generic [REDACTED] placeholder
    """

    MASK = "mask"
    REDACT = "redact"

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return f"'{self.value}'"
