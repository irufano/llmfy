from enum import StrEnum


class PIIStrategy(StrEnum):
    """Strategy for handling detected PII.

    Irreversible (one-way):
    - PARTIAL: replaces each PII with the first 2 chars of the value + *,
               e.g. 'john@example.com' -> 'jo*'
    - MASK: replaces each PII with a numbered, type-specific placeholder
            that is unique per distinct value, e.g. '[EMAIL_1]', '[EMAIL_2]'.
            Callers should not retain the returned values for later restore.
    - REDACT: replaces every PII with the same generic '[REDACTED]'
              placeholder. Placeholders are not unique per value, so this
              strategy cannot be reliably reversed with `PIIGuard.restore`.

    Reversible:
    - TOKENIZE: same placeholder format as MASK ('[EMAIL_1]', unique per
                value), but this is the strategy meant to be paired with
                `PIIGuard.restore(text, detections)`. PIIGuard itself keeps
                no internal mapping — the caller holds onto the returned
                `PIIDetectionResult.detections` and passes them back in.
    """

    PARTIAL = "partial"
    MASK = "mask"
    REDACT = "redact"
    TOKENIZE = "tokenize"

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return f"'{self.value}'"
