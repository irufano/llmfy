import re
from typing import Dict, List, Optional, Union

from llmfy.guardrails.pii.pii_mask_style import PIIMaskStyle
from llmfy.guardrails.pii.pii_result import PIIDetection, PIIDetectionResult
from llmfy.guardrails.pii.pii_strategy import PIIStrategy
from llmfy.guardrails.pii.pii_type import PIIType


class PIIDetector:
    """Detects and optionally replaces Personally Identifiable Information in text.

    Uses regex-based detection — no external NLP dependencies required.

    Example:
    ```python
    from llmfy import PIIDetector, PIIMaskStyle, PIIStrategy, PIIType

    # Default: MASK + PARTIAL (first 2 chars of value + *)
    detector = PIIDetector()
    result = detector.detect("Contact john@example.com or call 555-123-4567")
    print(result.processed_text)  # "Contact jo* or call 55*"

    # MASK + TYPE_NAME style
    detector = PIIDetector(mask_style=PIIMaskStyle.TYPE_NAME)
    result = detector.detect("Contact john@example.com or call 555-123-4567")
    print(result.processed_text)  # "Contact [EMAIL] or call [PHONE_NUMBER]"

    # REDACT strategy (mask_style ignored)
    detector = PIIDetector(strategy=PIIStrategy.REDACT, types=[PIIType.EMAIL])
    result = detector.detect("Email: jane@test.org, SSN: 123-45-6789")
    print(result.processed_text)  # "Email: [REDACTED], SSN: 123-45-6789"

    # Custom types with name and regex
    detector = PIIDetector(
        custom_types={"EMPLOYEE_ID": "EMP-[0-9]{6}", "PROJECT_CODE": "PRJ-[A-Z]{3}"}
    )
    result = detector.detect("Employee EMP-001234 is on project PRJ-ABC")
    print(result.processed_text)  # "Employee EM* is on project PR*"

    # Scan without replacing
    findings = detector.scan("Email: jane@test.org, IP: 10.0.0.1")
    for f in findings:
        print(f.pii_type, f.value)
    ```
    """

    # Compiled once at import time for performance.
    _PATTERNS: Dict[PIIType, re.Pattern] = {
        PIIType.EMAIL: re.compile(
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
        ),
        PIIType.PHONE_NUMBER: re.compile(
            r"(?:"
            r"\+\d{6,15}"                                                 # compact intl: +628987654321
            r"|"
            r"(?:\+?1[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)\d{3}[-.\s]?\d{4}"  # US/+1: (555) 123-4567
            r")\b"
        ),
        PIIType.SSN: re.compile(
            r"\b\d{3}-\d{2}-\d{4}\b"
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
        PIIType.PASSPORT_NUMBER: re.compile(
            r"\b[A-Z]{1,2}\d{6,9}\b"
        ),
    }

    def __init__(
        self,
        strategy: PIIStrategy = PIIStrategy.MASK,
        mask_style: PIIMaskStyle = PIIMaskStyle.PARTIAL,
        types: Optional[List[PIIType]] = None,
        custom_types: Optional[Dict[str, Union[str, re.Pattern]]] = None,
    ) -> None:
        """Initialize the PIIDetector.

        Args:
            strategy: PIIStrategy.MASK replaces PII using mask_style.
                      PIIStrategy.REDACT replaces all PII with [REDACTED].
                      Defaults to PIIStrategy.MASK.
            mask_style: Controls the placeholder format when strategy is MASK.
                        PIIMaskStyle.PARTIAL shows the first 2 chars of the
                        detected value followed by * (e.g. 'jo*').
                        PIIMaskStyle.TYPE_NAME shows the type in brackets
                        (e.g. '[EMAIL]'). Defaults to PIIMaskStyle.PARTIAL.
            types: List of PIIType values to detect. Pass None to detect all
                   supported PII types. Defaults to None (all types).
            custom_types: Dict mapping a custom type name to a regex pattern
                          (str or compiled). The name is used as the TYPE_NAME
                          placeholder label. If a key matches a built-in
                          PIIType name, the custom pattern replaces the built-in.
                          Defaults to None (no custom types).
        """
        self.strategy = strategy
        self.mask_style = mask_style
        self._custom_patterns: Dict[str, re.Pattern] = {
            name: (p if isinstance(p, re.Pattern) else re.compile(p))
            for name, p in (custom_types or {}).items()
        }
        # Exclude built-in types overridden by a custom pattern of the same name
        active_types = types if types is not None else list(PIIType)
        self.types: List[PIIType] = [
            t for t in active_types if t.value not in self._custom_patterns
        ]

    def _placeholder(self, pii_type: Union[PIIType, str], value: str) -> str:
        if self.strategy == PIIStrategy.REDACT:
            return "[REDACTED]"
        if self.mask_style == PIIMaskStyle.PARTIAL:
            return f"{value[:2]}{'*' * max(len(value) - 2, 0)}"
        return f"[{pii_type}]"

    def scan(self, text: str) -> List[PIIDetection]:
        """Find all PII in text without replacing anything.

        Detections are returned sorted by their start character index.

        Args:
            text: The input text to scan.

        Returns:
            List of PIIDetection instances, each describing one PII occurrence.
        """
        detections: List[PIIDetection] = []

        for pii_type in self.types:
            pattern = self._PATTERNS.get(pii_type)
            if pattern is None:
                continue
            for match in pattern.finditer(text):
                detections.append(
                    PIIDetection(
                        pii_type=pii_type,
                        value=match.group(),
                        start=match.start(),
                        end=match.end(),
                        placeholder=self._placeholder(pii_type, match.group()),
                    )
                )

        for type_name, pattern in self._custom_patterns.items():
            for match in pattern.finditer(text):
                detections.append(
                    PIIDetection(
                        pii_type=type_name,
                        value=match.group(),
                        start=match.start(),
                        end=match.end(),
                        placeholder=self._placeholder(type_name, match.group()),
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
