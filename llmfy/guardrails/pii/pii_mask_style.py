from enum import Enum


class PIIMaskStyle(str, Enum):
    """Placeholder style used when PIIStrategy is MASK.

    - PARTIAL: replaces PII with first 2 chars of the value followed by *
                e.g. 'john@example.com' → 'jo*'
    - TYPE_NAME: replaces PII with the type name in brackets
                  e.g. 'john@example.com' → '[EMAIL]'
    """

    PARTIAL = "partial"
    TYPE_NAME = "type_name"

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return f"'{self.value}'"
