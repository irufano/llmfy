import re
from typing import ClassVar

from llmfy.guardrails.pii.backends import SpacyNERBackend
from llmfy.guardrails.pii.pii_result import PIIDetection, PIIDetectionResult
from llmfy.guardrails.pii.pii_strategy import PIIStrategy
from llmfy.guardrails.pii.pii_type import PIIType


class PIIGuard:
    """Detects and optionally replaces Personally Identifiable Information in text.

    Most PII types use compiled regex and need no external dependencies.
    PIIType.PERSON_NAME and PIIType.ADDRESS are the exception: they're
    detected via an optional spaCy NER model (`xx_ent_pii_sm`, see README
    for install instructions), loaded lazily on first use — never at
    PIIGuard() construction time. Because `types=None` (the default)
    detects every PIIType including these two, a bare `PIIGuard()` now
    requires that model to be installed once you actually call scan()/
    detect() — pass `exclude_types=[PIIType.PERSON_NAME, PIIType.ADDRESS]`
    to stay on regex-only detection with no extra dependency.

    PIIGuard keeps no internal state between calls. For the reversible
    PIIStrategy.TOKENIZE strategy, the caller is responsible for holding on
    to `PIIDetectionResult.detections` and passing it back into `restore()`
    — PIIGuard never stores PII values itself.

    Example:
    ```python
    from llmfy import PIIGuard, PIIStrategy, PIIType

    # Default: TOKENIZE — reversible: hold on to result.detections to restore() later
    guard = PIIGuard()
    result = guard.detect("Contact john@example.com")
    print(result.processed_text)  # "Contact [EMAIL_1]"
    restored = guard.restore(result.processed_text, result.detections)
    print(restored)  # "Contact john@example.com"

    # MASK — numbered, type-specific placeholder, unique per value, one-way
    guard = PIIGuard(strategy=PIIStrategy.MASK)
    result = guard.detect("Contact john@example.com or call 555-123-4567")
    print(result.processed_text)  # "Contact [EMAIL_1] or call [PHONE_NUMBER_1]"

    # REDACT strategy — every PII becomes the same generic placeholder
    guard = PIIGuard(strategy=PIIStrategy.REDACT, types=[PIIType.EMAIL])
    result = guard.detect("Email: jane@test.org, SSN: 123-45-6789")
    print(result.processed_text)  # "Email: [REDACTED], SSN: 123-45-6789"

    # PARTIAL — first 2 chars of value + *
    guard = PIIGuard(strategy=PIIStrategy.PARTIAL)
    result = guard.detect("Contact john@example.com or call 555-123-4567")
    print(result.processed_text)  # "Contact jo* or call 55*"

    # exclude_types — detect every built-in type except the ones listed,
    # instead of enumerating everything you want to keep
    guard = PIIGuard(strategy=PIIStrategy.MASK, exclude_types=[PIIType.SSN])
    result = guard.detect("Email: jane@test.org, SSN: 123-45-6789")
    print(result.processed_text)  # "Email: [EMAIL_1], SSN: 123-45-6789"

    # Custom types with name and regex
    guard = PIIGuard(
        custom_types={"EMPLOYEE_ID": "EMP-[0-9]{6}", "PROJECT_CODE": "PRJ-[A-Z]{3}"}
    )
    result = guard.detect("Employee EMP-001234 is on project PRJ-ABC")
    print(result.processed_text)  # "Employee EM* is on project PR*"

    # Scan without replacing
    findings = guard.scan("Email: jane@test.org, IP: 10.0.0.1")
    for f in findings:
        print(f.pii_type, f.value)

    # PERSON_NAME / ADDRESS — requires the optional spaCy model installed
    guard = PIIGuard(strategy=PIIStrategy.MASK)
    result = guard.detect("Budi Santoso tinggal di Jl. Merdeka No. 10, Jakarta.")
    print(result.processed_text)  # "[PERSON_NAME_1] tinggal di [ADDRESS_1]."

    # Stay regex-only with no NER dependency
    guard = PIIGuard(exclude_types=[PIIType.PERSON_NAME, PIIType.ADDRESS])
    result = guard.detect("Contact john@example.com")
    print(result.processed_text)  # "Contact [EMAIL_1]"
    ```
    """

    # Compiled once at import time for performance.
    _PATTERNS: dict[PIIType, re.Pattern] = {
        PIIType.EMAIL: re.compile(
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
        ),
        PIIType.PHONE_NUMBER: re.compile(
            # (?<!\d) rather than \b at the start: \b would reject a leading
            # '+'/'(' preceded by whitespace (non-word next to non-word isn't
            # a boundary). We only need to block starting mid-digit-run.
            r"(?<!\d)(?:"
            r"\+\d{6,15}"                                                 # compact intl: +628987654321
            r"|"
            r"(?:\+?1[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)\d{3}[-.\s]?\d{4}"  # US/+1: (555) 123-4567
            r")\b"
        ),
        PIIType.SSN: re.compile(
            r"\b\d{3}-\d{2}-\d{4}\b"
        ),
        # Indonesian civil-registry number (province+city+district+birthdate+
        # sequence) — plain 16 digits. Also matches Kartu Keluarga (KK)
        # numbers, which use the same 16-digit format with no structural way
        # to tell them apart from NIK by regex alone.
        PIIType.NIK: re.compile(
            r"\b\d{16}\b"
        ),
        PIIType.CREDIT_CARD: re.compile(
            r"\b(?:\d{4}[-\s]?){3}\d{4}\b"
        ),
        PIIType.IP_ADDRESS: re.compile(
            r"\b(?:\d{1,3}\.){3}\d{1,3}\b"
        ),
        PIIType.DATE_OF_BIRTH: re.compile(
            r"\b(?:"
            r"\d{1,2}[/-]\d{1,2}[/-]\d{2,4}"
            r"|"
            r"\d{4}[/-]\d{1,2}[/-]\d{1,2}"
            r"|"
            r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*"
            r"\.?\s+\d{1,2},?\s+\d{4}"
            r")\b",
            re.IGNORECASE,
        ),
        # Covers the Indonesian passport format (1 letter + 7 digits, e.g.
        # 'C1234567') as well as broader alphanumeric passport formats.
        PIIType.PASSPORT_NUMBER: re.compile(
            r"\b[A-Z]{1,2}\d{6,9}\b"
        ),
    }

    # PERSON_NAME/ADDRESS have no regex entry above — they're detected via
    # SpacyNERBackend instead, mapping its raw entity labels to PIIType.
    _NER_LABEL_TO_TYPE: dict[str, PIIType] = {
        "PER": PIIType.PERSON_NAME,
        "ADR": PIIType.ADDRESS,
    }

    # Shared across all PIIGuard instances so the spaCy pipeline loads at
    # most once per process, on first actual use.
    _ner_backend: ClassVar[SpacyNERBackend | None] = None

    @classmethod
    def _get_ner_backend(cls) -> SpacyNERBackend:
        if cls._ner_backend is None:
            cls._ner_backend = SpacyNERBackend()
        return cls._ner_backend

    def __init__(
        self,
        strategy: PIIStrategy = PIIStrategy.TOKENIZE,
        types: list[PIIType] | None = None,
        exclude_types: list[PIIType] | None = None,
        custom_types: dict[str, str | re.Pattern] | None = None,
    ) -> None:
        """Initialize the PIIGuard.

        Args:
            strategy: How detected PII is replaced. PARTIAL shows the first
                2 chars of the value followed by * (e.g. 'jo*').
                MASK replaces with a numbered type placeholder unique
                per value (e.g. '[EMAIL_1]'), intended as one-way.
                REDACT replaces everything with '[REDACTED]'.
                TOKENIZE uses the same placeholder format as MASK but
                is meant to be paired with `restore()`. Defaults to
                PIIStrategy.TOKENIZE.
            types: List of PIIType values to detect. Pass None to detect all
                supported PII types. Defaults to None (all types).
                Mutually exclusive with `exclude_types`.
            exclude_types: List of PIIType values to skip, detecting every
                other built-in type. Use this instead of `types`
                when you want to drop just one or two types
                rather than enumerating the rest. Mutually
                exclusive with `types`. Defaults to None.
            custom_types: Dict mapping a custom type name to a regex pattern
                (str or compiled). The name is used as the label in
                MASK/TOKENIZE placeholders. If a key matches a
                built-in PIIType name, the custom pattern replaces
                the built-in. Defaults to None (no custom types).

        Raises:
            ValueError: If both `types` and `exclude_types` are provided.
        """
        if types is not None and exclude_types is not None:
            raise ValueError(
                "Pass either 'types' or 'exclude_types', not both."
            )

        self.strategy = strategy
        self._custom_patterns: dict[str, re.Pattern] = {
            name: (p if isinstance(p, re.Pattern) else re.compile(p))
            for name, p in (custom_types or {}).items()
        }
        if exclude_types is not None:
            active_types = [t for t in PIIType if t not in exclude_types]
        else:
            active_types = types if types is not None else list(PIIType)
        # Exclude built-in types overridden by a custom pattern of the same name
        self.types: list[PIIType] = [
            t for t in active_types if t.value not in self._custom_patterns
        ]

    def _placeholder(
        self,
        pii_type: PIIType | str,
        value: str,
        seen: dict[tuple[str, str], str],
        counters: dict[str, int],
    ) -> str:
        if self.strategy == PIIStrategy.REDACT:
            return "[REDACTED]"
        if self.strategy == PIIStrategy.PARTIAL:
            return f"{value[:2]}{'*' * max(len(value) - 2, 0)}"

        # MASK and TOKENIZE both use a numbered label, unique per value.
        type_name = str(pii_type)
        key = (type_name, value)
        if key in seen:
            return seen[key]
        counters[type_name] = counters.get(type_name, 0) + 1
        placeholder = f"[{type_name}_{counters[type_name]}]"
        seen[key] = placeholder
        return placeholder

    def scan(self, text: str) -> list[PIIDetection]:
        """Find all PII in text without replacing anything.

        Detections are returned sorted by their start character index.

        Args:
            text: The input text to scan.

        Returns:
            List of PIIDetection instances, each describing one PII occurrence.
        """
        detections: list[PIIDetection] = []
        seen: dict[tuple[str, str], str] = {}
        counters: dict[str, int] = {}
        # Two types (built-in or custom) can match the exact same span (e.g.
        # a custom pattern that overlaps a built-in one) — keep only the
        # first match per exact (start, end) span so detect() never replaces
        # the same span twice.
        seen_spans: set = set()

        for pii_type in self.types:
            pattern = self._PATTERNS.get(pii_type)
            if pattern is None:
                continue
            for match in pattern.finditer(text):
                span = (match.start(), match.end())
                if span in seen_spans:
                    continue
                seen_spans.add(span)
                detections.append(
                    PIIDetection(
                        pii_type=pii_type,
                        value=match.group(),
                        start=match.start(),
                        end=match.end(),
                        placeholder=self._placeholder(
                            pii_type, match.group(), seen, counters
                        ),
                    )
                )

        for type_name, pattern in self._custom_patterns.items():
            for match in pattern.finditer(text):
                span = (match.start(), match.end())
                if span in seen_spans:
                    continue
                seen_spans.add(span)
                detections.append(
                    PIIDetection(
                        pii_type=type_name,
                        value=match.group(),
                        start=match.start(),
                        end=match.end(),
                        placeholder=self._placeholder(
                            type_name, match.group(), seen, counters
                        ),
                    )
                )

        ner_types_active = [
            t for t in self.types if t in self._NER_LABEL_TO_TYPE.values()
        ]
        if ner_types_active:
            backend = self._get_ner_backend()
            for entity in backend.detect_entities(text):
                pii_type = self._NER_LABEL_TO_TYPE.get(entity.label)
                if pii_type is None or pii_type not in ner_types_active:
                    continue
                span = (entity.start, entity.end)
                if span in seen_spans:
                    continue
                seen_spans.add(span)
                detections.append(
                    PIIDetection(
                        pii_type=pii_type,
                        value=entity.text,
                        start=entity.start,
                        end=entity.end,
                        placeholder=self._placeholder(
                            pii_type, entity.text, seen, counters
                        ),
                    )
                )

        detections.sort(key=lambda d: d.start)
        return detections

    def detect(self, text: str) -> PIIDetectionResult:
        """Detect all PII in text and return a result with PII replaced.

        Replacements are applied right-to-left to preserve character index
        validity as substitutions are made.

        Args:
            text: The input text to process.

        Returns:
            PIIDetectionResult containing the original text, processed text
            with PII replaced, and all individual detections.
        """
        detections = self.scan(text)

        processed = text
        for detection in reversed(detections):
            processed = (
                processed[: detection.start]
                + detection.placeholder
                + processed[detection.end :]
            )

        return PIIDetectionResult(
            original_text=text,
            processed_text=processed,
            detections=detections,
            strategy=self.strategy,
        )

    def restore(self, text: str, detections: list[PIIDetection]) -> str:
        """Substitute placeholders in `text` back to their original values.

        `detections` should come from a prior `detect()`/`scan()` call made
        with PIIStrategy.TOKENIZE — PIIGuard keeps no mapping of its own, so
        the caller must hold on to and pass back the detections it was given.
        `text` doesn't have to be the exact `processed_text` that was
        returned — it can be any later text (e.g. an LLM response) that still
        contains the same placeholders.

        Not recommended for PIIStrategy.REDACT results: every value shares
        the same '[REDACTED]' placeholder, so substitution is ambiguous
        when more than one PII value was redacted in the same text.

        Placeholders in `text` that aren't present in `detections` are left
        unchanged.

        Args:
            text: Text containing placeholders to restore.
            detections: Detections (with original `value` and `placeholder`)
                        to substitute back into `text`.

        Returns:
            `text` with every known placeholder replaced by its original value.
        """
        for detection in detections:
            text = text.replace(detection.placeholder, detection.value)
        return text
