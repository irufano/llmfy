from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class NEREntity:
    """A single raw entity span reported by an NER backend.

    Deliberately dumb: backends know nothing about PIIType, PIIStrategy, or
    placeholder formatting — all of that lives in PIIGuard. `label` is the
    backend's own raw label string (e.g. spaCy's "PER"/"ADR"), which the
    caller maps to a PIIType.
    """

    text: str
    label: str
    start: int
    end: int


class BaseNERBackend(ABC):
    """Base class for pluggable NER-based PII detection backends."""

    @abstractmethod
    def detect_entities(self, text: str) -> list[NEREntity]:
        """Run NER over `text` and return raw entity spans."""
        raise NotImplementedError
